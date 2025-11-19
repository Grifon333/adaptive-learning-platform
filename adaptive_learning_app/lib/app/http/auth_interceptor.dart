import 'package:adaptive_learning_app/features/auth/data/dto/auth_dtos.dart';
import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:dio/dio.dart';
import 'package:i_app_services/i_app_services.dart';

abstract final class SecureStorageKeys {
  static const accessToken = 'access_token';
  static const refreshToken = 'refresh_token';
}

/// {@template auth_interceptor}
/// Interceptor, which automatically adds Access Token to requests
/// and handles token refresh (Refresh Token) in case of a 401 error.
/// {@endtemplate}
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({required Dio httpClient, required ISecureStorage secureStorage, required IDebugService debugService})
    : _httpClient = httpClient,
      _secureStorage = secureStorage,
      _debugService = debugService;

  final Dio _httpClient;
  final ISecureStorage _secureStorage;
  final IDebugService _debugService;

  static const _publicRoutes = {'/auth/login', '/auth/register', '/auth/refresh'};

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    if (_publicRoutes.contains(options.path)) return handler.next(options);
    final accessToken = await _secureStorage.read(SecureStorageKeys.accessToken);
    if (accessToken != null) {
      options.headers['Authorization'] = 'Bearer $accessToken';
      _debugService.log('AuthInterceptor: Added Bearer token to request.');
    } else {
      _debugService.logWarning('AuthInterceptor: No access token found.');
    }
    super.onRequest(options, handler);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    _debugService.logError('AuthInterceptor: Request error', error: err);
    if (err.response?.statusCode == 401) {
      final isRefreshPath = err.requestOptions.path.contains('/auth/refresh');
      if (!isRefreshPath) {
        _debugService.logWarning('AuthInterceptor: Received 401. Attempting token refresh...');

        // 1. Get refresh token
        final refreshToken = await _secureStorage.read(SecureStorageKeys.refreshToken);
        if (refreshToken == null) {
          _debugService.logError('AuthInterceptor: No refresh token found. Redirecting to login.');
          return handler.next(err);
        }

        // 2. Execure update request
        try {
          final dio = Dio(
            BaseOptions(
              baseUrl: _httpClient.options.baseUrl,
              connectTimeout: _httpClient.options.connectTimeout,
              sendTimeout: _httpClient.options.sendTimeout,
              receiveTimeout: _httpClient.options.receiveTimeout,
            ),
          );

          final refreshResponse = await dio.post(
            '${_httpClient.options.baseUrl}/api/v1/auth/refresh',
            data: {'refresh_token': refreshToken},
          );
          final newTokens = TokenResponse.fromJson(refreshResponse.data);

          // 3. Storage new tokens
          await _secureStorage.write(SecureStorageKeys.accessToken, newTokens.accessToken);
          await _secureStorage.write(SecureStorageKeys.refreshToken, newTokens.refreshToken);
          _debugService.log('AuthInterceptor: Tokens successfully refreshed.');

          // 4. Repaet original request
          final originalRequest = err.requestOptions;
          originalRequest.headers['Authorization'] = 'Bearer ${newTokens.accessToken}';
          final response = await _httpClient.fetch(originalRequest);
          return handler.resolve(response);
        } on DioException catch (e) {
          // If the update fails (e.g., invalid refresh token), clear the cache
          _debugService.logError('AuthInterceptor: Token refresh failed.', error: e);
          await _secureStorage.delete(SecureStorageKeys.accessToken);
          await _secureStorage.delete(SecureStorageKeys.refreshToken);
          // Allow 401 to pass for AuthBloc logout call
          return handler.next(err);
        }
      }
      return handler.next(err);
    }
    super.onError(err, handler);
  }
}
