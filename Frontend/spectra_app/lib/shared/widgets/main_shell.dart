import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/shared/models/user.dart';

class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.child});
  final Widget child;

  int _locationToIndex(String location, bool isAdmin) {
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/tests') || location.startsWith('/upload')) return 1;
    if (location.startsWith('/reference')) return 2;
    if (location.startsWith('/admin')) return isAdmin ? 3 : 0;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final isAdmin = user?.role == UserRole.admin;
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _locationToIndex(location, isAdmin);

    final tabs = [
      _NavItem(icon: Icons.grid_view_rounded, label: 'Home', path: '/dashboard'),
      _NavItem(icon: Icons.science_outlined, label: 'Tests', path: '/tests'),
      _NavItem(icon: Icons.library_books_outlined, label: 'Reference', path: '/reference'),
      if (isAdmin)
        _NavItem(icon: Icons.admin_panel_settings_outlined, label: 'Admin', path: '/admin'),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: const Border(
            top: BorderSide(color: AppColors.border, width: 1),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.3),
              blurRadius: 20,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: SafeArea(
          child: SizedBox(
            height: 64,
            child: Row(
              children: tabs.asMap().entries.map((entry) {
                final i = entry.key;
                final tab = entry.value;
                final selected = currentIndex == i;
                return Expanded(
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => context.go(tab.path),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 6),
                          decoration: BoxDecoration(
                            color: selected
                                ? AppColors.primary.withValues(alpha: 0.15)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(
                            tab.icon,
                            size: 22,
                            color: selected
                                ? AppColors.primary
                                : AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          tab.label,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: selected
                                ? FontWeight.w600
                                : FontWeight.w400,
                            color: selected
                                ? AppColors.primary
                                : AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  _NavItem({required this.icon, required this.label, required this.path});
  final IconData icon;
  final String label;
  final String path;
}
