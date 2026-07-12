import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/models/test.dart';
import 'package:spectra_app/shared/widgets/classification_badge.dart';

class TestsListScreen extends ConsumerStatefulWidget {
  const TestsListScreen({super.key});

  @override
  ConsumerState<TestsListScreen> createState() => _TestsListScreenState();
}

class _TestsListScreenState extends ConsumerState<TestsListScreen> {
  final _searchCtrl = TextEditingController();
  String? _filterResult;

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _search() {
    ref.read(testsProvider.notifier).refresh(
          drugName: _searchCtrl.text.trim().isEmpty
              ? null
              : _searchCtrl.text.trim(),
          result: _filterResult,
        );
  }

  @override
  Widget build(BuildContext context) {
    final testsAsync = ref.watch(testsProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: const Text('Test History'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'New Test',
            onPressed: () => context.go('/upload'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Search + filter bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchCtrl,
                    decoration: InputDecoration(
                      hintText: 'Search drug name…',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: _searchCtrl.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () {
                                _searchCtrl.clear();
                                _search();
                              },
                            )
                          : null,
                    ),
                    onSubmitted: (_) => _search(),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: 10),
                _FilterDropdown(
                  value: _filterResult,
                  onChanged: (v) {
                    setState(() => _filterResult = v);
                    _search();
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: testsAsync.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (tests) {
                if (tests.isEmpty) {
                  return _Empty();
                }
                return RefreshIndicator(
                  onRefresh: () =>
                      ref.read(testsProvider.notifier).refresh(),
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 4),
                    itemCount: tests.length,
                    separatorBuilder: (_, __) =>
                        const SizedBox(height: 10),
                    itemBuilder: (_, i) =>
                        _TestTile(test: tests[i]),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterDropdown extends StatelessWidget {
  const _FilterDropdown({this.value, required this.onChanged});
  final String? value;
  final ValueChanged<String?> onChanged;

  static const _options = {
    null: 'All',
    'genuine': 'Genuine',
    'potentially_counterfeit': 'Counterfeit',
    'requires_verification': 'Verify',
    'pending': 'Pending',
  };

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String?>(
          value: value,
          items: _options.entries
              .map((e) => DropdownMenuItem(
                    value: e.key,
                    child: Text(e.value, style: const TextStyle(fontSize: 13)),
                  ))
              .toList(),
          onChanged: onChanged,
          icon: const Icon(Icons.filter_list, size: 18),
        ),
      ),
    );
  }
}

class _TestTile extends ConsumerWidget {
  const _TestTile({required this.test});
  final SpectraTest test;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Dismissible(
      key: ValueKey(test.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: AppColors.error.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(14),
        ),
        child: const Icon(Icons.delete_outline, color: AppColors.error),
      ),
      confirmDismiss: (_) async {
        return await showDialog<bool>(
              context: context,
              builder: (_) => AlertDialog(
                title: const Text('Delete Test'),
                content: Text(
                    'Delete test for "${test.drugName}"? This cannot be undone.'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Cancel'),
                  ),
                  TextButton(
                    onPressed: () => Navigator.pop(context, true),
                    child: const Text('Delete',
                        style: TextStyle(color: AppColors.error)),
                  ),
                ],
              ),
            ) ??
            false;
      },
      onDismissed: (_) {
        ref.read(testsProvider.notifier).deleteTest(test.id);
      },
      child: GestureDetector(
        onTap: () => context.go('/tests/${test.id}'),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.09),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.science_outlined,
                    color: AppColors.primary, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(test.drugName,
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Text(
                          DateFormat('MMM d, y  HH:mm')
                              .format(test.testedAt),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        if (test.confidenceScore != null) ...[
                          const Text('  ·  ',
                              style:
                                  TextStyle(color: AppColors.textSecondary)),
                          Text(
                            '${(test.confidenceScore! * 100).toStringAsFixed(1)}%',
                            style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.textSecondary),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              ClassificationBadge(
                result: test.classificationResult,
                compact: true,
              ),
              const SizedBox(width: 4),
              const Icon(Icons.chevron_right,
                  color: AppColors.textSecondary, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.inbox_outlined,
              size: 64, color: AppColors.textSecondary),
          const SizedBox(height: 14),
          Text('No tests found',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 6),
          Text('Upload a spectra CSV to run your first test',
              style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: () => GoRouter.of(context).go('/upload'),
            icon: const Icon(Icons.upload_file),
            label: const Text('Upload Spectra'),
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(200, 48),
            ),
          ),
        ],
      ),
    );
  }
}
