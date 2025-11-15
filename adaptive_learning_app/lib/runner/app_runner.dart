import 'dart:async';
import 'dart:ui';

import 'package:adaptive_learning_app/app/app.dart';
import 'package:adaptive_learning_app/app/app_env.dart';
import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/debug/debug_service.dart';
import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

part 'errors_handlers.dart';

// Dependency initialization wait time.
// If exceeded, an error screen will be displayed.
const _initTimeout = Duration(seconds: 10);

/// {@template app_runner}
/// Class that implements application launch and configuration.
///
/// Initialization order:
/// 1. _initApp - basic Flutter initialization (screen orientation).
/// 2. _initErrorHandlers - configuration of global error handlers.
/// 3. _initDependencies - asynchronous initialization of services (DI).
/// 4. runApp - launch of the Flutter application.
/// {@endtemplate}
class AppRunner {
  AppRunner(this.env);

  final AppEnv env;
  late final IDebugService _debugService;

  Future<void> run() async {
    await runZonedGuarded(
      () async {
        WidgetsFlutterBinding.ensureInitialized();
        _debugService = DebugService();
        Bloc.observer = _debugService.blocObserver;
        await _initApp();
        _initErrorHandlers(_debugService);
        runApp(
          App(
            initDependencies: () => _initDependencies(debugService: _debugService, env: env).timeout(
              _initTimeout,
              onTimeout: () => throw TimeoutException('Dependency initialization timeout exceeded ($_initTimeout)'),
            ),
          ),
        );
      },
      (error, stackTrace) {
        // Handling errors that occur outside of Flutter (e.g., during initialization)
        _debugService.logError('Uncaught error in runZonedGuarded', error: error, stackTrace: stackTrace);
      },
    );
  }

  Future<void> _initApp() async {
    await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp, DeviceOrientation.portraitDown]);
  }

  Future<DiContainer> _initDependencies({required IDebugService debugService, required AppEnv env}) async {
    debugService.log('Assembly type: ${env.name}');
    final diContainer = DiContainer(env: env, debugServ: debugService);

    await diContainer.init(
      onProgress: (name) => debugService.log('Initialized: $name'),
      onComplete: (name) => debugService.log(name),
      onError: (message, error, [stackTrace]) {
        debugService.logError(message, error: error, stackTrace: stackTrace);
        throw Exception('Dependency initialization error: $message');
      },
    );
    return diContainer;
  }
}
