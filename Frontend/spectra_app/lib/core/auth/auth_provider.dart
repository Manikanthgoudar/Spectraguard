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
    state = state.copyWith(isLoading: true);
    try {
      if (await _service.isLoggedIn()) {
        final user = await _service.getMe();
        state = state.copyWith(user: user, isLoading: false);
      } else {
        state = state.copyWith(isLoading: false);
      }
    } catch (_) {
      state = state.copyWith(isLoading: false);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _service.login(email, password);
      state = state.copyWith(user: user, isLoading: false);
    } on Exception catch (e) {
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
    } on Exception catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> logout() async {
    await _service.logout();
    state = const AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(ref.watch(authServiceProvider)),
);
