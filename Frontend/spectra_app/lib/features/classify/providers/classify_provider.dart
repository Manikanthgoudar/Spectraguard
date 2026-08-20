import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/api/api_client.dart';
import 'package:spectra_app/core/api/raman_analysis_service.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/shared/models/classification.dart';
import 'package:spectra_app/shared/models/raman_analysis_response.dart';

class ClassifyState {
  const ClassifyState({
    this.isLoading = false,
    this.result,
    this.ramanResult,
    this.error,
  });

  final bool isLoading;
  final ClassificationResponse? result;
  final RamanAnalysisResponse? ramanResult;
  final String? error;

  ClassifyState copyWith({
    bool? isLoading,
    ClassificationResponse? result,
    RamanAnalysisResponse? ramanResult,
    String? error,
  }) {
    return ClassifyState(
      isLoading: isLoading ?? this.isLoading,
      result: result ?? this.result,
      ramanResult: ramanResult ?? this.ramanResult,
      error: error,
    );
  }
}

class ClassifyNotifier extends StateNotifier<ClassifyState> {
  ClassifyNotifier(this._ref) : super(const ClassifyState());
  final Ref _ref;

  /// Analyze spectrum using FastAPI POST /api/analyze-raman endpoint
  Future<RamanAnalysisResponse?> analyzeRaman({
    required PlatformFile platformFile,
    required String drugName,
  }) async {
    state = const ClassifyState(isLoading: true);
    try {
      final service = RamanAnalysisService(dio: _ref.read(dioProvider));
      final response = await service.analyzeRamanSpectrum(
        platformFile: platformFile,
        drugName: drugName,
      );
      state = ClassifyState(ramanResult: response);
      return response;
    } on RamanAnalysisException catch (e) {
      state = ClassifyState(error: e.message);
      return null;
    } catch (e) {
      state = ClassifyState(
        error: 'An unexpected error occurred during Raman analysis.',
      );
      return null;
    }
  }

  /// Run legacy classification endpoint POST /classify/$testId
  Future<void> classify(int testId) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final dio = _ref.read(dioProvider);
      final resp = await dio.post('/classify/$testId');
      final classificationResponse = ClassificationResponse.fromJson(
        resp.data as Map<String, dynamic>,
      );
      state = state.copyWith(
        isLoading: false,
        result: classificationResponse,
      );
    } on DioException catch (e) {
      String userMessage = 'Classification failed.';
      if (e.response?.data is Map && e.response?.data['detail'] != null) {
        userMessage = e.response!.data['detail'].toString();
      } else if (e.type == DioExceptionType.connectionTimeout) {
        userMessage = 'Network connection timed out.';
      } else if (e.type == DioExceptionType.connectionError) {
        userMessage = 'Unable to connect to server.';
      }
      state = state.copyWith(isLoading: false, error: userMessage);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Classification failed: ${e.toString()}',
      );
    }
  }

  void setRamanResult(RamanAnalysisResponse response) {
    state = state.copyWith(ramanResult: response);
  }

  void reset() => state = const ClassifyState();
}

final classifyProvider =
    StateNotifierProvider.family<ClassifyNotifier, ClassifyState, int>(
  (ref, testId) => ClassifyNotifier(ref),
);

/// Map storing latest RamanAnalysisResponse objects by test ID
final ramanResultsStoreProvider =
    StateProvider<Map<int, RamanAnalysisResponse>>((ref) => {});

// ── Top matches ────────────────────────────────────────────────────────────
final topMatchesProvider =
    FutureProvider.family<Map<String, dynamic>, int>((ref, testId) async {
  final dio = ref.read(dioProvider);
  final resp = await dio.get('/classify/reference-matches/$testId');
  return resp.data as Map<String, dynamic>;
});
