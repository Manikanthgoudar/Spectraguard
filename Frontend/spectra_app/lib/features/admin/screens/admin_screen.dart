import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/features/admin/providers/admin_provider.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';
import 'package:spectra_app/shared/widgets/stat_card.dart';

class AdminScreen extends ConsumerWidget {
  const AdminScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(adminStatsProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.navBackground,
        title: const Text('Admin Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.people_outlined),
            tooltip: 'Manage Users',
            onPressed: () => context.go('/admin/users'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(adminStatsProvider),
          ),
        ],
      ),
      body: statsAsync.when(
        loading: () => const LoadingOverlay(message: 'Loading stats…'),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (stats) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Overview',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 14),

              // Stats grid
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.4,
                children: [
                  StatCard(
                    label: 'Total Tests',
                    value: stats.totalTests.toString(),
                    icon: Icons.science,
                    color: AppColors.primary,
                  ),
                  StatCard(
                    label: 'Total Users',
                    value: stats.totalUsers.toString(),
                    icon: Icons.people,
                    color: AppColors.secondary,
                  ),
                  StatCard(
                    label: 'Genuine',
                    value: stats.genuineCount.toString(),
                    icon: Icons.check_circle,
                    color: AppColors.genuine,
                  ),
                  StatCard(
                    label: 'Counterfeit',
                    value: stats.counterfeitsCount.toString(),
                    icon: Icons.dangerous,
                    color: AppColors.counterfeit,
                  ),
                  StatCard(
                    label: 'Needs Verify',
                    value: stats.requiresVerificationCount.toString(),
                    icon: Icons.warning_amber,
                    color: AppColors.requiresVerification,
                  ),
                  StatCard(
                    label: 'Detection Rate',
                    value:
                        '${stats.counterfeiteDetectionRate.toStringAsFixed(1)}%',
                    icon: Icons.analytics,
                    color: AppColors.warning,
                  ),
                ],
              ),

              const SizedBox(height: 28),
              Text('Users by Role',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 14),
              _RoleBreakdown(usersByRole: stats.usersByRole),

              const SizedBox(height: 28),
              Text('Most Tested Drugs',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 14),
              _DrugRanking(drugs: stats.mostTestedDrugs),

              const SizedBox(height: 24),
              OutlinedButton.icon(
                onPressed: () => context.go('/admin/users'),
                icon: const Icon(Icons.manage_accounts),
                label: const Text('Manage Users'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoleBreakdown extends StatelessWidget {
  const _RoleBreakdown({required this.usersByRole});
  final Map<String, int> usersByRole;

  static const _colors = {
    'admin': AppColors.counterfeit,
    'pharmacist': AppColors.primary,
    'investigator': AppColors.secondary,
    'public': AppColors.pending,
  };

  @override
  Widget build(BuildContext context) {
    final total = usersByRole.values.fold(0, (a, b) => a + b);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: usersByRole.entries.map((e) {
          final pct = total > 0 ? e.value / total : 0.0;
          final color = _colors[e.key] ?? AppColors.primary;
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Column(
              children: [
                Row(
                  children: [
                    Container(
                      width: 10,
                      height: 10,
                      decoration: BoxDecoration(
                        color: color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      e.key[0].toUpperCase() + e.key.substring(1),
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const Spacer(),
                    Text('${e.value}',
                        style: const TextStyle(fontWeight: FontWeight.w600)),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: pct,
                    backgroundColor: color.withValues(alpha: 0.1),
                    valueColor: AlwaysStoppedAnimation<Color>(color),
                    minHeight: 5,
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

class _DrugRanking extends StatelessWidget {
  const _DrugRanking({required this.drugs});
  final List<Map<String, dynamic>> drugs;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: ListView.separated(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: drugs.length,
        separatorBuilder: (_, __) =>
            const Divider(height: 1, indent: 16, endIndent: 16),
        itemBuilder: (_, i) {
          final d = drugs[i];
          final name = d['drug_name'] as String;
          final count = d['count'] as int;
          return ListTile(
            leading: CircleAvatar(
              backgroundColor: AppColors.primary.withValues(alpha: 0.1),
              radius: 18,
              child: Text(
                '${i + 1}',
                style: const TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ),
            title: Text(name, style: Theme.of(context).textTheme.bodyLarge),
            trailing: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '$count tests',
                style: const TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
