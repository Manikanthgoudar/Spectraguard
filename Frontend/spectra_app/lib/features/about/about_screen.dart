import 'package:flutter/material.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/shared/widgets/app_shell_app_bar.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final padding = context.pagePadding;
    final isWide = context.isWide;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppShellAppBar(title: 'About'),
      body: SingleChildScrollView(
        child: ContentContainer(
          padding: padding.add(const EdgeInsets.symmetric(vertical: 24)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Header ──────────────────────────────────────────────────
              _HeaderCard(),
              const SizedBox(height: 16),

              // ── What it does ─────────────────────────────────────────────
              _SectionCard(
                title: 'What it does',
                child: Text(
                  'SpectraGuard uses Raman spectroscopy to authenticate '
                  'pharmaceutical products. By comparing a sample\'s spectral '
                  'fingerprint against a curated reference database, the app '
                  'instantly classifies drugs as genuine, potentially counterfeit, '
                  'or requiring further verification — helping laboratories and '
                  'field inspectors catch substandard medicines before they reach '
                  'patients.',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ),
              const SizedBox(height: 16),

              // ── Feature tiles ────────────────────────────────────────────
              isWide
                  ? _FeatureTilesRow()
                  : _FeatureTilesColumn(),
              const SizedBox(height: 16),

              // ── How it works ─────────────────────────────────────────────
              _SectionCard(
                title: 'How it works',
                child: _HowItWorksList(),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Header card ───────────────────────────────────────────────────────────────

class _HeaderCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          // App icon — mirrors the sidebar brand logo
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.primary,
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Icon(Icons.biotech, color: Colors.white, size: 34),
          ),
          const SizedBox(height: 14),
          Text(
            'SpectraGuard',
            style: Theme.of(context).textTheme.titleLarge,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            'Version 1.0.0',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

// ── Reusable section card (title + arbitrary child) ───────────────────────────

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }
}

// ── Feature tile — same card style as StatCard / quick action cards ───────────

class _FeatureTile extends StatelessWidget {
  const _FeatureTile({
    required this.icon,
    required this.color,
    required this.label,
    required this.description,
  });
  final IconData icon;
  final Color color;
  final String label;
  final String description;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 22),
          ),
          const SizedBox(height: 10),
          Text(
            label,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 4),
          Text(
            description,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

// ── Three feature tiles: horizontal row for wide screens ─────────────────────

class _FeatureTilesRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: _FeatureTile(
              icon: Icons.stacked_line_chart,
              color: AppColors.primary,
              label: 'Spectral Analysis',
              description:
                  'Processes raw Raman CSV data and extracts spectral peaks for comparison.',
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _FeatureTile(
              icon: Icons.verified_outlined,
              color: AppColors.secondary,
              label: 'Authentication',
              description:
                  'Matches sample spectra against verified reference profiles in the database.',
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: _FeatureTile(
              icon: Icons.description_outlined,
              color: AppColors.warning,
              label: 'Real-time Reports',
              description:
                  'Generates downloadable PDF reports with classification results and confidence scores.',
            ),
          ),
        ],
      ),
    );
  }
}

// ── Three feature tiles: vertical stack for mobile ───────────────────────────

class _FeatureTilesColumn extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _FeatureTile(
          icon: Icons.stacked_line_chart,
          color: AppColors.primary,
          label: 'Spectral Analysis',
          description:
              'Processes raw Raman CSV data and extracts spectral peaks for comparison.',
        ),
        const SizedBox(height: 12),
        _FeatureTile(
          icon: Icons.verified_outlined,
          color: AppColors.secondary,
          label: 'Authentication',
          description:
              'Matches sample spectra against verified reference profiles in the database.',
        ),
        const SizedBox(height: 12),
        _FeatureTile(
          icon: Icons.description_outlined,
          color: AppColors.warning,
          label: 'Real-time Reports',
          description:
              'Generates downloadable PDF reports with classification results and confidence scores.',
        ),
      ],
    );
  }
}

// ── How it works: 3 numbered steps, same row layout as existing tiles ─────────

class _HowItWorksList extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    const steps = [
      (
        '1',
        Icons.upload_file_rounded,
        AppColors.primary,
        'Upload',
        'Export a Raman spectrum as a CSV file and upload it via the app.',
      ),
      (
        '2',
        Icons.manage_search,
        AppColors.secondary,
        'Match',
        'The engine compares the spectrum against the reference database using cosine similarity.',
      ),
      (
        '3',
        Icons.fact_check_outlined,
        AppColors.warning,
        'Classify',
        'A confidence score determines whether the sample is genuine, counterfeit, or borderline.',
      ),
    ];

    return Column(
      children: steps.asMap().entries.map((entry) {
        final isLast = entry.key == steps.length - 1;
        final step = entry.value;
        return Column(
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Step number badge
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: step.$3.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Center(
                    child: Text(
                      step.$1,
                      style: TextStyle(
                        color: step.$3,
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        step.$4,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        step.$5,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (!isLast) ...[
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 12),
            ],
          ],
        );
      }).toList(),
    );
  }
}
