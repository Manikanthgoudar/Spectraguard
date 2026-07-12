import 'package:flutter/material.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/shared/models/test.dart';

class ClassificationBadge extends StatelessWidget {
  const ClassificationBadge({super.key, required this.result, this.compact = false});
  final ClassificationResult result;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final (label, color, icon) = switch (result) {
      ClassificationResult.genuine => ('Genuine', AppColors.genuine, Icons.check_circle),
      ClassificationResult.potentially_counterfeit => ('Counterfeit', AppColors.counterfeit, Icons.dangerous),
      ClassificationResult.requires_verification => ('Verify', AppColors.requiresVerification, Icons.warning_amber),
      ClassificationResult.pending => ('Pending', AppColors.pending, Icons.hourglass_empty),
    };

    if (compact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
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
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.4)),
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
