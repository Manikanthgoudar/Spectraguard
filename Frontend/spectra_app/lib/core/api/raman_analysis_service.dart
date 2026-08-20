import 'dart:io';
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:spectra_app/core/api/api_client.dart';
import 'package:spectra_app/shared/models/raman_analysis_response.dart';

class RamanAnalysisException implements Exception {
  final String message;
  final int? statusCode;

  RamanAnalysisException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class RamanAnalysisService {
  final Dio _dio;

  RamanAnalysisService({Dio? dio}) : _dio = dio ?? createDio();

  /// Fetch available reference drugs via GET /reference/drugs
  Future<List<String>> fetchAvailableDrugs() async {
    try {
      final response = await _dio.get('/reference/drugs');
      if (response.data is Map<String, dynamic>) {
        final data = response.data as Map<String, dynamic>;
        if (data['drugs'] is List) {
          return (data['drugs'] as List).map((e) => e.toString()).toList();
        }
      }
      return [];
    } catch (_) {
      try {
        final response = await _dio.get('/api/reference/drugs');
        if (response.data is Map<String, dynamic>) {
          final data = response.data as Map<String, dynamic>;
          if (data['drugs'] is List) {
            return (data['drugs'] as List).map((e) => e.toString()).toList();
          }
        }
      } catch (e) {
        throw RamanAnalysisException(
          'Failed to load available reference drugs from server.',
        );
      }
      return [];
    }
  }

  /// Execute Raman spectrum analysis via POST /api/analyze-raman

  Future<RamanAnalysisResponse> analyzeRamanSpectrum({
    required PlatformFile platformFile,
    required String drugName,
  }) async {
    try {
      final bytes = platformFile.bytes;
      final filename = platformFile.name;

      MultipartFile multipartFile;
      if (bytes != null) {
        multipartFile = MultipartFile.fromBytes(bytes, filename: filename);
      } else if (platformFile.path != null && !kIsWeb) {
        multipartFile = await MultipartFile.fromFile(
          platformFile.path!,
          filename: filename,
        );
      } else {
        throw RamanAnalysisException(
          'Could not read file data. Please select a valid CSV file.',
        );
      }

      final formData = FormData.fromMap({
        'drug_name': drugName.trim(),
        'file': multipartFile,
      });

      final requestPath = '/api/analyze-raman';
      final fullUrl = '${_dio.options.baseUrl}$requestPath';
      if (kDebugMode) {
        debugPrint('[RamanAnalysisService] Executing request to: $fullUrl');
      }

      final response = await _dio.post(
        requestPath,
        data: formData,
      );

      if (response.data is Map<String, dynamic>) {
        return RamanAnalysisResponse.fromJson(
          response.data as Map<String, dynamic>,
        );
      } else {
        throw RamanAnalysisException(
          'Unexpected response format received from server.',
        );
      }
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      if (e is RamanAnalysisException) rethrow;
      throw RamanAnalysisException(
        'An error occurred while analyzing the Raman spectrum: ${e.toString()}',
      );
    }
  }

  RamanAnalysisException _handleDioError(DioException error) {
    final response = error.response;
    if (response != null) {
      final statusCode = response.statusCode;
      String userMessage = 'Server error occurred during analysis.';

      if (response.data is Map<String, dynamic>) {
        final data = response.data as Map<String, dynamic>;
        if (data['detail'] != null) {
          final detail = data['detail'];
          if (detail is String) {
            userMessage = detail;
          } else if (detail is List) {
            userMessage = detail.map((e) => e.toString()).join(', ');
          }
        } else if (data['message'] != null) {
          userMessage = data['message'].toString();
        }
      }

      switch (statusCode) {
        case 400:
        case 422:
          return RamanAnalysisException(
            userMessage,
            statusCode: statusCode,
          );
        case 401:
        case 403:
          return RamanAnalysisException(
            'Session expired or not authenticated. Please log in again.',
            statusCode: statusCode,
          );
        case 404:
          return RamanAnalysisException(
            'Raman analysis endpoint not found.',
            statusCode: 404,
          );
        case 415:
          return RamanAnalysisException(
            'Unsupported File Format. Only CSV files (.csv) are accepted.',
            statusCode: 415,
          );
        case 500:
          return RamanAnalysisException(
            userMessage,
            statusCode: 500,
          );
        default:
          return RamanAnalysisException(
            'Analysis failed (HTTP $statusCode): $userMessage',
            statusCode: statusCode,
          );
      }
    }

    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return RamanAnalysisException(
        'Network timeout connecting to FastAPI server. Please check your network connection and try again.',
      );
    }

    return RamanAnalysisException(
      'Cannot connect to FastAPI server at $apiBaseUrl. Please check if the backend server is running.',
    );
  }
}
