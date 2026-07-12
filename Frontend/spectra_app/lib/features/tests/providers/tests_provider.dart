import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/shared/models/test.dart';

// ── Tests list ─────────────────────────────────────────────────────────────
final testsProvider =
    AsyncNotifierProvider<TestsNotifier, List<SpectraTest>>(TestsNotifier.new);

class TestsNotifier extends AsyncNotifier<List<SpectraTest>> {
  @override
  Future<List<SpectraTest>> build() => _fetch();

  Future<List<SpectraTest>> _fetch({
    String? drugName,
    String? result,
    String? dateFrom,
    String? dateTo,
  }) async {
    final dio = ref.read(dioProvider);
    final params = <String, dynamic>{
      'skip': 0,
      'limit': 50,
      if (drugName != null) 'drug_name': drugName,
      if (result != null) 'result': result,
      if (dateFrom != null) 'date_from': dateFrom,
      if (dateTo != null) 'date_to': dateTo,
    };
    final resp = await dio.get('/tests', queryParameters: params);
    final data = resp.data as Map<String, dynamic>;
    return (data['tests'] as List)
        .map((e) => SpectraTest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> refresh({
    String? drugName,
    String? result,
    String? dateFrom,
    String? dateTo,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => _fetch(
        drugName: drugName,
        result: result,
        dateFrom: dateFrom,
        dateTo: dateTo,
      ),
    );
  }

  Future<void> deleteTest(int testId) async {
    final dio = ref.read(dioProvider);
    await dio.delete('/tests/$testId');
    state = AsyncData(
      state.value?.where((t) => t.id != testId).toList() ?? [],
    );
  }
}

// ── Single test ────────────────────────────────────────────────────────────
final testDetailProvider =
    FutureProvider.family<SpectraTest, int>((ref, testId) async {
  final dio = ref.read(dioProvider);
  final resp = await dio.get('/tests/$testId');
  return SpectraTest.fromJson(resp.data as Map<String, dynamic>);
});
