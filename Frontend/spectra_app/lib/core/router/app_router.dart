import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/features/auth/screens/login_screen.dart';
import 'package:spectra_app/features/auth/screens/signup_screen.dart';
import 'package:spectra_app/features/dashboard/dashboard_screen.dart';
import 'package:spectra_app/features/tests/screens/tests_list_screen.dart';
import 'package:spectra_app/features/tests/screens/test_detail_screen.dart';
import 'package:spectra_app/features/spectra/screens/upload_spectra_screen.dart';
import 'package:spectra_app/features/classify/screens/classify_screen.dart';
import 'package:spectra_app/features/reports/screens/report_screen.dart';
import 'package:spectra_app/features/reference/screens/reference_list_screen.dart';
import 'package:spectra_app/features/admin/screens/admin_screen.dart';
import 'package:spectra_app/features/admin/screens/admin_users_screen.dart';
import 'package:spectra_app/features/about/about_screen.dart';
import 'package:spectra_app/features/profile/screens/profile_screen.dart';
import 'package:spectra_app/features/settings/screens/settings_screen.dart';
import 'package:spectra_app/features/chat/screens/chat_screen.dart';
import 'package:spectra_app/features/nearby/screens/nearby_screen.dart';
import 'package:spectra_app/shared/widgets/main_shell.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/login',
    redirect: (context, state) {
      final loggedIn = auth.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/login') ||
          state.matchedLocation.startsWith('/signup');

      if (!loggedIn && !isAuthRoute) return '/login';
      if (loggedIn && isAuthRoute) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        builder: (_, __) => const SignupScreen(),
      ),
      ShellRoute(
        builder: (_, __, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            builder: (_, __) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/tests',
            builder: (_, __) => const TestsListScreen(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (_, state) => TestDetailScreen(
                  testId: int.parse(state.pathParameters['id']!),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/upload',
            builder: (_, __) => const UploadSpectraScreen(),
          ),
          GoRoute(
            path: '/classify/:id',
            builder: (_, state) => ClassifyScreen(
              testId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/reports/:id',
            builder: (_, state) => ReportScreen(
              testId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/reference',
            builder: (_, __) => const ReferenceListScreen(),
          ),
          GoRoute(
            path: '/admin',
            builder: (_, __) => const AdminScreen(),
          ),
          GoRoute(
            path: '/admin/users',
            builder: (_, __) => const AdminUsersScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (_, __) => const ProfileScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (_, __) => const SettingsScreen(),
          ),
          GoRoute(
            path: '/about',
            builder: (_, __) => const AboutScreen(),
          ),
          GoRoute(
            path: '/chat',
            builder: (_, __) => const ChatScreen(),
          ),
          GoRoute(
            path: '/nearby',
            builder: (_, __) => const NearbyScreen(),
          ),
        ],
      ),
    ],
  );
});
