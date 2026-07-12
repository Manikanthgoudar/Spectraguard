class AdminStats {
  const AdminStats({
    required this.totalTests,
    required this.totalUsers,
    required this.counterfeitsCount,
    required this.genuineCount,
    required this.requiresVerificationCount,
    required this.counterfeiteDetectionRate,
    required this.mostTestedDrugs,
    required this.usersByRole,
  });

  final int totalTests;
  final int totalUsers;
  final int counterfeitsCount;
  final int genuineCount;
  final int requiresVerificationCount;
  final double counterfeiteDetectionRate;
  final List<Map<String, dynamic>> mostTestedDrugs;
  final Map<String, int> usersByRole;

  factory AdminStats.fromJson(Map<String, dynamic> j) => AdminStats(
        totalTests: j['total_tests'] as int,
        totalUsers: j['total_users'] as int,
        counterfeitsCount: j['counterfeit_count'] as int,
        genuineCount: j['genuine_count'] as int,
        requiresVerificationCount: j['requires_verification_count'] as int,
        counterfeiteDetectionRate:
            (j['counterfeit_detection_rate'] as num).toDouble(),
        mostTestedDrugs: List<Map<String, dynamic>>.from(
          j['most_tested_drugs'] as List,
        ),
        usersByRole: Map<String, int>.from(
          (j['users_by_role'] as Map).map(
            (k, v) => MapEntry(k as String, (v as num).toInt()),
          ),
        ),
      );
}

class AdminUser {
  const AdminUser({
    required this.id,
    required this.fullName,
    required this.email,
    required this.role,
    required this.isActive,
    this.organization,
    this.designation,
    this.phone,
    this.licenseNumber,
    this.city,
    this.createdAt,
  });

  final int id;
  final String fullName;
  final String email;
  final String role;
  final int isActive;
  final String? organization;
  final String? designation;
  final String? phone;
  final String? licenseNumber;
  final String? city;
  final DateTime? createdAt;

  factory AdminUser.fromJson(Map<String, dynamic> j) => AdminUser(
        id: j['id'] as int,
        fullName: j['full_name'] as String,
        email: j['email'] as String,
        role: j['role'] as String,
        isActive: j['is_active'] as int,
        organization: j['organization'] as String?,
        designation: j['designation'] as String?,
        phone: j['phone'] as String?,
        licenseNumber: j['license_number'] as String?,
        city: j['city'] as String?,
        createdAt: j['created_at'] != null
            ? DateTime.parse(j['created_at'] as String)
            : null,
      );
}
