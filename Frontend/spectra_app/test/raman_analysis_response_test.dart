import 'package:flutter_test/flutter_test.dart';
import 'package:spectra_app/shared/models/raman_analysis_response.dart';

void main() {
  group('RamanAnalysisResponse Model Tests', () {
    test('Parses valid AUTHENTIC_REFERENCE_MATCH JSON as AUTHENTIC', () {
      final json = {
        'success': true,
        'drug_name': 'Paracetamol',
        'predicted_compound': 'Acetone',
        'compound_confidence': 0.9845,
        'authentication_status': 'AUTHENTIC_REFERENCE_MATCH',
        'similarity_score': 0.999018,
        'authentication_threshold': 0.9860,
        'reference_id': 'REF-PARAGUAY-PARA-050',
        'message': 'Matches the available authentic reference standard for Paracetamol.',
      };

      final response = RamanAnalysisResponse.fromJson(json);

      expect(response.success, isTrue);
      expect(response.drugName, equals('Paracetamol'));
      expect(response.authenticationStatus, equals('AUTHENTIC_REFERENCE_MATCH'));
      expect(response.displayStatus, equals('AUTHENTIC'));
      expect(response.finalAuthStatus, equals('AUTHENTIC'));
      expect(response.similarityScore, equals(0.999018));
      expect(response.authenticationThreshold, equals(0.9860));
      expect(response.referenceId, equals('REF-PARAGUAY-PARA-050'));
      expect(response.isAuthenticMatch, isTrue);
      expect(response.isCounterfeit, isFalse);
      expect(response.isUnknown, isFalse);
    });

    test('Parses intermediate similarity score as UNKNOWN', () {
      final json = {
        'success': true,
        'drug_name': 'Paracetamol',
        'predicted_compound': 'Unknown',
        'compound_confidence': 0.4500,
        'authentication_status': 'UNKNOWN',
        'similarity_score': 0.9120,
        'authentication_threshold': 0.9860,
        'reference_id': null,
        'message': 'Does not sufficiently match reference standard.',
      };

      final response = RamanAnalysisResponse.fromJson(json);

      expect(response.authenticationStatus, equals('UNKNOWN'));
      expect(response.displayStatus, equals('UNKNOWN'));
      expect(response.finalAuthStatus, equals('UNKNOWN'));
      expect(response.isAuthenticMatch, isFalse);
      expect(response.isCounterfeit, isFalse);
      expect(response.isUnknown, isTrue);
    });

    test('Parses low similarity score (< 0.85) as COUNTERFEIT', () {
      final json = {
        'success': true,
        'drug_name': 'Paracetamol',
        'predicted_compound': 'Unknown',
        'compound_confidence': 0.2000,
        'authentication_status': 'UNKNOWN',
        'similarity_score': 0.4200,
        'authentication_threshold': 0.9860,
        'reference_id': null,
        'message': 'Low spectral similarity indicates suspect/counterfeit sample.',
      };

      final response = RamanAnalysisResponse.fromJson(json);

      expect(response.displayStatus, equals('COUNTERFEIT'));
      expect(response.finalAuthStatus, equals('COUNTERFEIT'));
      expect(response.isCounterfeit, isTrue);
      expect(response.isAuthenticMatch, isFalse);
      expect(response.isUnknown, isFalse);
    });

    test('Parses REFERENCE_NOT_AVAILABLE status correctly as UNKNOWN', () {
      final json = {
        'success': true,
        'drug_name': 'Amoxicillin',
        'predicted_compound': 'Acetone',
        'compound_confidence': 0.8120,
        'authentication_status': 'REFERENCE_NOT_AVAILABLE',
        'similarity_score': null,
        'authentication_threshold': 0.9860,
        'reference_id': null,
        'message': 'No active reference standard is currently available for Amoxicillin.',
      };

      final response = RamanAnalysisResponse.fromJson(json);

      expect(response.success, isTrue);
      expect(response.drugName, equals('Amoxicillin'));
      expect(response.authenticationStatus, equals('REFERENCE_NOT_AVAILABLE'));
      expect(response.displayStatus, equals('UNKNOWN'));
      expect(response.similarityScore, isNull);
      expect(response.isAuthenticMatch, isFalse);
      expect(response.isUnknown, isTrue);
    });

    test('Handles null and missing fields safely', () {
      final json = <String, dynamic>{};

      final response = RamanAnalysisResponse.fromJson(json);

      expect(response.success, isFalse);
      expect(response.drugName, equals('Unspecified'));
      expect(response.predictedCompound, null);
      expect(response.compoundConfidence, null);
      expect(response.authenticationStatus, equals('UNKNOWN'));
      expect(response.displayStatus, equals('UNKNOWN'));
      expect(response.similarityScore, null);
      expect(response.authenticationThreshold, equals(0.9860));
      expect(response.referenceId, null);
      expect(response.message, isEmpty);
    });
  });
}
