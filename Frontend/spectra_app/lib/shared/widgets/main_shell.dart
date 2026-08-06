import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/shared/models/user.dart';

// ─── Nav item model ───────────────────────────────────────────────────────────

class _NavItem {
  _NavItem({required this.icon, required this.label, required this.path});
  final IconData icon;
  final String label;
  final String path;
}

// ─── Main shell ───────────────────────────────────────────────────────────────

class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.child});
  final Widget child;

  /// Maps the current URL to the logical tab index.
  int _locationToIndex(String location, bool isAdmin) {
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/tests') || location.startsWith('/upload')) {
      return 1;
    }
    if (location.startsWith('/chat')) return isAdmin ? 3 : 2;
    if (location.startsWith('/nearby')) return isAdmin ? 4 : 3;
    if (location.startsWith('/settings')) return isAdmin ? 5 : 4;
    if (location.startsWith('/about')) return isAdmin ? 6 : 5;
    if (location.startsWith('/admin')) return isAdmin ? 2 : 0;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final isAdmin = user?.role == UserRole.admin;
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _locationToIndex(location, isAdmin);

    // Sidebar / nav items — Reference and My Profile removed (UI-only).
    // Settings added as a proper nav destination.
    final tabs = [
      _NavItem(
        icon: Icons.grid_view_rounded,
        label: 'Home',
        path: '/dashboard',
      ),
      _NavItem(
        icon: Icons.science_outlined,
        label: 'Tests',
        path: '/tests',
      ),
      if (isAdmin)
        _NavItem(
          icon: Icons.admin_panel_settings_outlined,
          label: 'Admin',
          path: '/admin',
        ),
      _NavItem(
        icon: Icons.smart_toy_outlined,
        label: 'AI Chat',
        path: '/chat',
      ),
      _NavItem(
        icon: Icons.location_on_outlined,
        label: 'Nearby',
        path: '/nearby',
      ),
      _NavItem(
        icon: Icons.settings_outlined,
        label: 'Settings',
        path: '/settings',
      ),
      _NavItem(
        icon: Icons.info_outline,
        label: 'About',
        path: '/about',
      ),
    ];

    // On mobile show up to 5 items in the bottom nav (drop Settings & About
    // from the bar; they remain accessible via the sidebar drawer).
    final mobileTabs = tabs.length > 5 ? tabs.sublist(0, 5) : tabs;

    if (context.isWide) {
      // ── Desktop / Tablet: permanent sidebar ───────────────────────────
      return _WideLayout(
        tabs: tabs,
        currentIndex: currentIndex,
        user: user,
        child: child,
      );
    }

    // ── Mobile: bottom nav + hamburger drawer ────────────────────────────
    return _MobileLayout(
      tabs: tabs,
      mobileTabs: mobileTabs,
      currentIndex: currentIndex,
      user: user,
      child: child,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Mobile layout — bottom nav with a side drawer for all items
// ─────────────────────────────────────────────────────────────────────────────

class _MobileLayout extends ConsumerWidget {
  const _MobileLayout({
    required this.child,
    required this.tabs,
    required this.mobileTabs,
    required this.currentIndex,
    required this.user,
  });

  final Widget child;
  final List<_NavItem> tabs;
  final List<_NavItem> mobileTabs;
  final int currentIndex;
  final User? user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      // The drawer gives access to all nav items on mobile
      drawer: _SideDrawer(tabs: tabs, currentIndex: currentIndex, user: user),
      body: child,
      bottomNavigationBar: _BottomNav(
        tabs: mobileTabs,
        currentIndex: currentIndex,
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Wide layout: permanent left sidebar
// ─────────────────────────────────────────────────────────────────────────────

class _WideLayout extends ConsumerWidget {
  const _WideLayout({
    required this.child,
    required this.tabs,
    required this.currentIndex,
    required this.user,
  });

  final Widget child;
  final List<_NavItem> tabs;
  final int currentIndex;
  final User? user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Row(
        children: [
          // ── Permanent sidebar ────────────────────────────────────────
          Container(
            width: Breakpoints.sidebarWidth,
            decoration: BoxDecoration(
              color: cs.surface,
              border: Border(right: BorderSide(color: cs.outline)),
            ),
            child: SafeArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Brand
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                    child: Row(
                      children: [
                        Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(Icons.biotech,
                              color: Colors.white, size: 20),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'SpectraGuard',
                            style: TextStyle(
                              color: cs.onSurface,
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Divider(height: 1),
                  ),
                  const SizedBox(height: 8),

                  // Nav items
                  Expanded(
                    child: ListView.builder(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      itemCount: tabs.length,
                      itemBuilder: (ctx, i) {
                        final tab = tabs[i];
                        final selected = currentIndex == i;
                        return _SidebarNavItem(
                          tab: tab,
                          selected: selected,
                          onTap: () => ctx.go(tab.path),
                        );
                      },
                    ),
                  ),

                  const SizedBox(height: 8),
                ],
              ),
            ),
          ),

          // ── Main content area ────────────────────────────────────────
          Expanded(child: child),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Sidebar profile tile (bottom of sidebar) — shows photo + popup menu
// ─────────────────────────────────────────────────────────────────────────────



// ─────────────────────────────────────────────────────────────────────────────
// Mobile side drawer
// ─────────────────────────────────────────────────────────────────────────────

class _SideDrawer extends ConsumerWidget {
  const _SideDrawer({
    required this.tabs,
    required this.currentIndex,
    required this.user,
  });
  final List<_NavItem> tabs;
  final int currentIndex;
  final User? user;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    return Drawer(
      backgroundColor: cs.surface,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Brand header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.biotech,
                        color: Colors.white, size: 20),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    'SpectraGuard',
                    style: TextStyle(
                      color: cs.onSurface,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Divider(height: 1),
            ),
            const SizedBox(height: 8),

            // Nav items
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 4),
                itemCount: tabs.length,
                itemBuilder: (ctx, i) {
                  final tab = tabs[i];
                  final selected = currentIndex == i;
                  return _SidebarNavItem(
                    tab: tab,
                    selected: selected,
                    onTap: () {
                      Navigator.of(context).pop(); // close drawer
                      ctx.go(tab.path);
                    },
                  );
                },
              ),
            ),

            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Drawer profile tile (mobile drawer)
// ─────────────────────────────────────────────────────────────────────────────



// ─────────────────────────────────────────────────────────────────────────────
// Sidebar nav item
// ─────────────────────────────────────────────────────────────────────────────

class _SidebarNavItem extends StatelessWidget {
  const _SidebarNavItem({
    required this.tab,
    required this.selected,
    required this.onTap,
  });
  final _NavItem tab;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final unselected = cs.onSurfaceVariant;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            decoration: BoxDecoration(
              color: selected
                  ? AppColors.primary.withOpacity(0.10)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(10),
              border: selected
                  ? Border.all(
                      color: AppColors.primary.withOpacity(0.25))
                  : null,
            ),
            child: Row(
              children: [
                Icon(
                  tab.icon,
                  size: 20,
                  color: selected
                      ? AppColors.primary
                      : unselected,
                ),
                const SizedBox(width: 12),
                Text(
                  tab.label,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight:
                        selected ? FontWeight.w600 : FontWeight.w400,
                    color: selected
                        ? AppColors.primary
                        : unselected,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Mobile bottom nav
// ─────────────────────────────────────────────────────────────────────────────

class _BottomNav extends StatelessWidget {
  const _BottomNav({required this.tabs, required this.currentIndex});
  final List<_NavItem> tabs;
  final int currentIndex;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      decoration: BoxDecoration(
        color: cs.surface,
        border: Border(top: BorderSide(color: cs.outline)),
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
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 5),
                        decoration: BoxDecoration(
                          color: selected
                              ? AppColors.primary.withOpacity(0.12)
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(
                          tab.icon,
                          size: 22,
                          color: selected
                              ? AppColors.primary
                              : cs.onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 2),
                        child: Text(
                          tab.label,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: selected
                                ? FontWeight.w600
                                : FontWeight.w400,
                            color: selected
                                ? AppColors.primary
                                : cs.onSurfaceVariant,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.center,
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
    );
  }
}
