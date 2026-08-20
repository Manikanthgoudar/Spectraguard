import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/classify/providers/classify_provider.dart';
import 'package:spectra_app/features/spectra/providers/spectra_provider.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/models/raman_analysis_response.dart';
import 'package:spectra_app/shared/models/test.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';
import 'package:fl_chart/fl_chart.dart';

// Typed aliases to prevent dynamic dispatch breaking AsyncValue.when()
typedef _TestAsync = AsyncValue<SpectraTest>;
typedef _SpectraAsync = AsyncValue<Map<String, dynamic>>;

class ClassifyScreen extends ConsumerStatefulWidget {
  const ClassifyScreen({super.key, required this.testId});
  final int testId;

  @override
  ConsumerState<ClassifyScreen> createState() => _ClassifyScreenState();
}

class _ClassifyScreenState extends ConsumerState<ClassifyScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Check if ramanResult is already in store for this testId
      final ramanStore = ref.read(ramanResultsStoreProvider);
      if (ramanStore.containsKey(widget.testId)) {
        ref
            .read(classifyProvider(widget.testId).notifier)
            .setRamanResult(ramanStore[widget.testId]!);
      } else {
        // Fallback: run classification logic
        ref
            .read(classifyProvider(widget.testId).notifier)
            .classify(widget.testId);
      }
    });
  }

  Widget _mobileLayout(
    BuildContext context,
    ClassifyState classifyState,
    _SpectraAsync spectraAsync,
    _TestAsync testAsync,
  ) {
    final ramanResult = classifyState.ramanResult;
    final String drugName = ramanResult?.drugName ??
        (testAsync.valueOrNull?.drugName ?? 'Target Pharmaceutical');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _DrugHeader(drugName: drugName),
        const SizedBox(height: 16),
        if (ramanResult != null)
          _RamanResultCard(result: ramanResult)
        else if (classifyState.result != null)
          _LegacyResultCard(result: classifyState.result!),
        const SizedBox(height: 20),
        Text('Spectral Profile',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 10),
        _buildChart(spectraAsync),
        const SizedBox(height: 20),
        _TopMatchesSection(testId: widget.testId),
        const SizedBox(height: 24),
        ..._buildActions(context),
      ],
    );
  }

  Widget _desktopLayout(
    BuildContext context,
    ClassifyState classifyState,
    _SpectraAsync spectraAsync,
    _TestAsync testAsync,
  ) {
    final ramanResult = classifyState.ramanResult;
    final String drugName = ramanResult?.drugName ??
        (testAsync.valueOrNull?.drugName ?? 'Target Pharmaceutical');

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 3,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _DrugHeader(drugName: drugName),
              const SizedBox(height: 16),
              if (ramanResult != null)
                _RamanResultCard(result: ramanResult)
              else if (classifyState.result != null)
                _LegacyResultCard(result: classifyState.result!),
              const SizedBox(height: 20),
              Text('Spectral Profile',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 10),
              _buildChart(spectraAsync),
            ],
          ),
        ),
        const SizedBox(width: 24),
        Expanded(
          flex: 2,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _TopMatchesSection(testId: widget.testId),
              const SizedBox(height: 24),
              ..._buildActions(context),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildChart(_SpectraAsync spectraAsync) {
    return spectraAsync.when(
      loading: () => const SizedBox(
          height: 220,
          child: Center(child: CircularProgressIndicator())),
      error: (_, __) => const SizedBox(
          height: 220,
          child: Center(child: Text('Could not load spectral data'))),
      data: (data) => _SpectraChart(
        wavenumbers: List<double>.from(
          (data['wavenumber_data'] as List)
              .map((e) => (e as num).toDouble()),
        ),
        intensities: List<double>.from(
          (data['intensity_data'] as List)
              .map((e) => (e as num).toDouble()),
        ),
      ),
    );
  }

  List<Widget> _buildActions(BuildContext context) {
    return [
      SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: () => context.go('/reports/${widget.testId}'),
          icon: const Icon(Icons.picture_as_pdf_outlined),
          label: const Text('Generate PDF Report'),
        ),
      ),
      const SizedBox(height: 10),
      SizedBox(
        width: double.infinity,
        child: OutlinedButton.icon(
          onPressed: () => context.go('/tests/${widget.testId}'),
          icon: const Icon(Icons.arrow_back),
          label: const Text('Back to Test Details'),
        ),
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final classifyState = ref.watch(classifyProvider(widget.testId));
    final spectraAsync = ref.watch(spectraDataProvider(widget.testId));
    final testAsync = ref.watch(testDetailProvider(widget.testId));

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: AppColors.navBackground,
        title: const Text('Raman Spectrum Analysis'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/tests/${widget.testId}'),
        ),
      ),
      body: classifyState.isLoading
          ? const LoadingOverlay(
              title: 'Analyzing Raman Spectrum',
              subtitle:
                  'Processing spectral data and comparing reference standards...',
            )
          : classifyState.error != null
              ? _ErrorView(
                  error: classifyState.error!,
                  onRetry: () => ref
                      .read(classifyProvider(widget.testId).notifier)
                      .classify(widget.testId),
                )
              : SingleChildScrollView(
                  child: ContentContainer(
                    padding: context.pagePadding
                        .add(const EdgeInsets.symmetric(vertical: 20)),
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        if (constraints.maxWidth >= 800) {
                          return _desktopLayout(
                              context, classifyState, spectraAsync, testAsync);
                        } else {
                          return _mobileLayout(
                              context, classifyState, spectraAsync, testAsync);
                        }
                      },
                    ),
                  ),
                ),
    );
  }
}

