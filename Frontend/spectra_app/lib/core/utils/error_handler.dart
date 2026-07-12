import 'package:dio/dio.dart';

String parseError(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map) {
      return (data['detail'] ?? data['message'] ?? 'Request failed').toString();
    }
    return error.message ?? 'Network error';
  }
  return error.toString();
}
