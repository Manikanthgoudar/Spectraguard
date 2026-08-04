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
    this.isActive,
    this.createdAt,
    this.profilePhoto,
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
  final int? isActive;
  final String? createdAt;
  final String? profilePhoto; // relative URL path, e.g. /uploads/photos/1_abc.jpg

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
        isActive: j['is_active'] as int?,
        createdAt: j['created_at'] as String?,
        profilePhoto: j['profile_photo'] as String?,
      );

  User copyWith({
    String? fullName,
    String? phone,
    String? city,
    String? email,
    String? profilePhoto,
    bool clearPhoto = false,
  }) =>
      User(
        id: id,
        fullName: fullName ?? this.fullName,
        email: email ?? this.email,
        role: role,
        phone: phone ?? this.phone,
        organization: organization,
        licenseNumber: licenseNumber,
        designation: designation,
        city: city ?? this.city,
        isActive: isActive,
        createdAt: createdAt,
        profilePhoto: clearPhoto ? null : (profilePhoto ?? this.profilePhoto),
      );
}
