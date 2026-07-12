import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/models/test.dart';
import 'package:spectra_app/shared/widgets/classification_badge.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';

class TestDetailScreen extends ConsumerWidget {
  const TestDetailScreen({super.key, required this.testId});
  final int testId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final testAsync = ref.watch(testDetailProvider(testId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: const Text('Test Details')),
      body: testAsync.when(
        loading: () => const LoadingOverlay(),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (test) => _TestDetailBody(test: test),
      ),
    );
  }
}

class _TestDetailBody extends StatelessWidget {
  const _TestDetailBody({required this.test});
  final SpectraTest test;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Result card
          _ResultCard(test: test),
          const SizedBox(height: 20),

          // Drug info
          _Section(
            title: 'Drug Information',
            children: [
              _InfoRow('Drug Name', test.drugName),
              if (test.batchNumber != null)
                _InfoRow('Batch Number', test.batchNumber!),
              if (test.manufacturer != null)
                _InfoRow('Manufacturer', test.manufacturer!),
              if (test.expiryDate != null)
                _InfoRow('Expiry Date', test.expiryDate!),
              _InfoRow('Test Date',
                  DateFormat('MMMM d, y – HH:mm').format(test.testedAt)),
            ],
          ),
          const SizedBox(height: 16),

          if (test.confidenceScore != null) ...[
            _Section(
              title: 'Classification Details',
              children: [
                _InfoRow('Confidence',
                    '${(test.confidenceScore! * 100).toStringAsFixed(2)}%'),
                if (test.matchedReferenceId != null)
                  _InfoRow('Matched Reference',
                      'Ref #${test.matchedReferenceId}'),
              ],
            ),
            const SizedBox(height: 16),
          ],

          // Actions
          _Actions(test: test),
        ],
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.test});
  final SpectraTest test;

  @override
  Widget build(BuildContext context) {
    final (bg, icon, desc) = switch (test.classificationResult) {
      ClassificationResult.genuine => (
          AppColors.genuine.withValues(alpha: 0.08),
          Icons.check_circle_outline,
          'Drug authenticated as genuine based on spectral analysis.',
        ),
      ClassificationResult.potentially_counterfeit => (
          AppColors.counterfeit.withValues(alpha: 0.08),
          Icons.dangerous_outlined,
          'Warning: Spectral profile is inconsistent. Possible counterfeit.',
        ),
      ClassificationResult.requires_verification => (
          AppColors.requiresVerification.withValues(alpha: 0.08),
          Icons.warning_amber_outlined,
          'Spectral similarity is ambiguous. Further verification recommended.',
        ),
      ClassificationResult.pending => (
          AppColors.pending.withValues(alpha: 0.08),
          Icons.hourglass_empty,
          'Test has not been classified yet.',
        ),
    };

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 28,
                  color: _colorForResult(test.classificationResult)),
              const SizedBox(width: 10),
              ClassificationBadge(result: test.classificationResult),
            ],
          ),
          const SizedBox(height: 12),
          Text(desc, style: Theme.of(context).textTheme.bodyLarge),
          if (test.confidenceScore != null) ...[
            const SizedBox(height: 12),
            LinearProgressIndicator(
              value: test.confidenceScore,
              backgroundColor:
                  _colorForResult(test.classificationResult).withValues(alpha: 0.2),
              valueColor: AlwaysStoppedAnimation<Color>(
                _colorForResult(test.classificationResult),
              ),
              borderRadius: BorderRadius.circular(4),
              minHeight: 6,
            ),
            const SizedBox(height: 4),
            Text(
              'Confidence: ${(test.confidenceScore! * 100).toStringAsFixed(1)}%',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ],
      ),
    );
  }

  Color _colorForResult(ClassificationResult r) => switch (r) {
        ClassificationResult.genuine => AppColors.genuine,
        ClassificationResult.potentially_counterfeit => AppColors.counterfeit,
        ClassificationResult.requires_verification =>
          AppColors.requiresVerification,
        ClassificationResult.pending => AppColors.pending,
      };
}

class _Actions extends StatelessWidget {
  const _Actions({required this.test});
  final SpectraTest test;

  @override
  Widget build(BuildContext context) {
    final isPending =
        test.classificationResult == ClassificationResult.pending;

    return Column(
      children: [
        if (isPending)
          ElevatedButton.icon(
            onPressed: () => context.go('/classify/${test.id}'),
            icon: const Icon(Icons.analytics_outlined),
            label: const Text('Run Classification'),
          ),
        if (!isPending) ...[
          ElevatedButton.icon(
            onPressed: () => context.go('/classify/${test.id}'),
            icon: const Icon(Icons.refresh),
            label: const Text('Re-classify'),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () => context.go('/reports/${test.id}'),
            icon: const Icon(Icons.picture_as_pdf_outlined),
            label: const Text('Generate / Download Report'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.primary,
            ),
          ),
        ],
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.children});
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          const Divider(height: 1),
          const SizedBox(height: 10),
          ...children,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(label,
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: AppColors.textSecondary)),
          ),
          Expanded(
            child: Text(value,
                style: Theme.of(context).textTheme.bodyLarge),
          ),
        ],
      ),
    );
  }
}
