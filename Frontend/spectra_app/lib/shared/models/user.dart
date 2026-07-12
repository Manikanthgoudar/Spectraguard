enum UserRole { public, pharmacist, investigator, admin }

class User {
  const User({
    required this.id,
    required this.fullName,
    required this.email,
    required this.role,
    this.phone,
    this.organization,
    this.licenseNumber,
    this.designation,
    this.city,
  });

  final int id;
  final String fullName;
  final String email;
  final UserRole role;
  final String? phone;
  final String? organization;
  final String? licenseNumber;
  final String? designation;
  final String? city;

  factory User.fromJson(Map<String, dynamic> j) => User(
        id: j['id'] as int,
        fullName: j['full_name'] as String,
        email: j['email'] as String,
        role: UserRole.values.firstWhere(
          (e) => e.name == (j['role'] as String),
          orElse: () => UserRole.public,
        ),
        phone: j['phone'] as String?,
        organization: j['organization'] as String?,
        licenseNumber: j['license_number'] as String?,
        designation: j['designation'] as String?,
        city: j['city'] as String?,
      );
}
