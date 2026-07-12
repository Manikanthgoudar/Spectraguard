import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/shared/models/test.dart';

class SpectraUploadState {
  const SpectraUploadState({
    this.isLoading = false,
    this.result,
    this.error,
  });
  final bool isLoading;
  final SpectraTest? result;
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

      // Use bytes so this works on both web and native
      final bytes = platformFile.bytes;
      final filename = platformFile.name;
      final MultipartFile multipart;
      if (bytes != null) {
        multipart = MultipartFile.fromBytes(bytes, filename: filename);
      } else if (platformFile.path != null) {
        // Native fallback when bytes not populated
        multipart = await MultipartFile.fromFile(platformFile.path!,
            filename: filename);
      } else {
        throw Exception('Could not read file data');
      }

      final formData = FormData.fromMap({
        'drug_name': drugName,
        if (batchNumber != null) 'batch_number': batchNumber,
        if (manufacturer != null) 'manufacturer': manufacturer,
        if (expiryDate != null) 'expiry_date': expiryDate,
        'file': multipart,
      });
      final resp = await dio.post('/spectra/upload', data: formData);
      final test = SpectraTest.fromJson(resp.data as Map<String, dynamic>);
      state = SpectraUploadState(result: test);
      return test;
    } on Exception catch (e) {
      state = SpectraUploadState(error: e.toString());
      return null;
    }
  }

  void reset() => state = const SpectraUploadState();

  Future<SpectraTest?> uploadSample(String filename) async {
    state = const SpectraUploadState(isLoading: true);
    try {
      final dio = _ref.read(dioProvider);
      // Use form data so the endpoint can accept optional fields in the future
      final formData = FormData.fromMap({});
      final resp = await dio.post(
        '/spectra/upload-sample/$filename',
        data: formData,
      );
      final test = SpectraTest.fromJson(resp.data as Map<String, dynamic>);
      state = SpectraUploadState(result: test);
      return test;
    } on Exception catch (e) {
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
