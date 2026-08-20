import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/spectra/providers/spectra_provider.dart';
import 'package:spectra_app/shared/widgets/app_shell_app_bar.dart';

/// Static list of current 11 supported reference drugs used as a fallback
/// when network data is loading or offline.
const List<String> kDefaultReferenceDrugs = [
  'Paracetamol',
  'Ibuprofen',
  'Acetylsalicylic Acid',
  'Amoxicillin',
  'Atorvastatin',
  'Azithromycin',
  'Ciprofloxacin',
  'Diclofenac',
  'Metformin',
  'Metronidazole',
  'Omeprazole',
];

class AboutScreen extends ConsumerWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final padding = context.pagePadding;
    final isWide = context.isWide;
    final drugsAsync = ref.watch(availableDrugsProvider);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: const AppShellAppBar(title: 'About SpectraGuard'),
      body: SingleChildScrollView(
        child: ContentContainer(
          padding: padding.add(const EdgeInsets.symmetric(vertical: 24)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 1. Hero Section
              const _HeroSectionCard(),
              const SizedBox(height: 20),

              // 2. What is SpectraGuard?
              const _WhatIsSpectraGuardCard(),
              const SizedBox(height: 20),

              // 3. How It Works Pipeline
              const _HowItWorksSection(),
              const SizedBox(height: 20),

              // 4. Authentication Results Definitions
              const _AuthenticationResultsSection(),
              const SizedBox(height: 20),

              // 5. Reference Library Statistics
              const _ReferenceLibrarySection(),
              const SizedBox(height: 20),

              // 6. Supported Pharmaceutical References (Dynamic with Fallback)
              _SupportedDrugsSection(drugsAsync: drugsAsync, isWide: isWide),
              const SizedBox(height: 20),

              // 7. Technology Stack
              const _TechnologyStackSection(),
              const SizedBox(height: 20),

              // 8. Scientific Integrity
              const _ScientificIntegritySection(),
              const SizedBox(height: 20),

              // 9. Current Scope
              const _CurrentScopeSection(),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Reusable Section Card Wrapper ──────────────────────────────────────────────

class _AboutSectionCard extends StatelessWidget {
  const _AboutSectionCard({
    required this.title,
    required this.icon,
    required this.child,
    this.subtitle,
  });

  final String title;
  final String? subtitle;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: AppColors.primary, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.2,
                          ),
                    ),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppColors.textSecondary,
                              fontSize: 13,
                            ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}

// ── 1. Hero Section ───────────────────────────────────────────────────────────

class _HeroSectionCard extends StatelessWidget {
  const _HeroSectionCard();

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            cs.surface,
            AppColors.primaryLight.withValues(alpha: 0.3),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.04),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // App Logo / Spectral Symbol
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppColors.primary, AppColors.primaryDark],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: AppColors.primary.withValues(alpha: 0.3),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Icon(
              Icons.biotech_rounded,
              color: Colors.white,
              size: 38,
            ),
          ),
          const SizedBox(height: 18),

          // App Title
          Text(
            'SpectraGuard',
            style: Theme.of(context).textTheme.displayLarge?.copyWith(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 6),

          // Subtitle
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
            ),
            child: Text(
              'AI-Based Raman Spectrometer for Rapid Pharmaceutical Authentication',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: AppColors.primaryDark,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
              textAlign: TextAlign.center,
            ),
          ),
          const SizedBox(height: 16),

          // Description
          Text(
            'SpectraGuard uses Raman spectral analysis and validated pharmaceutical '
            'reference standards to help authenticate pharmaceutical samples through '
            'spectral similarity analysis.',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

// ── 2. What is SpectraGuard? ──────────────────────────────────────────────────

class _WhatIsSpectraGuardCard extends StatelessWidget {
  const _WhatIsSpectraGuardCard();

  @override
  Widget build(BuildContext context) {
    return _AboutSectionCard(
      title: 'What is SpectraGuard?',
      icon: Icons.lightbulb_outline_rounded,
      child: Text(
        'Raman spectroscopy provides a non-destructive molecular fingerprint of a pharmaceutical '
        'sample. SpectraGuard processes the uploaded Raman spectrum and compares it against validated '
        'authentic pharmaceutical Raman reference spectra stored in MySQL. Using cosine similarity '
        'computation against an established threshold, the system produces a reliable, evidence-backed '
        'authentication decision.',
        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              height: 1.5,
              color: AppColors.textPrimary,
            ),
      ),
    );
  }
}

