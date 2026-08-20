import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/spectra/providers/spectra_provider.dart';
import 'package:spectra_app/shared/widgets/app_shell_app_bar.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';

typedef _UploadState = SpectraUploadState;

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
  String? _selectedDrug;

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
      withData: true,
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        _pickedFile = result.files.single;
        _fileName = result.files.single.name;
      });
    }
  }

  Future<void> _submit() async {
    final uploadState = ref.read(spectraUploadProvider);
    if (uploadState.isLoading) return;

    if (_pickedFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a valid Raman CSV file.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    if (_selectedDrug == null || _selectedDrug!.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a target pharmaceutical drug to verify.'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }

    _drugNameCtrl.text = _selectedDrug!.trim();

    if (!_formKey.currentState!.validate()) return;

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
          duration: const Duration(seconds: 4),
        ),
      );
      return;
    }

    if (test != null) {
      ref.read(spectraUploadProvider.notifier).reset();
      context.go('/classify/${test.id}');
    }
  }

  Widget _buildDrugSelectionCard() {
    final drugsAsync = ref.watch(availableDrugsProvider);

    return drugsAsync.when(
      loading: () => Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: const Center(
          child: Column(
            children: [
              SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2.5),
              ),
              SizedBox(height: 12),
              Text(
                'Loading active reference drugs...',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
      ),
      error: (err, stack) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.error.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.error.withValues(alpha: 0.3)),
        ),
        child: Column(
          children: [
            const Icon(Icons.error_outline, color: AppColors.error, size: 28),
            const SizedBox(height: 8),
            const Text(
              'Reference Drug API Unavailable',
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: AppColors.error,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Failed to fetch active reference standards from server.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () => ref.refresh(availableDrugsProvider),
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
      data: (drugsList) {
        final activeDrugs = List<String>.from(drugsList)..sort();

        return Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
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
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(
                      Icons.medication_outlined,
                      color: AppColors.primary,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'Target Pharmaceutical Drug *',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Text(
                'Select the claimed pharmaceutical drug to verify against the authentic reference library.',
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 14),
              _SearchableDrugDropdown(
                drugs: activeDrugs,
                selectedDrug: _selectedDrug,
                onSelected: (selected) {
                  setState(() {
                    _selectedDrug = selected;
                    _drugNameCtrl.text = selected;
                  });
                },
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildOptionalFields() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.inventory_2_outlined, size: 18, color: AppColors.textSecondary),
              SizedBox(width: 8),
              Text(
                'Sample Metadata (Optional)',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _batchCtrl,
            decoration: const InputDecoration(
              labelText: 'Batch Number',
              prefixIcon: Icon(Icons.tag),
              hintText: 'e.g. BATCH-2025-001',
            ),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _manufacturerCtrl,
            decoration: const InputDecoration(
              labelText: 'Manufacturer',
              prefixIcon: Icon(Icons.factory_outlined),
              hintText: 'e.g. PharmaCorp Ltd.',
            ),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _expiryCtrl,
            decoration: const InputDecoration(
              labelText: 'Expiry Date',
              prefixIcon: Icon(Icons.calendar_today_outlined),
              hintText: 'e.g. 2026-12',
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(spectraUploadProvider);
    final padding = context.pagePadding;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: const AppShellAppBar(title: 'Upload Spectra'),
      body: uploadState.isLoading
          ? const LoadingOverlay(
              title: 'Analyzing Raman Spectrum',
              subtitle:
                  'Processing spectral data and comparing reference standards...',
            )
          : SingleChildScrollView(
              child: ContentContainer(
                padding: padding.add(const EdgeInsets.symmetric(vertical: 20)),
                child: Form(
                  key: _formKey,
                  child: context.isDesktop
                      ? _desktopLayout(context, uploadState)
                      : _singleColumnLayout(context, uploadState),
                ),
              ),
            ),
    );
  }

  Widget _desktopLayout(BuildContext context, _UploadState uploadState) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 4,
          child: _buildFilePicker(uploadState),
        ),
        const SizedBox(width: 24),
        Expanded(
          flex: 5,
          child: Column(
            children: [
              _buildDrugSelectionCard(),
              const SizedBox(height: 16),
              _buildOptionalFields(),
              const SizedBox(height: 24),
              _buildSubmitButton(context, uploadState),
            ],
          ),
        ),
      ],
    );
  }

  Widget _singleColumnLayout(BuildContext context, _UploadState uploadState) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildFilePicker(uploadState),
        const SizedBox(height: 20),
        _buildDrugSelectionCard(),
        const SizedBox(height: 16),
        _buildOptionalFields(),
        const SizedBox(height: 24),
        _buildSubmitButton(context, uploadState),
      ],
    );
  }

  Widget _buildFilePicker(_UploadState uploadState) {
    return GestureDetector(
      onTap: uploadState.isLoading ? null : _pickFile,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.04),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: _pickedFile != null ? AppColors.primary : AppColors.border,
            width: _pickedFile != null ? 2 : 1,
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
            const SizedBox(height: 12),
            Text(
              _pickedFile != null ? _fileName! : 'Tap to select CSV file',
              style: TextStyle(
                fontSize: 15,
                color: _pickedFile != null
                    ? AppColors.primary
                    : AppColors.textPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              _pickedFile != null
                  ? 'File ready for Raman spectral analysis'
                  : 'Raman spectral CSV (3,276 features, 150–3425 cm⁻¹)',
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubmitButton(BuildContext context, _UploadState uploadState) {
    return Column(
      children: [
        if (uploadState.isLoading) ...[
          Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                SizedBox(width: 12),
                Text(
                  'Analyzing Raman spectrum...',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: AppColors.primary,
                  ),
                ),
              ],
            ),
          ),
        ],
        SizedBox(
          width: double.infinity,
          height: 48,
          child: ElevatedButton.icon(
            onPressed: uploadState.isLoading ? null : _submit,
            icon: uploadState.isLoading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.analytics_outlined),
            label: Text(
              uploadState.isLoading
                  ? 'Analyzing Raman Spectrum...'
                  : 'Analyze Raman Spectrum',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
            ),
          ),
        ),
      ],
    );
  }
}

