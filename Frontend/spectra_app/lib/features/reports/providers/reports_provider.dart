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
      state = ReportState(error: e.toString());
    }
  }

  Future<void> download() async {
    state = const ReportState(isDownloading: true);
    try {
      final dio = _ref.read(dioProvider);
      final savedPath = await downloadPdf(
        dio: dio,
        testId: testId,
      );
      state = ReportState(localPath: savedPath);
    } on Exception catch (e) {
      state = ReportState(error: e.toString());
    }
  }
}

final reportProvider =
    StateNotifierProvider.family<ReportNotifier, ReportState, int>(
  (ref, testId) => ReportNotifier(ref, testId),
);
