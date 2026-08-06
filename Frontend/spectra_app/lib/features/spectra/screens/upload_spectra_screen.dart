import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/spectra/providers/spectra_provider.dart';
import 'package:spectra_app/shared/widgets/app_shell_app_bar.dart';

// Typed aliases to avoid dynamic dispatch issues with AsyncValue.when()
typedef _UploadState = SpectraUploadState;
typedef _SamplesAsync = AsyncValue<List<Map<String, dynamic>>>;

class UploadSpectraScreen extends ConsumerStatefulWidget {
  const UploadSpectraScreen({super.key});

  @override
  ConsumerState<UploadSpectraScreen> createState() =>
      _UploadSpectraScreenState();
}

class _UploadSpectraScreenState extends ConsumerState<UploadSpectraScreen> {
  final _formKey = GlobalKey<FormState>();
  final _drugNameCtrl = TextEditingController();
  final _batchCtrl = TextEditingController();
  final _manufacturerCtrl = TextEditingController();
  final _expiryCtrl = TextEditingController();
  PlatformFile? _pickedFile;
  String? _fileName;

  @override
  void dispose() {
    _drugNameCtrl.dispose();
    _batchCtrl.dispose();
    _manufacturerCtrl.dispose();
    _expiryCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
      withData: true, // ensures bytes are populated on web
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        _pickedFile = result.files.single;
        _fileName = result.files.single.name;
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_pickedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a CSV file'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    final test = await ref.read(spectraUploadProvider.notifier).upload(
          drugName: _drugNameCtrl.text.trim(),
          platformFile: _pickedFile!,
          batchNumber: _batchCtrl.text.trim().isEmpty
              ? null
              : _batchCtrl.text.trim(),
          manufacturer: _manufacturerCtrl.text.trim().isEmpty
              ? null
              : _manufacturerCtrl.text.trim(),
          expiryDate: _expiryCtrl.text.trim().isEmpty
              ? null
              : _expiryCtrl.text.trim(),
        );

    if (!mounted) return;

