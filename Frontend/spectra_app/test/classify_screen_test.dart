import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:spectra_app/features/classify/providers/classify_provider.dart';
import 'package:spectra_app/features/classify/screens/classify_screen.dart';
import 'package:spectra_app/features/spectra/providers/spectra_provider.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/models/raman_analysis_response.dart';
import 'package:spectra_app/shared/models/test.dart';

void main() {
  const authenticResponse = RamanAnalysisResponse(
    success: true,
    drugName: 'Amoxicillin Trihydrate',
    predictedCompound: 'Acetone',
    compoundConfidence: 0.9821,
    authenticationStatus: 'AUTHENTIC_REFERENCE_MATCH',
    similarityScore: 0.9942,
    authenticationThreshold: 0.9860,
    referenceId: 'REF-PARAGUAY-AMOX-001',
    message: 'Matches authentic reference standard for Amoxicillin Trihydrate.',
    topReferenceMatches: [
      {
        'rank': 1,
        'reference_id': 'REF-PARAGUAY-AMOX-001',
        'drug_name': 'Amoxicillin Trihydrate',
        'cosine_similarity': 0.9942,
        'manufacturer': 'Paraguay OTC Reference',
        'brand': 'Para-Amox',
      },
      {
        'rank': 2,
        'reference_id': 'REF-PARAGUAY-AMOX-002',
        'drug_name': 'Amoxicillin Generic',
        'cosine_similarity': 0.00023,
        'manufacturer': 'Paraguay OTC Reference',
        'brand': 'Generic-Amox',
      },
    ],
  );

  const counterfeitResponse = RamanAnalysisResponse(
    success: true,
    drugName: 'Amoxicillin Trihydrate',
    predictedCompound: 'Unknown',
    compoundConfidence: 0.2100,
    authenticationStatus: 'UNKNOWN',
    similarityScore: 0.4200,
    authenticationThreshold: 0.9860,
    referenceId: null,
    message: 'Low similarity score detected. Sample fails authentication.',
    topReferenceMatches: [
      {
        'rank': 1,
        'reference_id': 'REF-PARAGUAY-AMOX-001',
        'drug_name': 'Amoxicillin Trihydrate',
        'cosine_similarity': 0.4200,
        'manufacturer': 'Paraguay OTC Reference',
        'brand': 'Para-Amox',
      },
    ],
  );

  final mockTest = SpectraTest(
    id: 101,
    userId: 1,
    drugName: 'Amoxicillin Trihydrate',
    classificationResult: ClassificationResult.genuine,
    testedAt: DateTime.parse('2026-08-15T00:00:00Z'),
    batchNumber: 'BATCH-2024-01',
  );

  final mockSpectraData = {
    'wavenumber_data': [400.0, 800.0, 1200.0, 1600.0, 2000.0, 3425.0],
    'intensity_data': [0.1, 0.5, 0.9, 0.4, 0.2, 0.05],
  };

  final mockMatchesData = {
    'matches': [
      {
        'rank': 1,
        'drug_name': 'Amoxicillin Trihydrate Standard',
        'cosine_similarity': 0.9942,
        'manufacturer': 'Pharma Corp',
      },
    ],
  };

  Widget buildTestWidget({
    required Size screenSize,
    required RamanAnalysisResponse response,
  }) {
    return ProviderScope(
      overrides: [
        classifyProvider(101).overrideWith(
          (ref) => ClassifyNotifierMock(
            ClassifyState(
              ramanResult: response,
              isLoading: false,
            ),
          ),
        ),
        spectraDataProvider(101).overrideWith(
          (ref) async => mockSpectraData,
        ),
        testDetailProvider(101).overrideWith(
          (ref) async => mockTest,
        ),
        topMatchesProvider(101).overrideWith(
          (ref) async => mockMatchesData,
        ),
      ],
      child: MaterialApp(
        home: MediaQuery(
          data: MediaQueryData(size: screenSize),
          child: const ClassifyScreen(testId: 101),
        ),
      ),
    );
  }

  group('ClassifyScreen Tests', () {
    testWidgets('CASE 1: Displays AUTHENTIC for matching spectrum on mobile', (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(buildTestWidget(
        screenSize: const Size(390, 844),
        response: authenticResponse,
      ));
      await tester.pumpAndSettle();

      // Check ML Classifier section is omitted
      expect(find.text('ML Compound Classifier Output (Technical Prediction)'), findsNothing);

      // Check AUTHENTIC final result card and evidence
      expect(find.text('AUTHENTIC'), findsOneWidget);
      expect(find.text('Reference Match Similarity'), findsOneWidget);
      expect(find.text('99.42%'), findsWidgets);
      expect(find.text('98.60%'), findsOneWidget);
      expect(find.text('REF-PARAGUAY-AMOX-001'), findsWidgets);
      expect(find.text('Spectral Profile'), findsOneWidget);
      expect(find.text('Top Reference Matches'), findsOneWidget);

      // Check small similarity precision formatting (0.023% instead of 0.00%)
      expect(find.text('0.023%'), findsOneWidget);
    });

    testWidgets('CASE 2: Displays COUNTERFEIT for low similarity spectrum on desktop', (tester) async {
      tester.view.physicalSize = const Size(1280, 720);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(buildTestWidget(
        screenSize: const Size(1280, 720),
        response: counterfeitResponse,
      ));
      await tester.pumpAndSettle();

      // Check ML Classifier section is omitted
      expect(find.text('ML Compound Classifier Output (Technical Prediction)'), findsNothing);

      // Check COUNTERFEIT final result card and evidence
      expect(find.text('COUNTERFEIT'), findsOneWidget);
      expect(find.text('42.00%'), findsWidgets);
      expect(find.text('98.60%'), findsOneWidget);
      expect(find.text('Top Reference Matches'), findsOneWidget);
    });
  });
}

class ClassifyNotifierMock extends StateNotifier<ClassifyState> implements ClassifyNotifier {
  ClassifyNotifierMock(ClassifyState initial) : super(initial);

  @override
  Future<RamanAnalysisResponse?> analyzeRaman({required dynamic platformFile, required String drugName}) async {
    return state.ramanResult;
  }

  @override
  Future<RamanAnalysisResponse?> classify(int testId) async {
    return state.ramanResult;
  }

  @override
  void reset() {}

  @override
  void setRamanResult(RamanAnalysisResponse response) {
    state = state.copyWith(ramanResult: response);
  }
}
