import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import 'package:spectra_app/features/tests/providers/tests_provider.dart';
import 'package:spectra_app/shared/models/test.dart';
import 'package:spectra_app/shared/widgets/classification_badge.dart';
import 'package:spectra_app/shared/widgets/profile_avatar.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnim = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.04),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut));
    _animCtrl.forward();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final testsAsync = ref.watch(testsProvider);
    final isWide = context.isWide;
    final padding = context.pagePadding;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: RefreshIndicator(
        color: AppColors.primary,
        backgroundColor: Theme.of(context).colorScheme.surface,
        onRefresh: () => ref.read(testsProvider.notifier).refresh(),
        child: FadeTransition(
          opacity: _fadeAnim,
          child: SlideTransition(
            position: _slideAnim,
            child: CustomScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              slivers: [
                // ── Header ──────────────────────────────────────────────
                SliverToBoxAdapter(
                  child: isWide
                      ? _WideHeader()
                      : _MobileHeader(),
                ),

                // ── Stats ────────────────────────────────────────────────
                SliverToBoxAdapter(
                  child: testsAsync.when(
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                    data: (tests) =>
                        _StatsSection(tests: tests, padding: padding),
                  ),
                ),

                // ── Quick Summary card ───────────────────────────────────
                SliverToBoxAdapter(
                  child: testsAsync.when(
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                    data: (tests) =>
                        _QuickSummaryCard(tests: tests, padding: padding),
                  ),
                ),

                // ── Quick Actions ────────────────────────────────────────
                SliverToBoxAdapter(
                  child: _QuickActionsSection(padding: padding),
                ),

                // ── Recent Tests header ──────────────────────────────────
                SliverToBoxAdapter(
                  child: ContentContainer(
                    padding: padding
                        .add(const EdgeInsets.fromLTRB(0, 28, 0, 12)),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Recent Tests',
                          style: TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        TextButton.icon(
                          onPressed: () => context.go('/tests'),
                          icon: const Icon(Icons.arrow_forward_rounded,
                              size: 16),
                          label: const Text('View all'),
                          style: TextButton.styleFrom(
                            foregroundColor: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // ── Recent Tests list ────────────────────────────────────
                testsAsync.when(
                  loading: () => const SliverToBoxAdapter(
                    child: Center(
                      child: Padding(
                        padding: EdgeInsets.all(32),
                        child: CircularProgressIndicator(
                            color: AppColors.primary),
                      ),
                    ),
                  ),
                  error: (e, _) => SliverToBoxAdapter(
                    child: Center(child: Text('Error: $e')),
                  ),
                  data: (tests) {
                    final recent = tests.take(5).toList();
                    if (recent.isEmpty) {
                      return const SliverToBoxAdapter(
                          child: _EmptyState());
                    }
                    return SliverPadding(
                      padding:
                          padding.add(const EdgeInsets.only(bottom: 32)),
                      sliver: isWide
                          ? SliverGrid(
                              gridDelegate:
                                  SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount:
                                    context.isDesktop ? 2 : 1,
                                crossAxisSpacing: 12,
                                mainAxisSpacing: 12,
                                childAspectRatio:
                                    context.isDesktop ? 3.8 : 5,
                              ),
                              delegate: SliverChildBuilderDelegate(
                                (_, i) => _RecentTestCard(
                                    test: recent[i]),
                                childCount: recent.length,
                              ),
                            )
                          : SliverList.builder(
                              itemCount: recent.length,
                              itemBuilder: (_, i) =>
                                  _RecentTestCard(test: recent[i]),
                            ),
                    );
                  },
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
// Headers
// ─────────────────────────────────────────────────────────────────────────────

class _MobileHeader extends ConsumerWidget {
  const _MobileHeader();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning ☀️'
        : hour < 17
            ? 'Good afternoon 🌤'
            : 'Good evening 🌙';

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: AppColors.cardShadow.withOpacity(0.6),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: EdgeInsets.fromLTRB(
          20, MediaQuery.of(context).padding.top + 20, 20, 20),
      child: Row(
        children: [
          // Hamburger to open the sidebar drawer on mobile
          GestureDetector(
            onTap: () => Scaffold.of(context).openDrawer(),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.menu_rounded,
                  color: AppColors.primary, size: 22),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  greeting,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w400,
                  ),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                ),
                const SizedBox(height: 3),
                Text(
                  user?.fullName ?? 'User',
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.3,
                  ),
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                ),
                if (user?.organization != null) ...[
                  const SizedBox(height: 3),
                  Row(
                    children: [
                      const Icon(Icons.business_outlined,
                          size: 12, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          user!.organization!,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 1,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          // Tappable avatar with profile popup menu
          GestureDetector(
            onTap: () => _showProfileMenu(context, ref),
            child: ProfileAvatar(size: 46, showGradient: true),
          ),
        ],
      ),
    );
  }

  void _showProfileMenu(BuildContext context, WidgetRef ref) {
    final RenderBox box = context.findRenderObject()! as RenderBox;
    final sz = box.size;
    // Capture router before the async gap to avoid BuildContext misuse.
    final router = GoRouter.of(context);
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(
        sz.width - 180,
        MediaQuery.of(context).padding.top + 76,
        16,
        0,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      elevation: 4,
      items: const [
        PopupMenuItem(
          value: 'profile',
          child: Row(children: [
            Icon(Icons.person_outline_rounded, size: 18),
            SizedBox(width: 10),
            Text('My Profile'),
          ]),
        ),
        PopupMenuItem(
          value: 'settings',
          child: Row(children: [
            Icon(Icons.settings_outlined, size: 18),
            SizedBox(width: 10),
            Text('Settings'),
          ]),
        ),
        PopupMenuDivider(),
        PopupMenuItem(
          value: 'logout',
          child: Row(children: [
            Icon(Icons.logout_rounded, size: 18),
            SizedBox(width: 10),
            Text('Logout'),
          ]),
        ),
      ],
    ).then((value) {
      if (value == 'profile') router.push('/profile');
      if (value == 'settings') router.push('/settings');
      if (value == 'logout') ref.read(authProvider.notifier).logout();
    });
  }
}

class _WideHeader extends ConsumerWidget {
  const _WideHeader();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good morning ☀️'
        : hour < 17
            ? 'Good afternoon 🌤'
            : 'Good evening 🌙';

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: AppColors.cardShadow.withOpacity(0.6),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      padding: EdgeInsets.fromLTRB(
          0, MediaQuery.of(context).padding.top + 20, 0, 20),
      child: ContentContainer(
        padding: context.pagePadding,
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(greeting,
                      style: const TextStyle(
                          color: AppColors.textSecondary, fontSize: 14)),
                  const SizedBox(height: 3),
                  Text(
                    user?.fullName ?? 'User',
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 26,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.5,
                    ),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                  if (user?.organization != null) ...[
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        const Icon(Icons.business_outlined,
                            size: 13, color: AppColors.textSecondary),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(user!.organization!,
                              style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 13),
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            // Avatar with popup menu
            GestureDetector(
              onTap: () => _showProfileMenu(context, ref),
              child: ProfileAvatar(size: 48, showGradient: true),
            ),
          ],
        ),
      ),
    );
  }

  void _showProfileMenu(BuildContext context, WidgetRef ref) {
    final RenderBox box = context.findRenderObject()! as RenderBox;
    final sz = box.size;
    // Capture router before the async gap to avoid BuildContext misuse.
    final router = GoRouter.of(context);
    showMenu<String>(
      context: context,
      position: RelativeRect.fromLTRB(
        sz.width - 180,
        MediaQuery.of(context).padding.top + 76,
        16,
        0,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      elevation: 4,
      items: const [
        PopupMenuItem(
          value: 'profile',
          child: Row(children: [
            Icon(Icons.person_outline_rounded, size: 18),
            SizedBox(width: 10),
            Text('My Profile'),
          ]),
        ),
        PopupMenuItem(
          value: 'settings',
          child: Row(children: [
            Icon(Icons.settings_outlined, size: 18),
            SizedBox(width: 10),
            Text('Settings'),
          ]),
        ),
        PopupMenuDivider(),
        PopupMenuItem(
          value: 'logout',
          child: Row(children: [
            Icon(Icons.logout_rounded, size: 18),
            SizedBox(width: 10),
            Text('Logout'),
          ]),
        ),
      ],
    ).then((value) {
      if (value == 'profile') router.push('/profile');
      if (value == 'settings') router.push('/settings');
      if (value == 'logout') ref.read(authProvider.notifier).logout();
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Stats Section — 4 cards in a 2×2 grid
// ─────────────────────────────────────────────────────────────────────────────

class _StatsSection extends StatelessWidget {
  const _StatsSection({required this.tests, required this.padding});
  final List<SpectraTest> tests;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final total = tests.length;
    final genuine = tests
        .where((t) => t.classificationResult == ClassificationResult.genuine)
        .length;
    final counterfeit = tests
        .where((t) =>
            t.classificationResult ==
            ClassificationResult.potentially_counterfeit)
        .length;
    final unknown = tests
        .where((t) =>
            t.classificationResult ==
                ClassificationResult.requires_verification ||
            t.classificationResult == ClassificationResult.pending)
        .length;

    final stats = [
      _StatData(
        label: 'Total Tests',
        value: total.toString(),
        icon: Icons.biotech_rounded,
        color: AppColors.primary,
        bgColor: AppColors.primaryLight,
      ),
      _StatData(
        label: 'Genuine',
        value: genuine.toString(),
        icon: Icons.verified_rounded,
        color: AppColors.genuine,
        bgColor: AppColors.genuine.withOpacity(0.12),
      ),
      _StatData(
        label: 'Counterfeit',
        value: counterfeit.toString(),
        icon: Icons.gpp_bad_rounded,
        color: AppColors.counterfeit,
        bgColor: AppColors.counterfeit.withOpacity(0.10),
      ),
      _StatData(
        label: 'Unknown',
        value: unknown.toString(),
        icon: Icons.help_outline_rounded,
        color: AppColors.requiresVerification,
        bgColor: AppColors.requiresVerification.withOpacity(0.12),
      ),
    ];

    final cols = context.statGridColumns; // 2 mobile, 3 tablet, 4 desktop

    return ContentContainer(
      padding: padding.add(const EdgeInsets.only(top: 24)),
      child: GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: stats.length,
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: cols < 4 ? 2 : 4,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.55,
        ),
        itemBuilder: (_, i) => _PremiumStatCard(stat: stats[i]),
      ),
    );
  }
}

class _StatData {
  const _StatData({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    required this.bgColor,
  });
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final Color bgColor;
}

class _PremiumStatCard extends StatelessWidget {
  const _PremiumStatCard({required this.stat});
  final _StatData stat;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: stat.color.withOpacity(0.07),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
          const BoxShadow(
            color: AppColors.cardShadow,
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: stat.bgColor,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(stat.icon, color: stat.color, size: 18),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                stat.value,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: stat.color,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 1),
              Text(
                stat.label,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick Summary Card
// ─────────────────────────────────────────────────────────────────────────────

class _QuickSummaryCard extends StatelessWidget {
  const _QuickSummaryCard({required this.tests, required this.padding});
  final List<SpectraTest> tests;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final todayTests = tests
        .where((t) =>
            t.testedAt.year == now.year &&
            t.testedAt.month == now.month &&
            t.testedAt.day == now.day)
        .length;

    final lastTest = tests.isNotEmpty ? tests.first : null;

    final lastGenuine = tests
        .where((t) => t.classificationResult == ClassificationResult.genuine)
        .length;
    final total = tests.length;
    final genuineRate =
        total > 0 ? ((lastGenuine / total) * 100).toStringAsFixed(0) : '90';

    return ContentContainer(
      padding: padding.add(const EdgeInsets.only(top: 20)),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.primary,
              AppColors.primaryDark,
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withOpacity(0.30),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.20),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.insights_rounded,
                      color: Colors.white, size: 18),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Quick Summary',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _SummaryMetric(
                    label: "Today's Tests",
                    value: todayTests.toString(),
                    icon: Icons.today_rounded,
                  ),
                ),
                Container(
                    width: 1,
                    height: 40,
                    color: Colors.white.withOpacity(0.25)),
                Expanded(
                  child: _SummaryMetric(
                    label: 'Genuine Rate',
                    value: '$genuineRate%',
                    icon: Icons.verified_rounded,
                  ),
                ),
                Container(
                    width: 1,
                    height: 40,
                    color: Colors.white.withOpacity(0.25)),
                Expanded(
                  child: _SummaryMetric(
                    label: 'Total Tests',
                    value: total.toString(),
                    icon: Icons.science_rounded,
                  ),
                ),
              ],
            ),
            if (lastTest != null) ...[
              const SizedBox(height: 14),
              Container(
                height: 1,
                color: Colors.white.withOpacity(0.20),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.history_rounded,
                      color: Colors.white70, size: 14),
                  const SizedBox(width: 6),
                  const Text(
                    'Last test: ',
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                  Expanded(
                    child: Text(
                      lastTest.drugName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (lastTest.confidenceScore != null) ...[
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.20),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${lastTest.confidenceScore!.toStringAsFixed(1)}%',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.icon,
  });
  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white70, size: 18),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.5,
              ),
            ),
          ),
          Text(
            label,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 10,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick Actions Section — Upload Spectra, View Tests, Settings
// ─────────────────────────────────────────────────────────────────────────────

class _QuickActionsSection extends StatelessWidget {
  const _QuickActionsSection({required this.padding});
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final actions = [
      _ActionData(
        label: 'Upload\nSpectrum',
        icon: Icons.upload_file_rounded,
        color: AppColors.primary,
        bgColor: AppColors.primaryLight,
        path: '/upload',
      ),
      _ActionData(
        label: 'View\nTests',
        icon: Icons.biotech_rounded,
        color: const Color(0xFF5B6CF5), // indigo-blue
        bgColor: const Color(0xFFEEF0FD),
        path: '/tests',
      ),
    ];

    return ContentContainer(
      padding: padding.add(const EdgeInsets.only(top: 20)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Quick Actions',
            style: TextStyle(
              color: cs.onSurface,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: actions.asMap().entries.map((entry) {
              final isLast = entry.key == actions.length - 1;
              final a = entry.value;
              return Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: isLast ? 0 : 12),
                  child: _ActionTile(action: a),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _ActionData {
  const _ActionData({
    required this.label,
    required this.icon,
    required this.color,
    required this.bgColor,
    required this.path,
  });
  final String label;
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String path;
}

class _ActionTile extends StatefulWidget {
  const _ActionTile({required this.action});
  final _ActionData action;

  @override
  State<_ActionTile> createState() => _ActionTileState();
}

class _ActionTileState extends State<_ActionTile>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 120));
    _scale = Tween<double>(begin: 1.0, end: 0.95)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeIn));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final a = widget.action;
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        context.go(a.path);
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 8),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.border),
            boxShadow: [
              BoxShadow(
                color: a.color.withOpacity(0.08),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
              const BoxShadow(
                color: AppColors.cardShadow,
                blurRadius: 4,
                offset: Offset(0, 1),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: a.bgColor,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(a.icon, color: a.color, size: 24),
              ),
              const SizedBox(height: 10),
              Text(
                a.label,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  height: 1.4,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Recent Test Card — enhanced with confidence score
// ─────────────────────────────────────────────────────────────────────────────

class _RecentTestCard extends StatelessWidget {
  const _RecentTestCard({required this.test});
  final SpectraTest test;

  Color _resultAccent(ClassificationResult r) => switch (r) {
        ClassificationResult.genuine => AppColors.genuine,
        ClassificationResult.potentially_counterfeit => AppColors.counterfeit,
        ClassificationResult.requires_verification =>
          AppColors.requiresVerification,
        ClassificationResult.pending => AppColors.pending,
      };

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final accent = _resultAccent(test.classificationResult);

    return GestureDetector(
      onTap: () => context.go('/tests/${test.id}'),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        decoration: BoxDecoration(
          color: cs.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: cs.outline),
          boxShadow: [
            BoxShadow(
              color: accent.withOpacity(0.06),
              blurRadius: 10,
              offset: const Offset(0, 3),
            ),
            BoxShadow(
              color: cs.shadow.withOpacity(0.04),
              blurRadius: 4,
              offset: const Offset(0, 1),
            ),
          ],
        ),
        child: Row(
          children: [
            // Colored left accent bar
            Container(
              width: 4,
              height: 72,
              decoration: BoxDecoration(
                color: accent,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  bottomLeft: Radius.circular(16),
                ),
              ),
            ),
            const SizedBox(width: 14),
            // Drug icon
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: accent.withOpacity(0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(Icons.medication_rounded, color: accent, size: 20),
            ),
            const SizedBox(width: 12),
            // Info
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      test.drugName,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        const Icon(Icons.calendar_today_outlined,
                            size: 11, color: AppColors.textSecondary),
                        const SizedBox(width: 4),
                        Text(
                          DateFormat('MMM d, y').format(test.testedAt),
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 11),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            // Right: badge + confidence
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  ClassificationBadge(
                    result: test.classificationResult,
                    compact: true,
                  ),
                  if (test.confidenceScore != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      '${test.confidenceScore!.toStringAsFixed(1)}% AI',
                      style: TextStyle(
                        color: accent,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded,
                color: AppColors.textSecondary, size: 18),
            const SizedBox(width: 6),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Empty State
// ─────────────────────────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 48, horizontal: 20),
      child: Center(
        child: Column(
          children: [
            Container(
              width: 88,
              height: 88,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppColors.primary.withOpacity(0.15),
                    AppColors.primary.withOpacity(0.05),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.biotech_rounded,
                  size: 42, color: AppColors.primary),
            ),
            const SizedBox(height: 18),
            const Text(
              'No tests yet',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 17,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Upload a Raman spectrum CSV to run\nyour first AI classification',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 22),
            ElevatedButton.icon(
              onPressed: () => GoRouter.of(context).go('/upload'),
              icon: const Icon(Icons.upload_file_rounded, size: 18),
              label: const Text('Upload Spectrum'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(200, 48),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