    final state = ref.read(spectraUploadProvider);
    if (state.error != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(state.error!),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    if (test != null) {
      ref.read(spectraUploadProvider.notifier).reset();
      // Go to classify screen right away
      context.go('/classify/${test.id}');
    }
  }

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(spectraUploadProvider);
    final samplesAsync = ref.watch(sampleDatasetsProvider);
    final padding = context.pagePadding;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppShellAppBar(title: 'Upload Spectra'),
      body: SingleChildScrollView(
        child: ContentContainer(
          padding: padding.add(const EdgeInsets.symmetric(vertical: 20)),
          child: Form(
            key: _formKey,
            child: context.isDesktop
                ? _desktopLayout(context, uploadState, samplesAsync)
                : _singleColumnLayout(context, uploadState, samplesAsync),
          ),
        ),
      ),
    );
  }

  /// Desktop: two-column layout with upload zone on left, form on right
  Widget _desktopLayout(BuildContext context, _UploadState uploadState, _SamplesAsync samplesAsync) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 4,
          child: Column(
            children: [
              _buildFilePicker(),
              const SizedBox(height: 24),
              _buildSampleDatasets(context, uploadState, samplesAsync),
            ],
          ),
        ),
        const SizedBox(width: 32),
        Expanded(
          flex: 5,
          child: _buildDrugInfoForm(context, uploadState),
        ),
      ],
    );
  }

  /// Mobile / tablet: single column (original layout)
  Widget _singleColumnLayout(BuildContext context, _UploadState uploadState, _SamplesAsync samplesAsync) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildFilePicker(),
        const SizedBox(height: 24),
        Text('Drug Information',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 14),
        _buildFields(),
        const SizedBox(height: 28),
        _buildSubmitButton(context, uploadState),
        const SizedBox(height: 32),
        _buildSampleDatasets(context, uploadState, samplesAsync),
      ],
    );
  }

  Widget _buildFilePicker() {
    return GestureDetector(
      onTap: _pickFile,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 32),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: _pickedFile != null ? AppColors.primary : AppColors.border,
            width: _pickedFile != null ? 2 : 1,
            style: BorderStyle.solid,
          ),
        ),
        child: Column(
          children: [
            Icon(
              _pickedFile != null
                  ? Icons.check_circle_outline
                  : Icons.upload_file_outlined,
              size: 48,
              color: _pickedFile != null
                  ? AppColors.primary
                  : AppColors.textSecondary,
            ),
            const SizedBox(height: 10),
            Text(
              _pickedFile != null ? _fileName! : 'Tap to select CSV file',
              style: TextStyle(
                color: _pickedFile != null
                    ? AppColors.primary
                    : AppColors.textSecondary,
                fontWeight: FontWeight.w500,
              ),
            ),
            if (_pickedFile == null)
              const Text(
                'Raman spectral data (wavenumber, intensity)',
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildFields() {
    return Column(
      children: [
        TextFormField(
          controller: _drugNameCtrl,
          decoration: const InputDecoration(
            labelText: 'Drug Name *',
            prefixIcon: Icon(Icons.medication_outlined),
          ),
          validator: (v) =>
              v == null || v.trim().isEmpty ? 'Required' : null,
        ),
        const SizedBox(height: 14),
        TextFormField(
          controller: _batchCtrl,
          decoration: const InputDecoration(
            labelText: 'Batch Number (optional)',
            prefixIcon: Icon(Icons.tag),
          ),
        ),
        const SizedBox(height: 14),
        TextFormField(
          controller: _manufacturerCtrl,
          decoration: const InputDecoration(
            labelText: 'Manufacturer (optional)',
            prefixIcon: Icon(Icons.factory_outlined),
          ),
        ),
        const SizedBox(height: 14),
        TextFormField(
          controller: _expiryCtrl,
          decoration: const InputDecoration(
            labelText: 'Expiry Date (optional)',
            prefixIcon: Icon(Icons.calendar_today_outlined),
            hintText: 'e.g. 2025-12',
          ),
        ),
      ],
    );
  }

  Widget _buildDrugInfoForm(BuildContext context, _UploadState uploadState) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Drug Information',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 14),
          _buildFields(),
          const SizedBox(height: 28),
          _buildSubmitButton(context, uploadState),
        ],
      ),
    );
  }

  Widget _buildSubmitButton(BuildContext context, _UploadState uploadState) {
    return ElevatedButton.icon(
      onPressed: uploadState.isLoading ? null : _submit,
      icon: uploadState.isLoading
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: Colors.white),
            )
          : const Icon(Icons.cloud_upload_outlined),
      label: Text(
          uploadState.isLoading ? 'Uploading…' : 'Upload & Classify'),
    );
  }

  Widget _buildSampleDatasets(BuildContext context, _UploadState uploadState, _SamplesAsync samplesAsync) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Sample Datasets',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        Text(
          'Select a preloaded sample for quick demo',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 12),
        samplesAsync.when(
          loading: () =>
              const Center(child: CircularProgressIndicator()),
          error: (_, __) => const Text('Could not load samples'),
          data: (samples) => Wrap(
            spacing: 8,
            runSpacing: 8,
            children: samples
                .map((s) => ActionChip(
                      avatar:
                          const Icon(Icons.description_outlined, size: 16),
                      label: Text(
                        s['description'] as String,
                        style: const TextStyle(fontSize: 12),
                      ),
                      onPressed: uploadState.isLoading
                          ? null
                          : () async {
                              final filename = s['filename'] as String;
                              final messenger =
                                  ScaffoldMessenger.of(context);
                              final router = GoRouter.of(context);
                              final test = await ref
                                  .read(spectraUploadProvider.notifier)
                                  .uploadSample(filename);

                              if (!mounted) return;

                              final state =
                                  ref.read(spectraUploadProvider);
                              if (state.error != null) {
                                messenger.showSnackBar(
                                  SnackBar(
                                    content: Text(state.error!),
                                    backgroundColor: AppColors.error,
                                  ),
                                );
                                return;
                              }

                              if (test != null) {
                                ref
                                    .read(spectraUploadProvider.notifier)
                                    .reset();
                                router.go('/classify/${test.id}');
                              }
                            },
                    ))
                .toList(),
          ),
        ),
      ],
    );
  }
}
