import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/shared/models/reference.dart';

final referenceProvider =
    AsyncNotifierProvider<ReferenceNotifier, List<ReferenceSpectrum>>(
        ReferenceNotifier.new);

class ReferenceNotifier extends AsyncNotifier<List<ReferenceSpectrum>> {
  @override
  Future<List<ReferenceSpectrum>> build() => _fetch();

  Future<List<ReferenceSpectrum>> _fetch({String? drugName}) async {
    final dio = ref.read(dioProvider);
    final resp = await dio.get('/reference', queryParameters: {
      'skip': 0,
      'limit': 100,
      if (drugName != null) 'drug_name': drugName,
    });
    return (resp.data as List)
        .map((e) => ReferenceSpectrum.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> search(String drugName) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
        () => _fetch(drugName: drugName.isEmpty ? null : drugName));
  }

  Future<void> delete(int refId) async {
    final dio = ref.read(dioProvider);
    await dio.delete('/reference/$refId');
    state = AsyncData(
        state.value?.where((r) => r.id != refId).toList() ?? []);
  }
}