class _SearchableDrugDropdown extends StatefulWidget {
  final List<String> drugs;
  final String? selectedDrug;
  final ValueChanged<String> onSelected;

  const _SearchableDrugDropdown({
    required this.drugs,
    required this.selectedDrug,
    required this.onSelected,
  });

  @override
  State<_SearchableDrugDropdown> createState() => _SearchableDrugDropdownState();
}

class _SearchableDrugDropdownState extends State<_SearchableDrugDropdown> {
  bool _isExpanded = false;
  final TextEditingController _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final query = _searchCtrl.text.trim().toLowerCase();
    final filtered = query.isEmpty
        ? widget.drugs
        : widget.drugs.where((d) => d.toLowerCase().contains(query)).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () {
            setState(() {
              _isExpanded = !_isExpanded;
            });
          },
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: _isExpanded ? AppColors.primary : AppColors.border,
                width: _isExpanded ? 1.5 : 1,
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.medication_outlined, size: 20, color: AppColors.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    widget.selectedDrug ?? 'Select pharmaceutical drug',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: widget.selectedDrug != null
                          ? FontWeight.w600
                          : FontWeight.normal,
                      color: widget.selectedDrug != null
                          ? AppColors.textPrimary
                          : AppColors.textSecondary,
                    ),
                  ),
                ),
                Icon(
                  _isExpanded ? Icons.arrow_drop_up : Icons.arrow_drop_down,
                  color: AppColors.primary,
                ),
              ],
            ),
          ),
        ),
        if (_isExpanded) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.border),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: _searchCtrl,
                  autofocus: true,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Search drugs...',
                    prefixIcon: const Icon(Icons.search, size: 18),
                    suffixIcon: _searchCtrl.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 16),
                            onPressed: () {
                              _searchCtrl.clear();
                              setState(() {});
                            },
                          )
                        : null,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 10,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 220),
                  child: filtered.isEmpty
                      ? const Padding(
                          padding: EdgeInsets.all(16),
                          child: Text(
                            'No matching reference drugs found',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        )
                      : ListView.builder(
                          shrinkWrap: true,
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final drug = filtered[index];
                            final isSelected = widget.selectedDrug == drug;
                            return InkWell(
                              onTap: () {
                                widget.onSelected(drug);
                                setState(() {
                                  _isExpanded = false;
                                  _searchCtrl.clear();
                                });
                              },
                              borderRadius: BorderRadius.circular(6),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 10,
                                ),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? AppColors.primary.withValues(alpha: 0.1)
                                      : Colors.transparent,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Row(
                                  children: [
                                    Icon(
                                      Icons.medication_outlined,
                                      size: 18,
                                      color: isSelected
                                          ? AppColors.primary
                                          : AppColors.textSecondary,
                                    ),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Text(
                                        drug,
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: isSelected
                                              ? FontWeight.w600
                                              : FontWeight.normal,
                                          color: isSelected
                                              ? AppColors.primary
                                              : AppColors.textPrimary,
                                        ),
                                      ),
                                    ),
                                    if (isSelected)
                                      const Icon(
                                        Icons.check_circle,
                                        size: 18,
                                        color: AppColors.primary,
                                      ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
