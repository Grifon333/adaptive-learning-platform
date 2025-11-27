import 'dart:io';

import 'package:adaptive_learning_app/app/app_env.dart';
import 'package:envied/envied.dart';
import 'package:flutter/foundation.dart';

part 'app_config.g.dart';

/// {@template i_app_config}
/// Interface for application configuration.
/// Defines mandatory parameters for all configuration implementations.
/// {@endtemplate}
abstract interface class IAppConfig {
  IAppConfig();

  String get name => 'IAppConfig';
  String get baseUrl;
  AppEnv get env;
  String get secretKey;

  String get learningPathServiceUrl;
  String get eventServiceUrl;
  String get knowledgeGraphServiceUrl;
  String get mlServiceUrl;
  String get analyticsServiceUrl;
}

/// {@template app_config_dev}
/// Application configuration for development mode (dev).
/// Uses environment variables from the env/dev.env file.
/// {@endtemplate}
@Envied(name: 'Dev', path: 'env/dev.env')
class AppConfigDev implements IAppConfig {
  AppConfigDev();

  @override
  AppEnv get env => AppEnv.dev;

  @override
  String get name => 'AppConfigDev';

  @override
  @EnviedField(obfuscate: true)
  final String secretKey = _Dev.secretKey;

  String get _host {
    if (kIsWeb) return 'localhost';
    if (Platform.isAndroid) return '10.0.2.2';
    return '127.0.0.1';
  }

  @override
  String get baseUrl => 'http://$_host:8000/api/v1';

  @override
  String get knowledgeGraphServiceUrl => 'http://$_host:8001/api/v1';

  @override
  String get learningPathServiceUrl => 'http://$_host:8002/api/v1';

  @override
  String get eventServiceUrl => 'http://$_host:8003/api/v1';

  @override
  String get mlServiceUrl => 'http://$_host:8004/api/v1';

  @override
  String get analyticsServiceUrl => 'http://$_host:8005/api/v1';
}

/// {@template app_config_stage}
/// Application configuration for production mode (prod).
/// Uses environment variables from the env/prod.env file.
/// {@endtemplate}
@Envied(name: 'Stage', path: 'env/stage.env')
class AppConfigStage implements IAppConfig {
  AppConfigStage();

  @override
  AppEnv get env => AppEnv.stage;

  @override
  String get name => 'AppConfigStage';

  @override
  @EnviedField(obfuscate: true)
  final String baseUrl = _Stage.baseUrl;

  @override
  @EnviedField(obfuscate: true)
  final String secretKey = _Stage.secretKey;

  // Assuming Stage uses an API Gateway or specific domains
  // For now, we point everything to baseUrl if it's a monolith gateway.

  @override
  String get learningPathServiceUrl => baseUrl;
  @override
  String get eventServiceUrl => baseUrl;
  @override
  String get knowledgeGraphServiceUrl => baseUrl;
  @override
  String get mlServiceUrl => baseUrl;
  @override
  String get analyticsServiceUrl => baseUrl;
}

/// {@template app_config_prod}
/// Application configuration for stage mode (stage).
/// Uses environment variables from the env/stage.env file.
/// {@endtemplate}
@Envied(name: 'Prod', path: 'env/prod.env')
class AppConfigProd implements IAppConfig {
  AppConfigProd();

  @override
  AppEnv get env => AppEnv.prod;

  @override
  String get name => 'AppConfigProd';

  @override
  @EnviedField(obfuscate: true)
  final String baseUrl = _Prod.baseUrl;

  @override
  @EnviedField(obfuscate: true)
  final String secretKey = _Prod.secretKey;

  @override
  String get learningPathServiceUrl => baseUrl;
  @override
  String get eventServiceUrl => baseUrl;
  @override
  String get knowledgeGraphServiceUrl => baseUrl;
  @override
  String get mlServiceUrl => baseUrl;
  @override
  String get analyticsServiceUrl => baseUrl;
}
