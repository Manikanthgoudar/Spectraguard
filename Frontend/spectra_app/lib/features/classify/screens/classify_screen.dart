import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/features/classify/providers/classify_provider.dart';
import 'package:spectra_app/features/spectra/providers/spectra_provider.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/models/classification.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';
import 'package:fl_chart/fl_chart.dart';

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
    // Auto-run classification on open
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(classifyProvider(widget.testId).notifier).classify(widget.testId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final classifyState = ref.watch(classifyProvider(widget.testId));
    final spectraAsync = ref.watch(spectraDataProvider(widget.testId));
    final testAsync = ref.watch(testDetailProvider(widget.testId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.navBackground,
        title: const Text('AI Classification'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/tests/${widget.testId}'),
        ),
      ),
      body: classifyState.isLoading
          ? const LoadingOverlay(message: 'Running AI classification…')
          : classifyState.error != null
              ? _ErrorView(
                  error: classifyState.error!,
                  onRetry: () => ref
                      .read(classifyProvider(widget.testId).notifier)
                      .classify(widget.testId),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Drug name from test
                      testAsync.when(
                        loading: () => const SizedBox.shrink(),
                        error: (_, __) => const SizedBox.shrink(),
                        data: (t) => _DrugHeader(drugName: t.drugName),
                      ),
                      const SizedBox(height: 16),

                      // Result card
                      if (classifyState.result != null)
                        _ResultCard(result: classifyState.result!),
                      const SizedBox(height: 20),

                      // Spectral chart
                      Text('Spectral Profile',
                          style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 10),
                      spectraAsync.when(
                        loading: () => const SizedBox(
                          height: 200,
                          child: Center(
                              child: CircularProgressIndicator()),
                        ),
                        error: (_, __) => const SizedBox(
                          height: 200,
                          child: Center(
                              child: Text('Could not load spectral data')),
                        ),
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
                      ),
                      const SizedBox(height: 20),

                      // Top matches
                      if (classifyState.result != null)
                        _TopMatchesSection(testId: widget.testId),

                      const SizedBox(height: 24),
                      // Actions
                      if (classifyState.result != null) ...[
                        ElevatedButton.icon(
                          onPressed: () =>
                              context.go('/reports/${widget.testId}'),
                          icon: const Icon(Icons.picture_as_pdf_outlined),
                          label: const Text('Generate Report'),
                        ),
                        const SizedBox(height: 10),
                        OutlinedButton.icon(
                          onPressed: () =>
                              context.go('/tests/${widget.testId}'),
                          icon: const Icon(Icons.arrow_back),
                          label: const Text('Back to Test'),
                        ),
                      ],
                    ],
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
            color: AppColors.primary.withValues(alpha: 0.1),
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
              Text('Analysing', style: Theme.of(context).textTheme.bodyMedium),
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

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});
  final ClassificationResponse result;

  Color get _color => switch (result.result) {
        ClassificationResultEnum.genuine => AppColors.genuine,
        ClassificationResultEnum.potentiallyCounterfeit => AppColors.counterfeit,
        ClassificationResultEnum.requiresVerification =>
          AppColors.requiresVerification,
        ClassificationResultEnum.pending => AppColors.pending,
      };

  IconData get _icon => switch (result.result) {
        ClassificationResultEnum.genuine => Icons.check_circle_outline,
        ClassificationResultEnum.potentiallyCounterfeit =>
          Icons.dangerous_outlined,
        ClassificationResultEnum.requiresVerification =>
          Icons.warning_amber_outlined,
        ClassificationResultEnum.pending => Icons.hourglass_empty,
      };

  String get _label => switch (result.result) {
        ClassificationResultEnum.genuine => 'GENUINE',
        ClassificationResultEnum.potentiallyCounterfeit => 'COUNTERFEIT',
        ClassificationResultEnum.requiresVerification =>
          'REQUIRES VERIFICATION',
        ClassificationResultEnum.pending => 'PENDING',
      };

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _color.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(_icon, color: _color, size: 28),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _label,
                  style: TextStyle(
                    color: _color,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 2,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(result.message,
              style: Theme.of(context).textTheme.bodyLarge),
          const SizedBox(height: 14),
          // Confidence bar
          Row(
            children: [
              Text('Confidence',
                  style: Theme.of(context).textTheme.bodyMedium),
              const Spacer(),
              Text(
                '${(result.confidenceScore * 100).toStringAsFixed(1)}%',
                style: TextStyle(
                  color: _color,
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: result.confidenceScore,
              backgroundColor: _color.withValues(alpha: 0.15),
              valueColor: AlwaysStoppedAnimation<Color>(_color),
              minHeight: 8,
            ),
          ),
          if (result.matchedDrugName != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.link, size: 16, color: AppColors.textSecondary),
                const SizedBox(width: 6),
                Text('Matched: ',
                    style: Theme.of(context).textTheme.bodyMedium),
                Text(
                  result.matchedDrugName!,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ],
          if (result.cosineSimilarity != null) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: _Metric('Cosine Similarity',
                      result.cosineSimilarity!.toStringAsFixed(4)),
                ),
                if (result.euclideanDistance != null) ...[
                  const SizedBox(width: 12),
                  Expanded(
                    child: _Metric('Euclidean Distance',
                        result.euclideanDistance!.toStringAsFixed(4)),
                  ),
                ],
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(
                fontSize: 11, color: AppColors.textSecondary)),
        Text(value,
            style: const TextStyle(
                fontSize: 13, fontWeight: FontWeight.w600)),
      ],
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
    // Downsample to max 300 points for performance
    final step = (wavenumbers.length / 300).ceil().clamp(1, 999);
    final spots = <FlSpot>[];
    for (int i = 0; i < wavenumbers.length; i += step) {
      spots.add(FlSpot(wavenumbers[i], intensities[i]));
    }

    return Container(
      height: 220,
      padding: const EdgeInsets.fromLTRB(8, 12, 16, 8),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: LineChart(
        LineChartData(
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
              axisNameWidget: const Text('Wavenumber (cm⁻¹)',
                  style: TextStyle(
                      fontSize: 11, color: AppColors.textSecondary)),
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 28,
                getTitlesWidget: (v, _) => Text(
                  v.toInt().toString(),
                  style: const TextStyle(
                      fontSize: 9, color: AppColors.textSecondary),
                ),
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
                color: AppColors.primary.withValues(alpha: 0.08),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TopMatchesSection extends ConsumerWidget {
  const _TopMatchesSection({required this.testId});
  final int testId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final matchesAsync = ref.watch(topMatchesProvider(testId));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Top Reference Matches',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 10),
        matchesAsync.when(
          loading: () =>
              const Center(child: CircularProgressIndicator()),
          error: (_, __) => const SizedBox.shrink(),
          data: (data) {
            final matches =
                (data['matches'] as List).cast<Map<String, dynamic>>();
            return Column(
              children: matches
                  .map((m) => _MatchTile(match: m))
                  .toList(),
            );
          },
        ),
      ],
    );
  }
}

class _MatchTile extends StatelessWidget {
  const _MatchTile({required this.match});
  final Map<String, dynamic> match;

  @override
  Widget build(BuildContext context) {
    final rank = match['rank'] as int;
    final drug = match['drug_name'] as String;
    final similarity =
        ((match['cosine_similarity'] as num).toDouble() * 100)
            .toStringAsFixed(1);
    final mfr = match['manufacturer'] as String?;

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
                  : AppColors.primary.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                '$rank',
                style: TextStyle(
                  color: rank == 1
                      ? Colors.white
                      : AppColors.primary,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(drug,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontSize: 14,
                        )),
                if (mfr != null)
                  Text(mfr,
                      style: Theme.of(context).textTheme.bodyMedium),
              ],
            ),
          ),
          Text(
            '$similarity%',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 15,
              color: double.parse(similarity) >= 90
                  ? AppColors.genuine
                  : double.parse(similarity) >= 70
                      ? AppColors.requiresVerification
                      : AppColors.counterfeit,
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
            Text('Classification Failed',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(error,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(minimumSize: const Size(180, 48)),
            ),
          ],
        ),
      ),
    );
  }
}
