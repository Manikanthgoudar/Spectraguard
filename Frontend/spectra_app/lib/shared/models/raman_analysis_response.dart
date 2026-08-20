class RamanAnalysisResponse {
  const RamanAnalysisResponse({
    required this.success,
    required this.drugName,
    this.predictedCompound,
    this.compoundConfidence,
    required this.authenticationStatus,
    this.similarityScore,
    this.authenticationThreshold = 0.9860,
    this.referenceId,
    required this.message,
    this.topReferenceMatches,
    this.details,
  });

  final bool success;
  final String drugName;
  final String? predictedCompound;
  final double? compoundConfidence;
  final String authenticationStatus;
  final double? similarityScore;
  final double authenticationThreshold;
  final String? referenceId;
  final String message;
  final List<Map<String, dynamic>>? topReferenceMatches;
  final Map<String, dynamic>? details;

  factory RamanAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return RamanAnalysisResponse(
      success: json['success'] as bool? ?? false,
      drugName: json['drug_name'] as String? ?? 'Unspecified',
      predictedCompound: json['predicted_compound'] as String?,
      compoundConfidence: (json['compound_confidence'] as num?)?.toDouble(),
      authenticationStatus:
          json['authentication_status'] as String? ?? 'UNKNOWN',
      similarityScore: (json['similarity_score'] as num?)?.toDouble(),
      authenticationThreshold:
          (json['authentication_threshold'] as num?)?.toDouble() ?? 0.9860,
      referenceId: json['reference_id'] as String?,
      message: json['message'] as String? ?? '',
      topReferenceMatches: (json['top_reference_matches'] as List?)
          ?.cast<Map<String, dynamic>>(),
      details: json['details'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() => {
        'success': success,
        'drug_name': drugName,
        'predicted_compound': predictedCompound,
        'compound_confidence': compoundConfidence,
        'authentication_status': authenticationStatus,
        'similarity_score': similarityScore,
        'authentication_threshold': authenticationThreshold,
        'reference_id': referenceId,
        'message': message,
        'top_reference_matches': topReferenceMatches,
        'details': details,
      };

  /// Evaluates the pharmaceutical authentication status dynamically: AUTHENTIC, COUNTERFEIT, or UNKNOWN
  String get finalAuthStatus {
    if (authenticationStatus == 'AUTHENTIC_REFERENCE_MATCH' ||
        (similarityScore != null && similarityScore! >= authenticationThreshold)) {
      return 'AUTHENTIC';
    } else if (authenticationStatus == 'COUNTERFEIT' ||
        authenticationStatus == 'POTENTIALLY_COUNTERFEIT' ||
        (similarityScore != null && similarityScore! < 0.85)) {
      return 'COUNTERFEIT';
    } else {
      return 'UNKNOWN';
    }
  }

  /// Returns user-friendly pharmaceutical authentication status text
  String get displayStatus => finalAuthStatus;

  /// Returns true if evaluated as AUTHENTIC
  bool get isAuthenticMatch => finalAuthStatus == 'AUTHENTIC';

  /// Returns true if evaluated as COUNTERFEIT
  bool get isCounterfeit => finalAuthStatus == 'COUNTERFEIT';

  /// Returns true if evaluated as UNKNOWN
  bool get isUnknown => finalAuthStatus == 'UNKNOWN';
}
