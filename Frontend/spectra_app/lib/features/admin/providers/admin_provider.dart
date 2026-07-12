import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/shared/models/admin.dart';

final adminStatsProvider = FutureProvider<AdminStats>((ref) async {
  final dio = ref.read(dioProvider);
  final resp = await dio.get('/admin/stats');
  return AdminStats.fromJson(resp.data as Map<String, dynamic>);
});

final adminUsersProvider =
    AsyncNotifierProvider<AdminUsersNotifier, List<AdminUser>>(
        AdminUsersNotifier.new);

class AdminUsersNotifier extends AsyncNotifier<List<AdminUser>> {
  @override
  Future<List<AdminUser>> build() => _fetch();

  Future<List<AdminUser>> _fetch({String? role, int? isActive}) async {
    final dio = ref.read(dioProvider);
    final resp = await dio.get('/admin/users', queryParameters: {
      'skip': 0,
      'limit': 100,
      if (role != null) 'role': role,
      if (isActive != null) 'is_active': isActive,
    });
    return (resp.data as List)
        .map((e) => AdminUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> filter({String? role, int? isActive}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetch(role: role, isActive: isActive));
  }

  Future<void> updateUser(
    int userId, {
    String? role,
    int? isActive,
    String? fullName,
    String? organization,
    String? designation,
  }) async {
    final dio = ref.read(dioProvider);
    final payload = {
      if (role != null) 'role': role,
      if (isActive != null) 'is_active': isActive,
      if (fullName != null) 'full_name': fullName,
      if (organization != null) 'organization': organization,
      if (designation != null) 'designation': designation,
    };
    await dio.patch('/admin/users/$userId', data: payload);
    // Refresh
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }
}
