/// Native (non-web) implementation of PDF download.
/// Saves to the app's documents directory and returns the local file path.
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

Future<String> downloadPdf({
  required Dio dio,
  required int testId,
}) async {
  final dir = await getApplicationDocumentsDirectory();
  final filePath = '${dir.path}/spectraguard_report_test$testId.pdf';
  await dio.download('/reports/$testId', filePath);
  return filePath;
}
