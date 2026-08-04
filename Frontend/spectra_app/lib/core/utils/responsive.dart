import 'package:flutter/material.dart';

/// Breakpoints:
///   mobile  : < 600
///   tablet  : 600 – 1024
///   desktop : >= 1024
class Breakpoints {
  static const double mobile = 600;
  static const double tablet = 1024;
  static const double maxContentWidth = 1140.0;
  static const double formMaxWidth = 520.0;
  static const double sidebarWidth = 220.0;
}

enum ScreenSize { mobile, tablet, desktop }

extension ResponsiveContext on BuildContext {
  double get screenWidth => MediaQuery.sizeOf(this).width;
  double get screenHeight => MediaQuery.sizeOf(this).height;

  bool get isMobile => screenWidth < Breakpoints.mobile;
  bool get isTablet =>
      screenWidth >= Breakpoints.mobile && screenWidth < Breakpoints.tablet;
  bool get isDesktop => screenWidth >= Breakpoints.tablet;
  bool get isWide => screenWidth >= Breakpoints.mobile; // tablet or desktop

  ScreenSize get screenSize {
    if (isMobile) return ScreenSize.mobile;
    if (isTablet) return ScreenSize.tablet;
    return ScreenSize.desktop;
  }

  /// Horizontal page padding: tight on mobile, generous on desktop
  EdgeInsets get pagePadding {
    if (isMobile) return const EdgeInsets.symmetric(horizontal: 16);
    if (isTablet) return const EdgeInsets.symmetric(horizontal: 32);
    return const EdgeInsets.symmetric(horizontal: 48);
  }

  /// Number of grid columns for stat cards
  int get statGridColumns {
    if (isMobile) return 2;
    if (isTablet) return 3;
    return 4;
  }

  /// Number of columns for list grids (e.g., reference / test list)
  int get listGridColumns {
    if (isMobile) return 1;
    if (isTablet) return 2;
    return 3;
  }

  /// Responsive font scale factor
  double get fontScale {
    if (isMobile) return 1.0;
    if (isTablet) return 1.05;
    return 1.1;
  }
}

/// Constrains and horizontally centers content for wide screens.
/// Leaves mobile layout completely unchanged.
class ContentContainer extends StatelessWidget {
  const ContentContainer({
    super.key,
    required this.child,
    this.maxWidth = Breakpoints.maxContentWidth,
    this.padding,
  });

  final Widget child;
  final double maxWidth;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    if (context.isMobile) {
      return padding != null ? Padding(padding: padding!, child: child) : child;
    }
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: padding != null
            ? Padding(padding: padding!, child: child)
            : child,
      ),
    );
  }
}

/// Wraps a form to be centered with a max width on wide screens.
class FormContainer extends StatelessWidget {
  const FormContainer({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    if (context.isMobile) return child;
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: Breakpoints.formMaxWidth),
        child: child,
      ),
    );
  }
}

/// Returns a value depending on current screen size.
T responsive<T>(
  BuildContext context, {
  required T mobile,
  T? tablet,
  T? desktop,
}) {
  if (context.isDesktop) return desktop ?? tablet ?? mobile;
  if (context.isTablet) return tablet ?? mobile;
  return mobile;
}
