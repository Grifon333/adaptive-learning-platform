import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/app_env.dart';
import 'package:adaptive_learning_app/app/http/app_http_client.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/di/di_repositories.dart';
import 'package:adaptive_learning_app/di/di_services.dart';
import 'package:adaptive_learning_app/di/di_typedefs.dart';
import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';

/// {@template di_container}
/// Container for all application dependencies (services, repositories).
/// Initialized asynchronously during startup.
/// {@endtemplate}
final class DiContainer {
  DiContainer({required this.env, required IDebugService debugServ}) : debugService = debugServ;

  final AppEnv env;
  late final IDebugService debugService;
  late final IAppConfig appConfig;
  late final IHttpClient httpClient;
  late final DiRepositories repositories;
  late final DiServices services;

  Future<void> init({required OnProgress onProgress, required OnComplete onComplete, required OnError onError}) async {
    appConfig = switch (env) {
      AppEnv.dev => AppConfigDev(),
      AppEnv.stage => AppConfigStage(),
      AppEnv.prod => AppConfigProd(),
    };
    onProgress('AppConfig');

    services = DiServices()..init(onProgress: onProgress, onError: onError, diContainer: this);
    onProgress('DiServices');

    httpClient = AppHttpClient(debugService: debugService, appConfig: appConfig, secureStorage: services.secureStorage);
    onProgress('IHttpClient');

    repositories = DiRepositories()..init(onProgress: onProgress, onError: onError, diContainer: this);
    onProgress('DiRepositories');

    onComplete('Dependency initialization is complete.');
  }
}
