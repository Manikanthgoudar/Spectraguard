import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/api/api_client.dart';
import 'package:spectra_app/core/api/raman_analysis_service.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/features/classify/providers/classify_provider.dart';
import 'package:spectra_app/shared/models/raman_analysis_response.dart';
import 'package:spectra_app/shared/models/test.dart';

class SpectraUploadState {
  const SpectraUploadState({
    this.isLoading = false,
    this.result,
    this.ramanAnalysis,
    this.error,
  });

  final bool isLoading;
  final SpectraTest? result;
  final RamanAnalysisResponse? ramanAnalysis;
  final String? error;
}

class SpectraUploadNotifier extends StateNotifier<SpectraUploadState> {
  SpectraUploadNotifier(this._ref) : super(const SpectraUploadState());

  final Ref _ref;

  Future<SpectraTest?> upload({
    required String drugName,
    required PlatformFile platformFile,
    String? batchNumber,
    String? manufacturer,
    String? expiryDate,
  }) async {
    state = const SpectraUploadState(isLoading: true);
    try {
      final dio = _ref.read(dioProvider);
      final ramanService = RamanAnalysisService(dio: dio);

      // Task 2: Execute POST /api/analyze-raman with selected drug_name and CSV file
      final ramanResponse = await ramanService.analyzeRamanSpectrum(
        platformFile: platformFile,
        drugName: drugName,
      );

      // Create test record in DB
      final bytes = platformFile.bytes;
      final filename = platformFile.name;
      final MultipartFile multipart;
      if (bytes != null) {
        multipart = MultipartFile.fromBytes(bytes, filename: filename);
      } else if (platformFile.path != null) {
        multipart = await MultipartFile.fromFile(
          platformFile.path!,
          filename: filename,
        );
      } else {
        throw RamanAnalysisException('Could not read file data');
      }

      final formData = FormData.fromMap({
        'drug_name': drugName.trim(),
        if (batchNumber != null && batchNumber.isNotEmpty)
          'batch_number': batchNumber,
        if (manufacturer != null && manufacturer.isNotEmpty)
          'manufacturer': manufacturer,
        if (expiryDate != null && expiryDate.isNotEmpty)
          'expiry_date': expiryDate,
        'file': multipart,
      });

      final resp = await dio.post('/spectra/upload', data: formData);
      final test = SpectraTest.fromJson(resp.data as Map<String, dynamic>);

      // Save ramanResponse in store keyed by test ID
      _ref.read(ramanResultsStoreProvider.notifier).update((map) {
        final newMap = Map<int, RamanAnalysisResponse>.from(map);
        newMap[test.id] = ramanResponse;
        return newMap;
      });

      // Update classifyNotifier state for this test ID
      _ref
          .read(classifyProvider(test.id).notifier)
          .setRamanResult(ramanResponse);

      state = SpectraUploadState(
        result: test,
        ramanAnalysis: ramanResponse,
      );
      return test;
    } on RamanAnalysisException catch (e) {
      state = SpectraUploadState(error: e.message);
      return null;
    } on DioException catch (e) {
      String userMsg = 'Upload failed.';
      if (e.response?.statusCode == 401 || e.response?.statusCode == 403) {
        userMsg = 'Session expired or not authenticated. Please log in again.';
      } else if (e.response?.data is Map && e.response?.data['detail'] != null) {
        userMsg = e.response!.data['detail'].toString();
      } else if (e.type == DioExceptionType.connectionTimeout) {
        userMsg = 'Network timeout occurred while uploading.';
      } else if (e.type == DioExceptionType.connectionError || e.response == null) {
        userMsg = 'Cannot connect to backend server at $apiBaseUrl. Please check if the backend server is running.';
      }
      state = SpectraUploadState(error: userMsg);
      return null;
    } catch (e) {
      state = SpectraUploadState(error: 'Upload failed: ${e.toString()}');
      return null;
    }
  }

  void reset() => state = const SpectraUploadState();

  Future<SpectraTest?> uploadSample(String filename, {String? drugName}) async {
    state = const SpectraUploadState(isLoading: true);
    try {
      final dio = _ref.read(dioProvider);
      final selectedDrug = drugName ?? 'Paracetamol';
      final formData = FormData.fromMap({'drug_name': selectedDrug});

      final resp = await dio.post(
        '/spectra/upload-sample/$filename',
        data: formData,
      );
      final test = SpectraTest.fromJson(resp.data as Map<String, dynamic>);
      state = SpectraUploadState(result: test);
      return test;
    } catch (e) {
      state = SpectraUploadState(error: e.toString());
      return null;
    }
  }
}

final spectraUploadProvider =
    StateNotifierProvider<SpectraUploadNotifier, SpectraUploadState>(
  (ref) => SpectraUploadNotifier(ref),
);

// ── Spectral data for a test (wavenumbers + intensities) ──────────────────
final spectraDataProvider =
    FutureProvider.family<Map<String, dynamic>, int>((ref, testId) async {
  final dio = ref.read(dioProvider);
  final resp = await dio.get('/spectra/$testId');
  return resp.data as Map<String, dynamic>;
});

// ── Sample datasets ────────────────────────────────────────────────────────
final sampleDatasetsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) async {
    final dio = ref.read(dioProvider);
    final resp = await dio.get('/spectra/sample-datasets');
    return List<Map<String, dynamic>>.from(resp.data['samples'] as List);
  },
);

// ── Dynamic Reference Drugs ────────────────────────────────────────────────
final availableDrugsProvider = FutureProvider<List<String>>((ref) async {
  final dio = ref.read(dioProvider);
  final service = RamanAnalysisService(dio: dio);
  return await service.fetchAvailableDrugs();
});

