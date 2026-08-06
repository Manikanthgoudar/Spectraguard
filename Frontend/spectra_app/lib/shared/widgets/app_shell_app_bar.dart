import 'package:flutter/material.dart';
import 'package:spectra_app/core/utils/responsive.dart';

/// A standard AppBar that automatically adds a hamburger menu icon on mobile
/// so the user can open the [MainShell] drawer. On tablet/desktop the sidebar
/// is always visible so no hamburger is shown.
///
/// Drop-in replacement for [AppBar] on shell-route screens.
class AppShellAppBar extends StatelessWidget implements PreferredSizeWidget {
  const AppShellAppBar({
    super.key,
    required this.title,
    this.actions,
    this.bottom,
  });

  final String title;
  final List<Widget>? actions;
  final PreferredSizeWidget? bottom;

  @override
  Size get preferredSize => Size.fromHeight(
        kToolbarHeight + (bottom?.preferredSize.height ?? 0),
      );

  @override
  Widget build(BuildContext context) {
    // On mobile show a hamburger; on wide layouts the sidebar handles nav.
    final isMobile = context.isMobile;

    return AppBar(
      backgroundColor: Theme.of(context).colorScheme.surface,
      title: Text(title),
      leading: isMobile
          ? IconButton(
              icon: const Icon(Icons.menu_rounded),
              tooltip: 'Menu',
              onPressed: () => Scaffold.of(context).openDrawer(),
            )
          : null,
      // Preserve automatic back-button when pushed onto the stack
      automaticallyImplyLeading: !isMobile,
      actions: actions,
      bottom: bottom,
    );
  }
}
