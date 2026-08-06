import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/admin/providers/admin_provider.dart';
import 'package:spectra_app/shared/models/admin.dart';
import 'package:spectra_app/shared/widgets/loading_overlay.dart';

const _roles = ['public', 'pharmacist', 'investigator', 'admin'];

class AdminUsersScreen extends ConsumerStatefulWidget {
  const AdminUsersScreen({super.key});

  @override
  ConsumerState<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends ConsumerState<AdminUsersScreen> {
  String? _filterRole;
  int? _filterActive;

  @override
  Widget build(BuildContext context) {
    final usersAsync = ref.watch(adminUsersProvider);
    final padding = context.pagePadding;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: AppColors.navBackground,
        title: const Text('Manage Users'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(adminUsersProvider.notifier).filter(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter bar
          ContentContainer(
            padding: padding.add(const EdgeInsets.fromLTRB(0, 12, 0, 0)),
            child: Row(
              children: [
                Expanded(
                  child: _FilterChip(
                    label: 'Role',
                    value: _filterRole ?? 'All',
                    options: ['All', ..._roles],
                    onSelected: (v) {
                      setState(() => _filterRole = v == 'All' ? null : v);
                      ref.read(adminUsersProvider.notifier).filter(
                            role: _filterRole,
                            isActive: _filterActive,
                          );
                    },
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _FilterChip(
                    label: 'Status',
                    value: _filterActive == null
                        ? 'All'
                        : _filterActive == 1
                            ? 'Active'
                            : 'Inactive',
                    options: ['All', 'Active', 'Inactive'],
                    onSelected: (v) {
                      setState(() {
                        _filterActive = v == 'All'
                            ? null
                            : v == 'Active'
                                ? 1
                                : 0;
                      });
                      ref.read(adminUsersProvider.notifier).filter(
                            role: _filterRole,
                            isActive: _filterActive,
                          );
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: usersAsync.when(
              loading: () => const LoadingOverlay(message: 'Loading users…'),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (users) {
                if (users.isEmpty) {
                  return const Center(child: Text('No users found'));
                }
                return context.isWide
                    ? ContentContainer(
                        child: GridView.builder(
                          padding: padding.add(
                              const EdgeInsets.symmetric(vertical: 4)),
                          gridDelegate:
                              SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: context.isDesktop ? 2 : 1,
                            crossAxisSpacing: 12,
                            mainAxisSpacing: 10,
                            childAspectRatio:
                                context.isDesktop ? 3.6 : 4,
                          ),
                          itemCount: users.length,
                          itemBuilder: (_, i) => _UserTile(user: users[i]),
                        ),
                      )
                    : ListView.separated(
                        padding: padding.add(
                            const EdgeInsets.symmetric(vertical: 4)),
                        itemCount: users.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 10),
                        itemBuilder: (_, i) => _UserTile(user: users[i]),
                      );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.value,
    required this.options,
    required this.onSelected,
  });
  final String label;
  final String value;
  final List<String> options;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () async {
        final picked = await showDialog<String>(
          context: context,
          builder: (_) => SimpleDialog(
            title: Text('Filter by $label'),
            children: options
                .map((o) => SimpleDialogOption(
                      onPressed: () => Navigator.pop(context, o),
                      child: Text(o),
                    ))
                .toList(),
          ),
        );
        if (picked != null) onSelected(picked);
      },
      child: Container(
        height: 44,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('$label: ', style: Theme.of(context).textTheme.bodyMedium),
            Text(value,
                style: const TextStyle(
                    fontWeight: FontWeight.w600, fontSize: 13)),
            const Icon(Icons.arrow_drop_down, size: 18),
          ],
        ),
      ),
    );
  }
}

class _UserTile extends ConsumerWidget {
  const _UserTile({required this.user});
  final AdminUser user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isActive = user.isActive == 1;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: AppColors.primary.withOpacity(0.1),
            child: Text(
              user.fullName.isNotEmpty
                  ? user.fullName[0].toUpperCase()
                  : '?',
              style: const TextStyle(
                  color: AppColors.primary, fontWeight: FontWeight.w700),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(user.fullName,
                    style: Theme.of(context).textTheme.titleMedium),
                Text(user.email,
                    style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 4),
                Row(
                  children: [
                    _Badge(
                      label: user.role[0].toUpperCase() +
                          user.role.substring(1),
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 6),
                    _Badge(
                      label: isActive ? 'Active' : 'Inactive',
                      color: isActive ? AppColors.genuine : AppColors.pending,
                    ),
                  ],
                ),
              ],
            ),
          ),
          // Toggle active/inactive
          Switch.adaptive(
            value: isActive,
            activeColor: AppColors.genuine,
            onChanged: (v) {
              ref.read(adminUsersProvider.notifier).updateUser(
                    user.id,
                    isActive: v ? 1 : 0,
                  );
            },
          ),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label, required this.color});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
            color: color, fontSize: 11, fontWeight: FontWeight.w600),
      ),
    );
  }
}
