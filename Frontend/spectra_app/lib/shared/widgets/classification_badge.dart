import 'package:flutter/material.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/shared/models/test.dart';

class ClassificationBadge extends StatelessWidget {
  const ClassificationBadge({
    super.key,
    required this.result,
    this.statusString,
    this.compact = false,
  });

  final ClassificationResult result;
  final String? statusString;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    String label;
    Color color;
    IconData icon;

    if (statusString != null) {
      switch (statusString) {
        case 'AUTHENTIC_REFERENCE_MATCH':
          label = 'Authentic Match';
          color = AppColors.genuine;
          icon = Icons.verified;
          break;
        case 'UNKNOWN':
          label = 'Unknown / Verification Needed';
          color = AppColors.requiresVerification;
          icon = Icons.help;
          break;
        case 'REFERENCE_NOT_AVAILABLE':
          label = 'No Reference';
          color = AppColors.pending;
          icon = Icons.info;
          break;
        case 'INVALID_INPUT':
          label = 'Invalid Input';
          color = AppColors.error;
          icon = Icons.warning;
          break;
        default:
          label = statusString!.replaceAll('_', ' ');
          color = AppColors.requiresVerification;
          icon = Icons.help;
      }
    } else {
      final tuple = switch (result) {
        ClassificationResult.genuine =>
          ('Authentic Match', AppColors.genuine, Icons.check_circle),
        ClassificationResult.potentially_counterfeit =>
          ('Requires Verification', AppColors.requiresVerification, Icons.warning_amber),
        ClassificationResult.requires_verification =>
          ('Verify', AppColors.requiresVerification, Icons.warning_amber),
        ClassificationResult.pending =>
          ('Pending', AppColors.pending, Icons.hourglass_empty),
      };
      label = tuple.$1;
      color = tuple.$2;
      icon = tuple.$3;
    }

    if (compact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
