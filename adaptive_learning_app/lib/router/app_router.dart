import 'dart:async';

import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/admin_graph/presentation/screens/admin_graph_screen.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/auth/presentation/screens/login_screen.dart';
import 'package:adaptive_learning_app/features/auth/presentation/screens/register_screen.dart';
import 'package:adaptive_learning_app/features/dashboard/presentation/screens/dashboard_screen.dart';
import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/lesson_bloc/lesson_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/assessment_screen.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/concept_selector_screen.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/create_path_mode_screen.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/learning_path_screen.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/learning_paths_list_screen.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/lesson_screen.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/quiz_screen.dart';
import 'package:adaptive_learning_app/features/profile/presentation/screens/profile_screen.dart';
import 'package:adaptive_learning_app/features/root/root_screen.dart';
import 'package:adaptive_learning_app/features/splash/splash_screen.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

/// {@template app_router}
/// Class for managing navigation in the application
/// {@endtemplate}
class AppRouter {
  static final rootNavigatorKey = GlobalKey<NavigatorState>();
  static const String initialLocation = '/splash';

  static GoRouter createRouter(IDebugService debugService, AuthBloc authBloc) {
    return GoRouter(
      navigatorKey: rootNavigatorKey,
      initialLocation: initialLocation,
      observers: [debugService.routeObserver],
      refreshListenable: GoRouterRefreshStream(authBloc.stream),
      redirect: (BuildContext context, GoRouterState state) {
        final authState = authBloc.state;
        final location = state.matchedLocation;
        final isAuthRoute = location == '/login' || location == '/register';
        if (authState is AuthUnknown) return location == '/splash' ? null : '/splash';
        if (authState is AuthAuthenticated) return (isAuthRoute || location == '/splash') ? '/dashboard' : null;
        if (authState is AuthUnauthenticated) return isAuthRoute ? null : '/login';
        return null;
      },
      routes: [
        // --- Main navigation (with BottomNavigationBar) ---
        StatefulShellRoute.indexedStack(
          parentNavigatorKey: rootNavigatorKey,
          builder: (_, _, navigationShell) => RootScreen(navigationShell: navigationShell),
          branches: [
            // 1. Dashboard
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/dashboard',
                  name: 'dashboard',
                  builder: (context, state) => const DashboardScreen(),
                  routes: [
                    // List of trajectories
                    GoRoute(
                      path: 'paths',
                      name: 'paths_list',
                      builder: (context, state) => const LearningPathsListScreen(),
                      routes: [
                        // Creation mode selection screen
                        GoRoute(
                          path: 'create',
                          name: 'create_path_mode',
                          builder: (context, state) => const CreatePathModeScreen(),
                          routes: [
                            // Concept selection screen (dynamic)
                            GoRoute(
                              path: 'select',
                              name: 'concept_selector',
                              builder: (context, state) {
                                final mode = state.extra as CreatePathMode;
                                return ConceptSelectorScreen(mode: mode);
                              },
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
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
        GoRoute(path: '/login', name: 'login', builder: (context, state) => const LoginScreen()),
        GoRoute(path: '/register', name: 'register', builder: (context, state) => const RegisterScreen()),

        GoRoute(path: '/learning-path', name: 'learning-path', builder: (context, state) => const LearningPathScreen()),
        GoRoute(
          path: '/lesson',
          name: 'lesson',
          builder: (context, state) {
            final step = state.extra as LearningStepDto;
            return BlocProvider(
              create: (ctx) =>
                  LessonBloc(repository: ctx.di.repositories.learningPathRepository, stepId: step.id)
                    ..add(LessonStarted()),
              child: LessonScreen(step: step),
            );
          },
        ),
        GoRoute(
          path: '/quiz',
          name: 'quiz',
          builder: (context, state) {
            final args = state.extra as Map<String, String>;
            return QuizScreen(stepId: args['stepId']!, conceptId: args['conceptId']!);
          },
        ),

        GoRoute(
          path: '/assessment',
          name: 'assessment',
          builder: (context, state) {
            final goalId = state.extra as String;
            return AssessmentScreen(goalConceptId: goalId);
          },
        ),

        GoRoute(path: '/admin-graph', name: 'admin_graph', builder: (context, state) => const AdminGraphScreen()),
      ],
    );
  }
}

// Helper for converting Stream<AuthState> to Listenable for GoRouter.
class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
