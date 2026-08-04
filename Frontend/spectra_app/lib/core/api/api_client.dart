import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Resolves the correct backend base URL depending on the platform:
/// - Android emulator: 10.0.2.2 maps to the host machine's localhost
/// - Android physical device (or any real device on the same Wi-Fi):
///   pass your PC's current LAN IP via --dart-define=DEV_MACHINE_IP=x.x.x.x
/// - Everything else (web, Windows, macOS, Linux desktop): localhost
///
/// Run on a physical device:
///   flutter run --dart-define=DEV_MACHINE_IP=192.168.x.x
///
/// You never need to edit this file again — just change the flag.
const String _devMachineIp = String.fromEnvironment(
  'DEV_MACHINE_IP',
  defaultValue: '10.0.2.2',
);

String get _baseUrl {
  if (kIsWeb) return 'http://localhost:8000';
  if (Platform.isAndroid) {
    return 'http://$_devMachineIp:8000';
  }
  return 'http://localhost:8000';
}

/// Public accessor so other layers (e.g. profile photo URL builder) can
/// compose full URLs without duplicating the platform logic.
String get apiBaseUrl => _baseUrl;

Dio createDio() {
  final dio = Dio(
    BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      // Do NOT set a global Content-Type here — Dio sets it automatically
      // per request (application/json for JSON bodies, multipart/form-data
      // for FormData uploads). A hardcoded 'application/json' breaks
      // multipart uploads and causes 400 errors on the /spectra/upload endpoint.
    ),
  );

  dio.interceptors.add(_AuthInterceptor(dio));
  return dio;
}

class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._dio);

  final Dio _dio;
  final _storage = const FlutterSecureStorage();

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  // Guard against re-entrant refresh calls (prevents infinite retry loops).
  // When a refresh is already in flight, subsequent 401s wait on this
  // Completer instead of firing a second refresh request.
  bool _isRefreshing = false;
  Completer<String?>? _refreshCompleter;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final path = err.requestOptions.path;

    // Never try to refresh if the failing request IS a refresh/login/logout call
    // (prevents infinite loops and useless retries on auth endpoints).
    final isAuthEndpoint = path.contains('/auth/refresh-token') ||
        path.contains('/auth/login') ||
        path.contains('/auth/logout');

    if (err.response?.statusCode == 401 && !isAuthEndpoint) {
      // If a refresh is already in flight, wait for it to finish and retry
      // with its result rather than firing a duplicate refresh request.
      if (_isRefreshing) {
        final newAccess = await _refreshCompleter!.future;
        if (newAccess != null) {
          final opts = err.requestOptions;
          opts.headers['Authorization'] = 'Bearer $newAccess';
          try {
            final retried = await _dio.fetch(opts);
            return handler.resolve(retried);
          } catch (e) {
            return handler.next(err);
          }
        }
        return handler.next(err);
      }

      _isRefreshing = true;
      _refreshCompleter = Completer<String?>();

      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken != null) {
        try {
          final resp = await _dio.post(
            '/auth/refresh-token',
            data: {'refresh_token': refreshToken},
            options: Options(headers: {'Authorization': null}),
          );
          final newAccess = resp.data['access_token'] as String;
          final newRefresh = resp.data['refresh_token'] as String;
          await _storage.write(key: 'access_token', value: newAccess);
          await _storage.write(key: 'refresh_token', value: newRefresh);

          _refreshCompleter!.complete(newAccess);
          _isRefreshing = false;
          _refreshCompleter = null;

          // Retry the original request with the new token
          final opts = err.requestOptions;
          opts.headers['Authorization'] = 'Bearer $newAccess';
          final retried = await _dio.fetch(opts);
          return handler.resolve(retried);
        } catch (_) {
          // Refresh failed — clear all tokens and signal waiting requests
          await _storage.deleteAll();
          _refreshCompleter!.complete(null);
          _isRefreshing = false;
          _refreshCompleter = null;
        }
      } else {
        _refreshCompleter!.complete(null);
        _isRefreshing = false;
        _refreshCompleter = null;
      }
    }
    handler.next(err);
  }
}