// ── 3. How It Works ───────────────────────────────────────────────────────────

class _HowItWorksSection extends StatelessWidget {
  const _HowItWorksSection();

  @override
  Widget build(BuildContext context) {
    const steps = [
      (
        '1',
        Icons.upload_file_rounded,
        'Upload Raman CSV',
        'Upload a raw Raman spectral CSV file containing wavenumber and intensity measurements.'
      ),
      (
        '2',
        Icons.auto_fix_high_rounded,
        'Spectral Preprocessing',
        'Baseline removal, noise filtering, and intensity normalization prepare the spectrum.'
      ),
      (
        '3',
        Icons.find_in_page_rounded,
        'Reference Library Lookup',
        'Retrieves verified reference spectra for the target drug from MySQL storage.'
      ),
      (
        '4',
        Icons.analytics_rounded,
        'Cosine Similarity Analysis',
        'Calculates mathematical similarity between sample and reference spectra.'
      ),
      (
        '5',
        Icons.fact_check_rounded,
        'Authentication Decision',
        'Compares similarity against the calibrated threshold (0.9860).'
      ),
      (
        '6',
        Icons.task_alt_rounded,
        'Result',
        'Generates an accurate result: Authentic Match, Unknown, Reference Not Available, or Invalid.'
      ),
    ];

    return _AboutSectionCard(
      title: 'How It Works',
      subtitle: '6-Step Raman Spectral Authentication Pipeline',
      icon: Icons.account_tree_rounded,
      child: Column(
        children: steps.asMap().entries.map((entry) {
          final idx = entry.key;
          final step = entry.value;
          final isLast = idx == steps.length - 1;

          return Column(
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Step Badge
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.primary.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Center(
                      child: Icon(step.$2, size: 20, color: AppColors.primary),
                    ),
                  ),
                  const SizedBox(width: 14),

                  // Step Info
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              'Step ${step.$1}: ',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.w700,
                                  ),
                            ),
                            Expanded(
                              child: Text(
                                step.$3,
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(
                                      fontWeight: FontWeight.w600,
                                    ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          step.$4,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: AppColors.textSecondary,
                                height: 1.4,
                              ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (!isLast) ...[
                Padding(
                  padding: const EdgeInsets.only(left: 18, top: 8, bottom: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Container(
                      width: 2,
                      height: 20,
                      color: AppColors.primary.withValues(alpha: 0.25),
                    ),
                  ),
                ),
              ],
            ],
          );
        }).toList(),
      ),
    );
  }
}

// ── 4. Authentication Results Section ─────────────────────────────────────────

class _AuthenticationResultsSection extends StatelessWidget {
  const _AuthenticationResultsSection();

