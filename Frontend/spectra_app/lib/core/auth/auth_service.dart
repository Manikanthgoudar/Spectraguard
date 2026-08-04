import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:spectra_app/shared/models/user.dart';

class AuthService {
  AuthService(this._dio);

  final Dio _dio;
  final _storage = const FlutterSecureStorage();

  // ── Device ID ─────────────────────────────────────────────────────────────

  /// Returns a stable device ID, generating one on first call and persisting it.
  Future<String> _getDeviceId() async {
    const key = 'device_id';
    var id = await _storage.read(key: key);
    if (id == null) {
      final rng = Random.secure();
      final bytes = List<int>.generate(16, (_) => rng.nextInt(256));
      bytes[6] = (bytes[6] & 0x0f) | 0x40;
      bytes[8] = (bytes[8] & 0x3f) | 0x80;

      String h(List<int> b) =>
          b.map((e) => e.toRadixString(16).padLeft(2, '0')).join();

      id = '${h(bytes.sublist(0, 4))}-'
          '${h(bytes.sublist(4, 6))}-'
          '${h(bytes.sublist(6, 8))}-'
          '${h(bytes.sublist(8, 10))}-'
          '${h(bytes.sublist(10, 16))}';
      await _storage.write(key: key, value: id);
    }
    return id;
  }

  // ── Token helpers ──────────────────────────────────────────────────────────

  /// Decode a JWT and return its payload map without verifying the signature.
  Map<String, dynamic>? _decodeJwtPayload(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      // Base64url → base64 padding
      String padded = parts[1].replaceAll('-', '+').replaceAll('_', '/');
      while (padded.length % 4 != 0) {
        padded += '=';
      }
      final decoded = utf8.decode(base64Decode(padded));
      return jsonDecode(decoded) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  /// Returns true if the token exists AND has not expired yet (with a 30-second buffer).
  bool _isTokenValid(String? token) {
    if (token == null) return false;
    final payload = _decodeJwtPayload(token);
    if (payload == null) return false;
    final exp = payload['exp'];
    if (exp == null) return false;
    final expiry = DateTime.fromMillisecondsSinceEpoch((exp as int) * 1000);
    return expiry.isAfter(DateTime.now().add(const Duration(seconds: 30)));
  }

  /// Try to silently refresh using the stored refresh token.
  /// Returns the new access token on success, null on failure.
  Future<String?> _refreshAccessToken() async {
    final refreshToken = await _storage.read(key: 'refresh_token');
    if (!_isTokenValid(refreshToken)) return null;
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
      return newAccess;
    } catch (_) {
      return null;
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  Future<User> login(String email, String password) async {
    final deviceId = await _getDeviceId();
    final resp = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
      'device_id': deviceId,
    });
    await _storage.write(
        key: 'access_token', value: resp.data['access_token'] as String);
    await _storage.write(
        key: 'refresh_token', value: resp.data['refresh_token'] as String);
    return getMe();
  }

  Future<User> signup({
    required String fullName,
    required String email,
    required String password,
    String? phone,
    String role = 'public',
    String? organization,
    String? licenseNumber,
    String? designation,
    String? city,
  }) async {
    await _dio.post('/auth/signup', data: {
      'full_name': fullName,
      'email': email,
      'password': password,
      if (phone != null) 'phone': phone,
      'role': role,
      if (organization != null) 'organization': organization,
      if (licenseNumber != null) 'license_number': licenseNumber,
      if (designation != null) 'designation': designation,
      if (city != null) 'city': city,
    });
    // Auto-login after signup so tokens are immediately stored
    return login(email, password);
  }

  Future<User> getMe() async {
    final resp = await _dio.get('/auth/me');
    return User.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<User> updateProfile({
    String? fullName,
    String? phone,
    String? city,
  }) async {
    final body = <String, dynamic>{};
    if (fullName != null) body['full_name'] = fullName;
    if (phone != null) body['phone'] = phone;
    if (city != null) body['city'] = city;
    final resp = await _dio.patch('/auth/me', data: body);
    return User.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<void> deleteAccount() async {
    await _dio.delete('/auth/me');
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } catch (_) {
      // Proceed with local cleanup even if the server call fails
    }
    // Preserve device_id so the same device can log in again
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
  }

  // ── Profile photo ─────────────────────────────────────────────────────────

  /// Upload a profile photo from raw bytes. [fileName] must include extension (e.g. photo.jpg).
  Future<User> uploadProfilePhoto({
    required Uint8List bytes,
    required String fileName,
  }) async {
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: fileName),
    });
    final resp = await _dio.post('/auth/me/photo', data: formData);
    return User.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<User> deleteProfilePhoto() async {
    final resp = await _dio.delete('/auth/me/photo');
    return User.fromJson(resp.data as Map<String, dynamic>);
  }

  // ── Account security ──────────────────────────────────────────────────────

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _dio.post('/auth/me/change-password', data: {
      'current_password': currentPassword,
      'new_password': newPassword,
    });
  }

  Future<User> changeEmail({
    required String newEmail,
    required String password,
  }) async {
    final resp = await _dio.post('/auth/me/change-email', data: {
      'new_email': newEmail,
      'password': password,
    });
    return User.fromJson(resp.data as Map<String, dynamic>);
  }

  // ── Session check ─────────────────────────────────────────────────────────

  /// Check if the user has a valid session — locally first, then via server.
  ///
  /// 1. Access token still valid  → return true immediately (no network call)
  /// 2. Access token expired but refresh token valid → refresh silently → return true
  /// 3. Both expired or missing → clear storage → return false
  Future<bool> isLoggedIn() async {
    final accessToken = await _storage.read(key: 'access_token');

    // Fast path: access token is still good
    if (_isTokenValid(accessToken)) return true;

    // Slow path: try refreshing
    final refreshed = await _refreshAccessToken();
    if (refreshed != null) return true;

    // Nothing valid — clean up so there's no stale data
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');
    return false;
  }
}
