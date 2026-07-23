import 'dart:math';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:spectra_app/shared/models/user.dart';

class AuthService {
  AuthService(this._dio);

  final Dio _dio;
  final _storage = const FlutterSecureStorage();

  /// Returns a stable device ID, generating one on first call and persisting it.
  Future<String> _getDeviceId() async {
    const key = 'device_id';
    var id = await _storage.read(key: key);
    if (id == null) {
      // Generate a random UUID v4-like string without extra dependencies
      final rng = Random.secure();
      String hex(int bytes) => List.generate(
            bytes,
            (_) => rng.nextInt(256).toRadixString(16).padLeft(2, '0'),
          ).join();
      id = '${hex(4)}-${hex(2)}-4${hex(1)}a${hex(1)}-${hex(2)}-${hex(6)}';
      await _storage.write(key: key, value: id);
    }
    return id;
  }

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
    // Auto-login after signup
    return login(email, password);
  }

  Future<User> getMe() async {
    final resp = await _dio.get('/auth/me');
    return User.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }
}
