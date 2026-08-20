import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:open_filex/open_filex.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/reports/providers/reports_provider.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';

class ReportScreen extends ConsumerWidget {
  const ReportScreen({super.key, required this.testId});
  final int testId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final reportState = ref.watch(reportProvider(testId));
    final testAsync = ref.watch(testDetailProvider(testId));

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: AppColors.navBackground,
        title: const Text('Pharmaceutical Authentication Report'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/classify/$testId'),
        ),
      ),
      body: testAsync.when(
        loading: () => const LoadingOverlay(message: 'Loading test details...'),
        error: (e, _) => Center(child: Text('Error loading test: $e')),
        data: (test) => SingleChildScrollView(
          child: ContentContainer(
            padding: context.pagePadding
                .add(const EdgeInsets.symmetric(vertical: 24)),
            child: FormContainer(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const SizedBox(height: 20),
                  // PDF icon banner
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(
                      Icons.picture_as_pdf_outlined,
                      size: 48,
                      color: AppColors.primary,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'Pharmaceutical Authentication Report',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Target Drug: ${test.drugName}',
                    style: Theme.of(context)
                        .textTheme
                        .titleMedium
                        ?.copyWith(color: AppColors.textSecondary),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 28),

                  // Error Banner
                  if (reportState.error != null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.error.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppColors.error.withValues(alpha: 0.3),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.error_outline,
                            color: AppColors.error,
                            size: 20,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              reportState.error!,
                              style: const TextStyle(
                                color: AppColors.error,
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Generation Loading Banner
                  if (reportState.isGenerating) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppColors.primary.withValues(alpha: 0.3),
                        ),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          SizedBox(width: 12),
                          Text(
                            'Generating official PDF report...',
                            style: TextStyle(
                              color: AppColors.primary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Generation Success Banner
                  if (reportState.isGenerated && reportState.localPath == null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.genuine.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppColors.genuine.withValues(alpha: 0.3),
                        ),
                      ),
                      child: const Row(
                        children: [
                          Icon(
                            Icons.check_circle_outline,
                            color: AppColors.genuine,
                            size: 20,
                          ),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              '✓ Report generated successfully. Ready for download.',
                              style: TextStyle(
                                color: AppColors.genuine,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Downloaded File Saved Banner
                  if (reportState.localPath != null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.genuine.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppColors.genuine.withValues(alpha: 0.3),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.check_circle,
                            color: AppColors.genuine,
                            size: 20,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              kIsWeb
                                  ? '✓ PDF report downloaded to your browser downloads folder'
                                  : '✓ Report saved to device',
                              style: const TextStyle(
                                color: AppColors.genuine,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  const SizedBox(height: 16),

                  // Generate Button
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton.icon(
                      onPressed: (reportState.isGenerating ||
                              reportState.isDownloading)
                          ? null
                          : () async {
                              await ref
                                  .read(reportProvider(testId).notifier)
                                  .generate();
                              if (context.mounted &&
                                  ref.read(reportProvider(testId)).error ==
                                      null) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text('Report generated successfully'),
                                    backgroundColor: AppColors.genuine,
                                  ),
                                );
                              }
                            },
                      icon: reportState.isGenerating
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.picture_as_pdf_outlined),
                      label: Text(
                        reportState.isGenerating
                            ? 'Generating Report…'
                            : 'Generate PDF Report',
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Download & Open Button
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: OutlinedButton.icon(
                      onPressed: (reportState.isGenerating ||
                              reportState.isDownloading)
                          ? null
                          : () async {
                              await ref
                                  .read(reportProvider(testId).notifier)
                                  .download();
                              final savedPath =
                                  ref.read(reportProvider(testId)).localPath;
                              if (!kIsWeb && savedPath != null) {
                                await _openNativeFile(savedPath);
                              }
                              final error =
                                  ref.read(reportProvider(testId)).error;
                              if (error != null && context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text(error),
                                    backgroundColor: AppColors.error,
                                  ),
                                );
                              }
                            },
                      icon: reportState.isDownloading
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.download_outlined),
                      label: Text(
                        reportState.isDownloading
                            ? 'Downloading…'
                            : 'Download & Open PDF',
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  TextButton.icon(
                    onPressed: () => context.go('/classify/$testId'),
                    icon: const Icon(Icons.arrow_back),
                    label: const Text('Back to Classification Results'),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Opens a local file on native platforms using open_filex.
/// Never called on web — guarded by kIsWeb at the call site.
Future<void> _openNativeFile(String path) async {
  // ignore: depend_on_referenced_packages
  await OpenFilex.open(path);
}
