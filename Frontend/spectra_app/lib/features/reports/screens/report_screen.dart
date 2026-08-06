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
        title: const Text('Report'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/tests/$testId'),
        ),
      ),
      body: testAsync.when(
        loading: () => const LoadingOverlay(),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (test) => SingleChildScrollView(
          child: ContentContainer(
            padding: context.pagePadding
                .add(const EdgeInsets.symmetric(vertical: 24)),
            child: FormContainer(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
              const SizedBox(height: 20),
              // PDF icon
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.picture_as_pdf_outlined,
                    size: 50, color: AppColors.error),
              ),
              const SizedBox(height: 20),
              Text(
                'Test Report',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 6),
              Text(
                test.drugName,
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(color: AppColors.textSecondary),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // Status / error messages
              if (reportState.error != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.error.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline,
                          color: AppColors.error, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(reportState.error!,
                            style: const TextStyle(color: AppColors.error)),
                      ),
                    ],
                  ),
                ),

              if (reportState.localPath != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.genuine.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_outline,
                          color: AppColors.genuine, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          kIsWeb
                              ? 'PDF downloaded to your browser downloads folder'
                              : 'Report saved to device',
                          style: const TextStyle(color: AppColors.genuine),
                        ),
                      ),
                    ],
                  ),
                ),

              const SizedBox(height: 32),

              // Generate button
              ElevatedButton.icon(
                onPressed: (reportState.isGenerating || reportState.isDownloading)
                    ? null
                    : () async {
                        await ref
                            .read(reportProvider(testId).notifier)
                            .generate();
                        if (context.mounted &&
                            ref.read(reportProvider(testId)).error == null) {
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
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.auto_awesome_outlined),
                label: Text(reportState.isGenerating
                    ? 'Generating…'
                    : 'Generate PDF Report'),
              ),
              const SizedBox(height: 12),

              // Download button
              OutlinedButton.icon(
                onPressed: (reportState.isGenerating || reportState.isDownloading)
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
                label: Text(reportState.isDownloading
                    ? 'Downloading…'
                    : 'Download & Open PDF'),
              ),
              const SizedBox(height: 12),

              TextButton.icon(
                onPressed: () => context.go('/tests/$testId'),
                icon: const Icon(Icons.arrow_back),
                label: const Text('Back to Test'),
              ),
              const SizedBox(height: 24),
            ],
          ),           // end Column
        ),             // end FormContainer
      ),               // end ContentContainer
    ),                 // end SingleChildScrollView (data callback)
      ),               // end testAsync.when
    );                 // end Scaffold
  }
}

/// Opens a local file on native platforms using open_filex.
/// Never called on web — guarded by kIsWeb at the call site.
Future<void> _openNativeFile(String path) async {
  // open_filex works on Android, iOS, macOS, Windows, Linux
  // ignore: depend_on_referenced_packages
  await OpenFilex.open(path);
}
