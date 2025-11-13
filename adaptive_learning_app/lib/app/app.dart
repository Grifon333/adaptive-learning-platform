import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/app/app_providers.dart';
import 'package:adaptive_learning_app/app/depends_providers.dart';
import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/error/error_screen.dart';
import 'package:adaptive_learning_app/features/splash/splash_screen.dart';
import 'package:adaptive_learning_app/l10n/gen/app_localizations.dart';
import 'package:adaptive_learning_app/l10n/localization_notifier.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// {@template app}
/// The main widget of the application that manages dependency
/// initialization and displays the main interface.
/// {@endtemplate}
class App extends StatefulWidget {
  const App({required this.router, required this.initDependencies, super.key});

  final GoRouter router;
  final Future<DiContainer> Function() initDependencies;

  @override
  State<App> createState() => _AppState();
}

class _AppState extends State<App> {
  late Future<DiContainer> _initFuture;

  @override
  void initState() {
    super.initState();
    _initFuture = widget.initDependencies();
  }

  @override
  Widget build(BuildContext context) {
    return AppProviders(
      child: LocalizationConsumer(
        builder: () => FutureBuilder<DiContainer>(
          future: _initFuture,
          builder: (_, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) return const SplashScreen(isFullScreen: true);
            if (snapshot.hasError) {
              return ErrorScreen(error: snapshot.error, stackTrace: snapshot.stackTrace, onRetry: _retryInit);
            }
            if (snapshot.hasData && snapshot.data != null) {
              return _App(router: widget.router, diContainer: snapshot.data!);
            }
            return const SplashScreen(isFullScreen: true);
          },
        ),
      ),
    );
  }

  void _retryInit() {
    setState(() => _initFuture = widget.initDependencies());
  }
}

/// {@template app_internal}
/// Internal application widget that displays MaterialApp
/// after successful initialization of dependencies.
/// {@endtemplate}
class _App extends StatelessWidget {
  const _App({required this.router, required this.diContainer});

  final GoRouter router;
  final DiContainer diContainer;

  @override
  Widget build(BuildContext context) {
    return DependsProviders(
      diContainer: diContainer,
      child: MaterialApp.router(
        routerConfig: router,
        // --- Localization ---
        locale: context.localization.locale,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        // --- Theme ---
        theme: ThemeData.light(),
        darkTheme: ThemeData.dark(),
        themeMode: ThemeMode.system, // TODO: connect ThemeNotifier
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
