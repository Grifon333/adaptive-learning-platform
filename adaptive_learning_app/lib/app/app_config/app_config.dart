import 'package:adaptive_learning_app/app/app_env.dart';
import 'package:envied/envied.dart';

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
  @EnviedField()
  final String baseUrl = _Dev.baseUrl;

  @override
  @EnviedField(obfuscate: true)
  final String secretKey = _Dev.secretKey;
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
}
