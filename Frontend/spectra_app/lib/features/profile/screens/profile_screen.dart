import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/shared/models/user.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: user == null
          ? const Center(child: CircularProgressIndicator())
          : CustomScrollView(
              slivers: [
                // ── Header ──────────────────────────────────────────────
                SliverToBoxAdapter(
                  child: _ProfileHeader(user: user),
                ),

                // ── Content ──────────────────────────────────────────────
                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
                  sliver: SliverList(
                    delegate: SliverChildListDelegate([
                      const SizedBox(height: 24),

                      // Account info section
                      _SectionLabel(label: 'Account Information'),
                      const SizedBox(height: 12),
                      _InfoCard(user: user),
                      const SizedBox(height: 24),

                      // Contact info section
                      if (user.phone != null || user.city != null) ...[
                        _SectionLabel(label: 'Contact Details'),
                        const SizedBox(height: 12),
                        _ContactCard(user: user),
                        const SizedBox(height: 24),
                      ],

                      // Professional info section
                      if (user.organization != null ||
                          user.designation != null ||
                          user.licenseNumber != null) ...[
                        _SectionLabel(label: 'Professional Details'),
                        const SizedBox(height: 12),
                        _ProfessionalCard(user: user),
                        const SizedBox(height: 24),
                      ],

                      // Actions section
                      _SectionLabel(label: 'Account Actions'),
                      const SizedBox(height: 12),
                      _ActionCard(user: user),
                    ]),
                  ),
                ),
              ],
            ),
    );
  }
}

// ── Header with dark gradient background ──────────────────────────────────
class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.user});
  final User user;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.gradientStart, AppColors.gradientEnd],
        ),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(32),
          bottomRight: Radius.circular(32),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top bar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Hello,',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.8),
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.settings_outlined,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 2),
              Text(
                _firstName(user.fullName),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 24),

              // Avatar row
              Row(
                children: [
                  CircleAvatar(
                    radius: 38,
                    backgroundColor: Colors.white.withValues(alpha: 0.2),
                    child: Text(
                      _initials(user.fullName),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 26,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user.fullName,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          user.email,
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.75),
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 8),
                        _RoleBadge(role: user.role),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _firstName(String name) {
    final parts = name.trim().split(' ');
    return parts.isNotEmpty ? parts[0] : name;
  }

  String _initials(String name) {
    final parts = name.trim().split(' ');
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
}

// ── Section label ─────────────────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  const _SectionLabel({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: AppColors.textSecondary,
        letterSpacing: 0.5,
      ),
    );
  }
}

// ── Role badge ────────────────────────────────────────────────────────────
class _RoleBadge extends StatelessWidget {
  const _RoleBadge({required this.role});
  final UserRole role;

  static const _labels = {
    UserRole.public: 'Public',
    UserRole.pharmacist: 'Pharmacist',
    UserRole.investigator: 'Investigator',
    UserRole.admin: 'Administrator',
  };

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.3)),
      ),
      child: Text(
        _labels[role] ?? role.name,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

// ── Reusable detail tile ───────────────────────────────────────────────────
class _DetailTile extends StatelessWidget {
  const _DetailTile({
    required this.icon,
    required this.label,
    required this.value,
    this.isLast = false,
  });

  final IconData icon;
  final String label;
  final String value;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: AppColors.primary, size: 18),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      label,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      value,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (!isLast)
          const Divider(height: 1, indent: 68, endIndent: 16),
      ],
    );
  }
}

// ── Account info card ─────────────────────────────────────────────────────
class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.user});
  final User user;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          _DetailTile(
            icon: Icons.person_outline,
            label: 'Full Name',
            value: user.fullName,
          ),
          _DetailTile(
            icon: Icons.email_outlined,
            label: 'Email Address',
            value: user.email,
          ),
          _DetailTile(
            icon: Icons.badge_outlined,
            label: 'Role',
            value: _roleLabel(user.role),
            isLast: true,
          ),
        ],
      ),
    );
  }

  String _roleLabel(UserRole role) {
    const labels = {
      UserRole.public: 'Public',
      UserRole.pharmacist: 'Pharmacist',
      UserRole.investigator: 'Investigator',
      UserRole.admin: 'Administrator',
    };
    return labels[role] ?? role.name;
  }
}

// ── Contact card ──────────────────────────────────────────────────────────
class _ContactCard extends StatelessWidget {
  const _ContactCard({required this.user});
  final User user;

  @override
  Widget build(BuildContext context) {
    final tiles = <_TileData>[];
    if (user.phone != null) {
      tiles.add(_TileData(Icons.phone_outlined, 'Phone', user.phone!));
    }
    if (user.city != null) {
      tiles.add(_TileData(Icons.location_city_outlined, 'City', user.city!));
    }

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: tiles
            .asMap()
            .entries
            .map((e) => _DetailTile(
                  icon: e.value.icon,
                  label: e.value.label,
                  value: e.value.value,
                  isLast: e.key == tiles.length - 1,
                ))
            .toList(),
      ),
    );
  }
}

// ── Professional card ─────────────────────────────────────────────────────
class _ProfessionalCard extends StatelessWidget {
  const _ProfessionalCard({required this.user});
  final User user;

  @override
  Widget build(BuildContext context) {
    final tiles = <_TileData>[];
    if (user.organization != null) {
      tiles.add(_TileData(
          Icons.business_outlined, 'Organization', user.organization!));
    }
    if (user.designation != null) {
      tiles.add(
          _TileData(Icons.work_outlined, 'Designation', user.designation!));
    }
    if (user.licenseNumber != null) {
      tiles.add(_TileData(Icons.card_membership_outlined, 'License No.',
          user.licenseNumber!));
    }

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: tiles
            .asMap()
            .entries
            .map((e) => _DetailTile(
                  icon: e.value.icon,
                  label: e.value.label,
                  value: e.value.value,
                  isLast: e.key == tiles.length - 1,
                ))
            .toList(),
      ),
    );
  }
}

class _TileData {
  const _TileData(this.icon, this.label, this.value);
  final IconData icon;
  final String label;
  final String value;
}

// ── Actions card (Sign out + Delete account) ───────────────────────────────
class _ActionCard extends ConsumerWidget {
  const _ActionCard({required this.user});
  final User user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          // Sign out
          _ActionTile(
            icon: Icons.logout_rounded,
            label: 'Sign Out',
            color: AppColors.textPrimary,
            onTap: () async {
              await ref.read(authProvider.notifier).logout();
            },
          ),
          const Divider(height: 1, indent: 68, endIndent: 16),
          // Delete account
          _ActionTile(
            icon: Icons.delete_forever_outlined,
            label: 'Delete Account',
            color: AppColors.error,
            onTap: () => _confirmDelete(context, ref),
            isDestructive: true,
          ),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppColors.border),
        ),
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded,
                color: AppColors.error, size: 22),
            SizedBox(width: 8),
            Text(
              'Delete Account',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        content: const Text(
          'This action is permanent and cannot be undone. All your data, tests, and reports will be deleted.',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 14,
            height: 1.5,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text(
              'Cancel',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              // TODO: call delete account API then logout
              await ref.read(authProvider.notifier).logout();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
              minimumSize: Size.zero,
              padding:
                  const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Text('Delete',
                style: TextStyle(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
    this.isDestructive = false,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  final bool isDestructive;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 18),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: color,
                ),
              ),
            ),
            Icon(Icons.chevron_right,
                color: color.withValues(alpha: 0.5), size: 20),
          ],
        ),
      ),
    );
  }
}
