import 'dart:typed_data';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/api/api_client.dart';
import 'package:spectra_app/core/auth/auth_service.dart';
import 'package:spectra_app/shared/models/user.dart';

// ── DIO singleton ─────────────────────────────────────────────────────────
final dioProvider = Provider((ref) => createDio());

// ── AuthService ────────────────────────────────────────────────────────────
final authServiceProvider = Provider<AuthService>(
  (ref) => AuthService(ref.watch(dioProvider)),
);

// ── Auth state ─────────────────────────────────────────────────────────────
class AuthState {
  const AuthState({this.user, this.isLoading = false, this.error});
  final User? user;
  final bool isLoading;
  final String? error;

  bool get isAuthenticated => user != null;

  AuthState copyWith({User? user, bool? isLoading, String? error}) => AuthState(
        user: user ?? this.user,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );

  AuthState clearUser() =>
      AuthState(isLoading: isLoading, error: error);
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._service) : super(const AuthState()) {
    _init();
  }

  final AuthService _service;

  Future<void> _init() async {
    try {
      final loggedIn = await _service.isLoggedIn();
      if (loggedIn) {
        final user = await _service.getMe();
        state = state.copyWith(user: user);
      }
    } catch (_) {
      _service.logout().ignore();
      state = const AuthState();
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _service.login(email, password);
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> signup({
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
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _service.signup(
        fullName: fullName,
        email: email,
        password: password,
        phone: phone,
        role: role,
        organization: organization,
        licenseNumber: licenseNumber,
        designation: designation,
        city: city,
      );
      state = state.copyWith(user: user, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> logout() async {
    await _service.logout();
    state = const AuthState();
  }

  Future<bool> updateProfile({
    String? fullName,
    String? phone,
    String? city,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final updated = await _service.updateProfile(
        fullName: fullName,
        phone: phone,
        city: city,
      );
      state = state.copyWith(user: updated, isLoading: false);
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      return false;
    }
  }

  Future<void> deleteAccount() async {
    await _service.deleteAccount();
    state = const AuthState();
  }

  // ── Profile photo ─────────────────────────────────────────────────────────

  Future<bool> uploadProfilePhoto({
    required Uint8List bytes,
    required String fileName,
  }) async {
    try {
      final updated = await _service.uploadProfilePhoto(
        bytes: bytes,
        fileName: fileName,
      );
      state = state.copyWith(user: updated);
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  Future<bool> deleteProfilePhoto() async {
    try {
      final updated = await _service.deleteProfilePhoto();
      state = state.copyWith(user: updated);
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  // ── Account security ──────────────────────────────────────────────────────

  /// Returns null on success, or an error message string on failure.
  Future<String?> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      await _service.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      return null;
    } catch (e) {
      return _extractMessage(e);
    }
  }

  /// Returns null on success, or an error message string on failure.
  Future<String?> changeEmail({
    required String newEmail,
    required String password,
  }) async {
    try {
      final updated = await _service.changeEmail(
        newEmail: newEmail,
        password: password,
      );
      state = state.copyWith(user: updated);
      return null;
    } catch (e) {
      return _extractMessage(e);
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  String _extractMessage(Object e) {
    final s = e.toString();
    // Try to pull the detail field from a DioException response
    final match = RegExp(r'"detail"\s*:\s*"([^"]+)"').firstMatch(s);
    if (match != null) return match.group(1)!;
    return s;
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.watch(authServiceProvider)),
);
