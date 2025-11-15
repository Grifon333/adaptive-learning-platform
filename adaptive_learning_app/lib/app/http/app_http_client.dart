import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/auth_interceptor.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:dio/dio.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template app_http_client}
/// Class for implementing an HTTP client (Dio)
/// {@endtemplate}
final class AppHttpClient implements IHttpClient {
  AppHttpClient({
    required IDebugService debugService,
    required IAppConfig appConfig,
    required ISecureStorage secureStorage,
  }) {
    _httpClient = Dio();
    _appConfig = appConfig;

    _httpClient.options
      ..baseUrl = appConfig.baseUrl
      ..connectTimeout = const Duration(seconds: 10)
      ..sendTimeout = const Duration(seconds: 10)
      ..receiveTimeout = const Duration(seconds: 10)
      ..headers = {'Content-Type': 'application/json'};

    _httpClient.interceptors.add(debugService.dioLogger);
    _httpClient.interceptors.add(
      AuthInterceptor(httpClient: _httpClient, secureStorage: secureStorage, debugService: debugService),
    );

    debugService.log('HTTP client created');
  }

  late final IAppConfig _appConfig;
  late final Dio _httpClient;

  @override
  Future<Response> get(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _httpClient.get(path, data: data, queryParameters: queryParameters, options: options);
  }

  @override
  Future<Response> post(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _httpClient.post(path, data: data, queryParameters: queryParameters, options: options);
  }

  @override
  Future<Response> patch(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _httpClient.patch(path, data: data, queryParameters: queryParameters, options: options);
  }

  @override
  Future<Response> put(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _httpClient.put(path, data: data, queryParameters: queryParameters, options: options);
  }

  @override
  Future<Response> delete(String path, {Object? data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _httpClient.delete(path, data: data, queryParameters: queryParameters, options: options);
  }
}
