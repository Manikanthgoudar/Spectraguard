import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Resolves the correct backend base URL depending on the platform:
/// - Android emulator: 10.0.2.2 maps to the host machine's localhost
/// - Everything else (Windows, Linux, macOS, Web, physical device on same
///   network): use localhost / 127.0.0.1
String get _baseUrl {
  if (!kIsWeb && Platform.isAndroid) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
}

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

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      // Try refresh
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

          // Retry original request
          final opts = err.requestOptions;
          opts.headers['Authorization'] = 'Bearer $newAccess';
          final retried = await _dio.fetch(opts);
          return handler.resolve(retried);
        } catch (_) {
          await _storage.deleteAll();
        }
      }
    }
    handler.next(err);
  }
}
