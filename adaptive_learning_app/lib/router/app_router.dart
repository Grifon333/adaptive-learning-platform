import 'package:adaptive_learning_app/features/dashboard/presentation/screens/dashboard_screen.dart';
import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:adaptive_learning_app/features/profile/presentation/screens/profile_screen.dart';
import 'package:adaptive_learning_app/features/root/root_screen.dart';
import 'package:adaptive_learning_app/features/splash/splash_screen.dart';
import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

/// {@template app_router}
/// Class for managing navigation in the application
/// {@endtemplate}
class AppRouter {
  static final rootNavigationKey = GlobalKey<NavigatorState>();
  static const String initialLocation = '/dashboard';

  static GoRouter createRouter(IDebugService debugService) {
    return GoRouter(
      navigatorKey: rootNavigationKey,
      initialLocation: initialLocation,
      observers: [debugService.routeObserver],
      // TODO: Redirect logic to check if the user is logged in
      routes: [
        // --- Main navigation (with BottomNavigationBar) ---
        StatefulShellRoute.indexedStack(
          parentNavigatorKey: rootNavigationKey,
          builder: (_, _, navigationShell) => RootScreen(navigationShell: navigationShell),
          branches: [
            // 1. Dashboard
            StatefulShellBranch(
              routes: [
                GoRoute(path: '/dashboard', name: 'dashboard', builder: (context, state) => const DashboardScreen()),
              ],
            ),
            // 2. Profile
            StatefulShellBranch(
              routes: [GoRoute(path: '/profile', name: 'profile', builder: (context, state) => const ProfileScreen())],
            ),
          ],
        ),

        // --- Separate screens (outside BottomNavigationBar) ---
        GoRoute(path: '/splash', name: 'splash', builder: (context, state) => const SplashScreen()),
        // TODO
        // GoRoute(path: '/login', name: 'login', builder: (context, state) => const LoginScreen()),
        // GoRoute(path: '/register', name: 'register', builder: (context, state) => const RegisterScreen()),
      ],
    );
  }
}
