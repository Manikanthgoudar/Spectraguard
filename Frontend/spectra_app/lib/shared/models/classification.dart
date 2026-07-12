enum ClassificationResultEnum {
  genuine,
  potentiallyCounterfeit,
  requiresVerification,
  pending,
}

class ClassificationResponse {
  const ClassificationResponse({
    required this.testId,
    required this.result,
    required this.confidenceScore,
    required this.message,
    this.matchedReferenceId,
    this.matchedDrugName,
    this.cosineSimilarity,
    this.euclideanDistance,
  });

  final int testId;
  final ClassificationResultEnum result;
  final double confidenceScore;
  final String message;
  final int? matchedReferenceId;
  final String? matchedDrugName;
  final double? cosineSimilarity;
  final double? euclideanDistance;

  factory ClassificationResponse.fromJson(Map<String, dynamic> j) =>
      ClassificationResponse(
        testId: j['test_id'] as int,
        result: _parseResult(j['classification_result'] as String),
        confidenceScore: (j['confidence_score'] as num).toDouble(),
        message: j['message'] as String,
        matchedReferenceId: j['matched_reference_id'] as int?,
        matchedDrugName: j['matched_drug_name'] as String?,
        cosineSimilarity: (j['cosine_similarity'] as num?)?.toDouble(),
        euclideanDistance: (j['euclidean_distance'] as num?)?.toDouble(),
      );

  static ClassificationResultEnum _parseResult(String s) => switch (s) {
        'genuine' => ClassificationResultEnum.genuine,
        'potentially_counterfeit' =>
          ClassificationResultEnum.potentiallyCounterfeit,
        'requires_verification' =>
          ClassificationResultEnum.requiresVerification,
        _ => ClassificationResultEnum.pending,
      };
}
