// ignore_for_file: constant_identifier_names

enum ClassificationResult {
  genuine,
  potentially_counterfeit,
  requires_verification,
  pending,
}

class SpectraTest {
  const SpectraTest({
    required this.id,
    required this.userId,
    required this.drugName,
    required this.classificationResult,
    required this.testedAt,
    this.batchNumber,
    this.manufacturer,
    this.expiryDate,
    this.uploadedCsvPath,
    this.confidenceScore,
    this.matchedReferenceId,
  });

  final int id;
  final int userId;
  final String drugName;
  final ClassificationResult classificationResult;
  final DateTime testedAt;
  final String? batchNumber;
  final String? manufacturer;
  final String? expiryDate;
  final String? uploadedCsvPath;
  final double? confidenceScore;
  final int? matchedReferenceId;

  factory SpectraTest.fromJson(Map<String, dynamic> j) => SpectraTest(
        id: j['id'] as int,
        userId: j['user_id'] as int,
        drugName: j['drug_name'] as String,
        classificationResult: ClassificationResult.values.firstWhere(
          (e) => e.name == (j['classification_result'] as String),
          orElse: () => ClassificationResult.pending,
        ),
        testedAt: DateTime.parse(j['tested_at'] as String),
        batchNumber: j['batch_number'] as String?,
        manufacturer: j['manufacturer'] as String?,
        expiryDate: j['expiry_date'] as String?,
        uploadedCsvPath: j['uploaded_csv_path'] as String?,
        confidenceScore: (j['confidence_score'] as num?)?.toDouble(),
        matchedReferenceId: j['matched_reference_id'] as int?,
      );
}
