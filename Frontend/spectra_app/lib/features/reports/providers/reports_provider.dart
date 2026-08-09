import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/features/reports/providers/pdf_downloader.dart'
    if (dart.library.html) 'package:spectra_app/features/reports/providers/pdf_downloader_web.dart';

class ReportState {
  const ReportState({
    this.isGenerating = false,
    this.isDownloading = false,
    this.localPath,
    this.error,
  });
  final bool isGenerating;
  final bool isDownloading;
  final String? localPath;
  final String? error;
}

class ReportNotifier extends StateNotifier<ReportState> {
  ReportNotifier(this._ref, this.testId) : super(const ReportState());

  final Ref _ref;
  final int testId;

  Future<void> generate() async {
    state = const ReportState(isGenerating: true);
    try {
      final dio = _ref.read(dioProvider);
      await dio.post('/reports/generate/$testId');
      state = const ReportState();
    } on Exception catch (e) {
      state = ReportState(error: _extractMessage(e));
    }
  }

  Future<void> download() async {
    state = const ReportState(isDownloading: true);
    try {
      final dio = _ref.read(dioProvider);
      try {
        final savedPath = await downloadPdf(
          dio: dio,
          testId: testId,
        );
        state = ReportState(localPath: savedPath);
      } on DioException catch (e) {
        if (e.response?.statusCode == 404) {
          // Auto-generate report if not generated yet, then attempt download
          state = const ReportState(isGenerating: true);
          await dio.post('/reports/generate/$testId');
          state = const ReportState(isDownloading: true);
          final savedPath = await downloadPdf(
            dio: dio,
            testId: testId,
          );
          state = ReportState(localPath: savedPath);
        } else {
          rethrow;
        }
      }
    } on Exception catch (e) {
      state = ReportState(error: _extractMessage(e));
    }
  }

  String _extractMessage(Object e) {
    if (e is DioException) {
      if (e.response?.data is Map && (e.response!.data as Map).containsKey('detail')) {
        return (e.response!.data as Map)['detail'].toString();
      }
      if (e.type == DioExceptionType.connectionError) {
        return 'Connection error: Unable to reach backend API server.';
      }
      if (e.message != null && e.message!.isNotEmpty) {
        return e.message!;
      }
    }
    return e.toString();
  }
}

final reportProvider =
    StateNotifierProvider.family<ReportNotifier, ReportState, int>(
  (ref, testId) => ReportNotifier(ref, testId),
);
