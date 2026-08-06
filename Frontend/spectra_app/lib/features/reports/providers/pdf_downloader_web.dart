// ignore_for_file: avoid_web_libraries_in_flutter

library;

/// Web implementation of PDF download.
/// Fetches the PDF bytes and triggers a browser "Save As" dialog.
import 'dart:html' as html;
import 'package:dio/dio.dart';

Future<String> downloadPdf({
  required Dio dio,
  required int testId,
}) async {
  // Fetch raw bytes from the backend
  final resp = await dio.get<List<int>>(
    '/reports/$testId',
    options: Options(responseType: ResponseType.bytes),
  );

  final bytes = resp.data;
  if (bytes == null || bytes.isEmpty) {
    throw Exception('Received empty PDF from server');
  }

  final blob = html.Blob([bytes], 'application/pdf');
  final url = html.Url.createObjectUrlFromBlob(blob);
  html.AnchorElement(href: url)
    ..setAttribute('download', 'spectraguard_report_test$testId.pdf')
    ..click();
  html.Url.revokeObjectUrl(url);

  return 'Downloaded to downloads folder';
}