  @override
  Widget build(BuildContext context) {
    const results = [
      (
        'AUTHENTIC REFERENCE MATCH',
        'Strong similarity with an available authentic reference standard.',
        'The uploaded Raman spectrum sufficiently matches an available authentic reference standard in the validated MySQL database.',
        AppColors.success,
        Icons.verified_rounded,
      ),
      (
        'UNKNOWN',
        'The spectrum does not sufficiently match the available authentic reference standard. This result does not by itself prove that the sample is counterfeit.',
        'Reported when similarity is below threshold. SpectraGuard avoids making unverified claims; an UNKNOWN result requires secondary laboratory analysis.',
        AppColors.warning,
        Icons.help_outline_rounded,
      ),
      (
        'REFERENCE NOT AVAILABLE',
        'No active authentic reference standard is available for the selected pharmaceutical.',
        'No active reference standards have been loaded into the MySQL reference database for the chosen drug product.',
        Color(0xFF5B738B),
        Icons.find_in_page_outlined,
      ),
      (
        'INVALID INPUT',
        'The uploaded spectrum could not be processed successfully.',
        'The uploaded file is empty, corrupted, incorrectly formatted, or missing required wavenumber/intensity columns.',
        AppColors.error,
        Icons.error_outline_rounded,
      ),
    ];

    return _AboutSectionCard(
      title: 'Authentication Results',
      subtitle: 'Standardized Classification Outputs & Scientific Definitions',
      icon: Icons.fact_check_outlined,
      child: Column(
        children: results.map((r) {
          final title = r.$1;
          final summary = r.$2;
          final detail = r.$3;
          final color = r.$4;
          final icon = r.$5;

          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: color.withValues(alpha: 0.25)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: color, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: color,
                              fontWeight: FontWeight.w700,
                              fontSize: 14,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '"$summary"',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: AppColors.textPrimary,
                              fontSize: 13,
                              fontStyle: FontStyle.italic,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        detail,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppColors.textSecondary,
                              fontSize: 13,
                              height: 1.35,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

// ── 5. Reference Library Section ─────────────────────────────────────────────

class _ReferenceLibrarySection extends StatelessWidget {
  const _ReferenceLibrarySection();

  @override
  Widget build(BuildContext context) {
    final isWide = context.isWide;

    const statCards = [
      _StatTile(
        count: '11',
        label: 'Pharmaceutical Drugs',
        icon: Icons.medication_rounded,
        color: AppColors.primary,
      ),
      _StatTile(
        count: '158',
        label: 'Authentic Reference Spectra',
        icon: Icons.query_stats_rounded,
        color: AppColors.secondary,
      ),
      _StatTile(
        count: '0.9860',
        label: 'Cosine Similarity Threshold',
        icon: Icons.speed_rounded,
        color: AppColors.primaryDark,
      ),
    ];

    return _AboutSectionCard(
      title: 'Reference Library',
      subtitle: 'Validated Reference Spectra Repository Stored in MySQL',
      icon: Icons.storage_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          isWide
              ? Row(
                  children: statCards
                      .map((c) => Expanded(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 4),
                              child: c,
                            ),
                          ))
                      .toList(),
                )
              : Column(
                  children: statCards
                      .map((c) => Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: c,
                          ))
                      .toList(),
                ),
          const SizedBox(height: 14),
          Text(
            'The reference standards are stored securely in MySQL and can be dynamically expanded '
            'by adding additional validated pharmaceutical Raman reference standards with full provenance metadata. '
            'The system does not claim to support every pharmaceutical drug; only samples matching active '
            'reference standards in the database are authenticated.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.45,
                ),
          ),
        ],
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({
    required this.count,
    required this.label,
    required this.icon,
    required this.color,
  });

  final String count;
  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.02),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  count,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                        color: color,
                        fontSize: 20,
                      ),
                ),
                Text(
                  label,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── 6. Supported Pharmaceutical References Section ───────────────────────────

class _SupportedDrugsSection extends StatelessWidget {
  const _SupportedDrugsSection({
    required this.drugsAsync,
    required this.isWide,
  });

  final AsyncValue<List<String>> drugsAsync;
  final bool isWide;

  @override
  Widget build(BuildContext context) {
    final drugsList = drugsAsync.when(
      data: (data) => data.isNotEmpty ? data : kDefaultReferenceDrugs,
      loading: () => kDefaultReferenceDrugs,
      error: (_, __) => kDefaultReferenceDrugs,
    );

    return _AboutSectionCard(
      title: 'Supported Pharmaceutical References',
      subtitle:
          'Dynamically Loaded Reference Drugs Available for Authentication (${drugsList.length} Active)',
      icon: Icons.medication_liquid_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: drugsList.map((drug) {
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.science_rounded,
                      size: 16,
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      drug,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: AppColors.textPrimary,
                          ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Icon(
                Icons.sync_rounded,
                size: 14,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Reference drugs are dynamically loaded from the backend API (MySQL database).',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                        fontStyle: FontStyle.italic,
                      ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── 7. Technology Stack Section ───────────────────────────────────────────────

class _TechnologyStackSection extends StatelessWidget {
  const _TechnologyStackSection();

  @override
  Widget build(BuildContext context) {
    final isWide = context.isWide;

    const stackItems = [
      (
        'Frontend',
        'Flutter',
        'Cross-platform UI with Riverpod state management & GoRouter',
        Icons.flutter_dash_rounded,
        Color(0xFF02569B)
      ),
      (
        'Backend',
        'Python + FastAPI',
        'Asynchronous REST API processing spectral payloads',
        Icons.terminal_rounded,
        Color(0xFF009688)
      ),
      (
        'Database',
        'MySQL',
        'Relational storage for authentic reference spectra & metadata',
        Icons.storage_rounded,
        Color(0xFF00758F)
      ),
      (
        'Machine Learning',
        'Python + Scikit-learn',
        'Peak alignment, spectral normalization & analytical models',
        Icons.psychology_rounded,
        Color(0xFFF7931E)
      ),
      (
        'Authentication',
        'Cosine Similarity',
        'Normalized vector dot-product similarity (Threshold: 0.9860)',
        Icons.analytics_rounded,
        AppColors.primary
      ),
      (
        'Spectral Processing',
        'Raman Preprocessing',
        'Baseline subtraction, smoothing, and area normalization',
        Icons.graphic_eq_rounded,
        AppColors.secondary
      ),
    ];

    return _AboutSectionCard(
      title: 'Technology Stack',
      subtitle: 'System Architecture & Engineering Technologies',
      icon: Icons.code_rounded,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final crossAxisCount = isWide ? 3 : 1;
          return GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: stackItems.length,
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: crossAxisCount,
              mainAxisExtent: 110,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
            ),
            itemBuilder: (context, idx) {
              final item = stackItems[idx];
              return Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: Theme.of(context).colorScheme.outline,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: item.$5.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(item.$4, color: item.$5, size: 22),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            item.$1,
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium
                                ?.copyWith(
                                  fontSize: 11,
                                  color: AppColors.textSecondary,
                                  fontWeight: FontWeight.w600,
                                ),
                          ),
                          Text(
                            item.$2,
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.textPrimary,
                                ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            item.$3,
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium
                                ?.copyWith(
                                  fontSize: 11,
                                  color: AppColors.textSecondary,
                                  height: 1.2,
                                ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}

// ── 8. Scientific Integrity Section ───────────────────────────────────────────

class _ScientificIntegritySection extends StatelessWidget {
  const _ScientificIntegritySection();

  @override
  Widget build(BuildContext context) {
    return _AboutSectionCard(
      title: 'Scientific Integrity',
      subtitle: 'Rigorous Analytical Methodology & Standardized Reporting',
      icon: Icons.verified_user_rounded,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(
              Icons.gavel_rounded,
              color: AppColors.primary,
              size: 24,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                'SpectraGuard is designed to avoid unsupported pharmaceutical authentication claims. '
                'The system relies on experimentally obtained reference spectra with provenance information. '
                'A failed reference match is reported as UNKNOWN rather than automatically labeling a sample as counterfeit.',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppColors.textPrimary,
                      height: 1.5,
                      fontSize: 14,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 9. Current Scope Section ──────────────────────────────────────────────────

class _CurrentScopeSection extends StatelessWidget {
  const _CurrentScopeSection();

  @override
  Widget build(BuildContext context) {
    return _AboutSectionCard(
      title: 'Current Scope',
      subtitle: 'System Boundaries & Reference Library Capabilities',
      icon: Icons.center_focus_strong_rounded,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.secondary.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.secondary.withValues(alpha: 0.25)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(
              Icons.info_outline_rounded,
              color: AppColors.secondary,
              size: 24,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                'SpectraGuard currently authenticates pharmaceutical samples for drugs represented '
                'by validated active reference standards in its reference library. The system does not claim '
                'universal identification or definitive counterfeit detection for every pharmaceutical product.',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppColors.textPrimary,
                      height: 1.5,
                      fontSize: 14,
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