class _DrugHeader extends StatelessWidget {
  const _DrugHeader({required this.drugName});
  final String drugName;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Icon(Icons.medication_outlined,
              color: AppColors.primary, size: 24),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Target Pharmaceutical',
                  style: Theme.of(context).textTheme.bodyMedium),
              Text(
                drugName,
                style: Theme.of(context).textTheme.titleLarge,
                overflow: TextOverflow.ellipsis,
                maxLines: 2,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

String _formatSimilarityPct(double val) {
  final pct = val * 100.0;
  if (pct == 0.0) return '0.00%';
  if (pct >= 1.0) {
    return '${pct.toStringAsFixed(2)}%';
  } else if (pct >= 0.01) {
    return '${pct.toStringAsFixed(3)}%';
  } else if (pct >= 0.0001) {
    return '${pct.toStringAsFixed(4)}%';
  } else {
    return '${pct.toStringAsFixed(2)}%';
  }
}

class _RamanResultCard extends StatelessWidget {
  const _RamanResultCard({required this.result});
  final RamanAnalysisResponse result;

  Color get _color => switch (result.finalAuthStatus) {
        'AUTHENTIC' => AppColors.genuine,
        'COUNTERFEIT' => AppColors.error,
        'UNKNOWN' => AppColors.requiresVerification,
        _ => AppColors.requiresVerification,
      };

  IconData get _icon => switch (result.finalAuthStatus) {
        'AUTHENTIC' => Icons.verified,
        'COUNTERFEIT' => Icons.cancel,
        'UNKNOWN' => Icons.help_outline,
        _ => Icons.help_outline,
      };

  @override
  Widget build(BuildContext context) {
    final simScore = result.similarityScore;
    final displaySimPct = simScore != null ? _formatSimilarityPct(simScore) : 'N/A';
    final thresholdPct = _formatSimilarityPct(result.authenticationThreshold);
    final finalStatusText = result.finalAuthStatus;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _color, width: 2.0),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _color.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: Icon(_icon, color: _color, size: 32),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AUTHENTICATION RESULT',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.0,
                        color: _color.withOpacity(0.9),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      finalStatusText,
                      style: TextStyle(
                        color: _color,
                        fontSize: 26,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.2,
                      ),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (result.message.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(
              result.message,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    height: 1.4,
                  ),
            ),
          ],
          const SizedBox(height: 16),
          // Similarity Metric Bar
          if (simScore != null) ...[
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Reference Match Similarity',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  displaySimPct,
                  style: TextStyle(
                    color: _color,
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: simScore.clamp(0.0, 1.0),
                backgroundColor: _color.withOpacity(0.15),
                valueColor: AlwaysStoppedAnimation<Color>(_color),
                minHeight: 8,
              ),
            ),
            const SizedBox(height: 16),
          ],
          // Evidence Summary Grid
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface.withOpacity(0.9),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                _EvidenceRow(
                  label: 'Best Reference:',
                  value: result.drugName,
                ),
                const SizedBox(height: 8),
                _EvidenceRow(
                  label: 'Similarity:',
                  value: displaySimPct,
                  valueColor: _color,
                ),
                const SizedBox(height: 8),
                _EvidenceRow(
                  label: 'Threshold:',
                  value: thresholdPct,
                ),
                const SizedBox(height: 8),
                _EvidenceRow(
                  label: 'Reference ID:',
                  value: result.referenceId ?? 'N/A',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EvidenceRow extends StatelessWidget {
  const _EvidenceRow({
    required this.label,
    required this.value,
    this.valueColor,
  });

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(width: 12),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            softWrap: true,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: valueColor ?? AppColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}

class _LegacyResultCard extends StatelessWidget {
  const _LegacyResultCard({required this.result});
  final dynamic result;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.primary.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primary.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            result.message ?? 'Analysis Complete',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ],
      ),
    );
  }
}

class _SpectraChart extends StatelessWidget {
  const _SpectraChart({
    required this.wavenumbers,
    required this.intensities,
  });
  final List<double> wavenumbers;
  final List<double> intensities;

