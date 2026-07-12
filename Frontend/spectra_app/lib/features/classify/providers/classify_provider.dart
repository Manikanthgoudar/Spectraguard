import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/shared/models/classification.dart';

class ClassifyState {
  const ClassifyState({this.isLoading = false, this.result, this.error});
  final bool isLoading;
  final ClassificationResponse? result;
  final String? error;
}

class ClassifyNotifier extends StateNotifier<ClassifyState> {
  ClassifyNotifier(this._ref) : super(const ClassifyState());
  final Ref _ref;

  Future<void> classify(int testId) async {
    state = const ClassifyState(isLoading: true);
    try {
      final dio = _ref.read(dioProvider);
      final resp = await dio.post('/classify/$testId');
      state = ClassifyState(
        result: ClassificationResponse.fromJson(
            resp.data as Map<String, dynamic>),
      );
    } on Exception catch (e) {
      state = ClassifyState(error: e.toString());
    }
  }

  void reset() => state = const ClassifyState();
}

final classifyProvider =
    StateNotifierProvider.family<ClassifyNotifier, ClassifyState, int>(
  (ref, testId) => ClassifyNotifier(ref),
);

// ── Top matches ────────────────────────────────────────────────────────────
final topMatchesProvider =
    FutureProvider.family<Map<String, dynamic>, int>((ref, testId) async {
  final dio = ref.read(dioProvider);
  final resp = await dio.get('/classify/reference-matches/$testId');
  return resp.data as Map<String, dynamic>;
});
