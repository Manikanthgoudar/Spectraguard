import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/api/api_client.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/core/theme/app_theme.dart';

/// A shared avatar widget that always stays in sync with [authProvider].
/// Shows the profile photo when available, falls back to initials.
///
/// Use [ProfileAvatar] everywhere a user avatar is needed so they all
/// update automatically when the photo changes.
class ProfileAvatar extends ConsumerWidget {
  const ProfileAvatar({
    super.key,
    required this.size,
    this.showGradient = false,
    this.borderWidth = 0,
    this.borderColor,
  });

  /// Diameter of the avatar circle in logical pixels.
  final double size;

  /// When true a teal gradient background is used (dashboard header style).
  /// When false a light teal tinted background with a primary-colour border is
  /// used (sidebar / profile page style).
  final bool showGradient;

  /// Optional border width drawn around the circle.
  final double borderWidth;

  /// Optional border colour; defaults to [AppColors.primary] at 25 % opacity.
  final Color? borderColor;

  static String _initials(String name) {
    final parts = name.trim().split(' ');
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  static String _buildUrl(String photo) {
    if (photo.startsWith('http')) return photo;
    return '$apiBaseUrl$photo';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final initials = _initials(user?.fullName ?? '?');
    final photoUrl = (user?.profilePhoto?.isNotEmpty == true)
        ? _buildUrl(user!.profilePhoto!)
        : null;

    Widget fallback = Center(
      child: Text(
        initials,
        style: TextStyle(
          color: showGradient ? Colors.white : AppColors.primary,
          fontSize: size * 0.34,
          fontWeight: FontWeight.w700,
        ),
      ),
    );

    Widget content;
    if (photoUrl != null) {
      content = Image.network(
        photoUrl,
        fit: BoxFit.cover,
        // Re-use the key so Flutter reloads the image when the URL changes.
        key: ValueKey(photoUrl),
        errorBuilder: (_, __, ___) => fallback,
      );
    } else {
      content = fallback;
    }

    BoxDecoration decoration;
    if (showGradient) {
      decoration = BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.35),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      );
    } else {
      decoration = BoxDecoration(
        shape: BoxShape.circle,
        color: AppColors.primary.withOpacity(0.12),
        border: borderWidth > 0
            ? Border.all(
                color: borderColor ??
                    AppColors.primary.withOpacity(0.25),
                width: borderWidth,
              )
            : null,
      );
    }

    return Container(
      width: size,
      height: size,
      decoration: decoration,
      child: ClipOval(child: content),
    );
  }
}