  @override
  Widget build(BuildContext context) {
    if (wavenumbers.isEmpty || intensities.isEmpty) {
      return Container(
        height: 220,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: const Text('No spectral data available'),
      );
    }

    final step = (wavenumbers.length / 300).ceil().clamp(1, 999);
    final spots = <FlSpot>[];
    for (int i = 0; i < wavenumbers.length; i += step) {
      spots.add(FlSpot(wavenumbers[i], intensities[i]));
    }

    final minX = wavenumbers.first;
    final maxX = wavenumbers.last;
    final xRange = (maxX - minX).abs();
    final interval = xRange > 0 ? (xRange / 5.0) : 500.0;

    return Container(
      height: context.isDesktop ? 260 : 220,
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 24, 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          Expanded(
            child: LineChart(
              LineChartData(
                minX: minX,
                maxX: maxX,
                clipData: const FlClipData.all(),
                gridData: const FlGridData(show: false),
                titlesData: FlTitlesData(
                  leftTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 26,
                      interval: interval,
                      getTitlesWidget: (v, meta) {
                        return SideTitleWidget(
                          axisSide: meta.axisSide,
                          fitInside: SideTitleFitInsideData.fromTitleMeta(meta),
                          child: Text(
                            v.toInt().toString(),
                            style: const TextStyle(
                              fontSize: 10,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                borderData: FlBorderData(show: false),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: false,
                    color: AppColors.primary,
                    barWidth: 1.5,
                    dotData: const FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      color: AppColors.primary.withOpacity(0.08),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Wavenumber (cm⁻¹)',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _TopMatchesSection extends ConsumerWidget {
  const _TopMatchesSection({required this.testId});
  final int testId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final classifyState = ref.watch(classifyProvider(testId));
    final ramanTopMatches = classifyState.ramanResult?.topReferenceMatches;

    if (ramanTopMatches != null && ramanTopMatches.isNotEmpty) {
      final matches = List<Map<String, dynamic>>.from(ramanTopMatches);
      matches.sort((a, b) {
        final simA = (a['cosine_similarity'] as num).toDouble();
        final simB = (b['cosine_similarity'] as num).toDouble();
        return simB.compareTo(simA);
      });

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Top Reference Matches',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 10),
          ...matches
              .asMap()
              .entries
              .map((entry) => _MatchTile(
                    rankOverride: entry.key + 1,
                    match: entry.value,
                  )),
        ],
      );
    }

    final matchesAsync = ref.watch(topMatchesProvider(testId));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Top Reference Matches',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 10),
        matchesAsync.when(
          loading: () => const Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ),
          ),
          error: (_, __) => const SizedBox.shrink(),
          data: (data) {
            final rawMatches =
                (data['matches'] as List).cast<Map<String, dynamic>>();
            if (rawMatches.isEmpty) {
              return const Text('No reference matches found.');
            }
            final matches = List<Map<String, dynamic>>.from(rawMatches);
            matches.sort((a, b) {
              final simA = (a['cosine_similarity'] as num).toDouble();
              final simB = (b['cosine_similarity'] as num).toDouble();
              return simB.compareTo(simA);
            });

            return Column(
              children: matches
                  .asMap()
                  .entries
                  .map((entry) => _MatchTile(
                        rankOverride: entry.key + 1,
                        match: entry.value,
                      ))
                  .toList(),
            );
          },
        ),
      ],
    );
  }
}

class _MatchTile extends StatelessWidget {
  const _MatchTile({
    required this.match,
    this.rankOverride,
  });
  final Map<String, dynamic> match;
  final int? rankOverride;

  @override
  Widget build(BuildContext context) {
    final rank = rankOverride ?? (match['rank'] as int? ?? 1);
    final drug = match['drug_name'] as String;
    final similarityVal = (match['cosine_similarity'] as num).toDouble();
    final similarityStr = _formatSimilarityPct(similarityVal);
    final mfr = match['manufacturer'] as String? ?? match['source'] as String?;
    final brand = match['brand'] as String?;
    final refId = match['reference_id'] as String?;

    String subtitle = '';
    if (refId != null && refId.isNotEmpty) {
      subtitle = refId;
      if (brand != null && brand.isNotEmpty) {
        subtitle += ' ($brand)';
      }
    } else if (mfr != null && mfr.isNotEmpty) {
      subtitle = mfr;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: rank == 1
                  ? AppColors.primary
                  : AppColors.primary.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                '$rank',
                style: TextStyle(
                  color: rank == 1 ? Colors.white : AppColors.primary,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
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
                  drug,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (subtitle.isNotEmpty)
                  Text(
                    subtitle,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            similarityStr,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 14,
              color: similarityVal >= 0.9860
                  ? AppColors.genuine
                  : (similarityVal < 0.85
                      ? AppColors.error
                      : AppColors.requiresVerification),
            ),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error, required this.onRetry});
  final String error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline,
                size: 56, color: AppColors.error),
            const SizedBox(height: 14),
            Text('Analysis Failed',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(error,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry Analysis'),
              style: ElevatedButton.styleFrom(minimumSize: const Size(180, 48)),
            ),
          ],
        ),
      ),
    );
  }
}
