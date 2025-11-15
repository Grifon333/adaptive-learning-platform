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

  static const _publicRoutes = {
    '/auth/login',
    '/auth/register',
    // TODO: add '/auth/refresh'
  };

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
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _debugService.logError('AuthInterceptor: Request error', error: err);
    if (err.response?.statusCode == 401) {
      if (err.requestOptions.path != '/auth/login') {
        _debugService.logWarning('AuthInterceptor: Received 401. Refreshing token...');

        // TODO: Implement token refresh logic
        // 1. Get refresh token from _secureStorage
        // 2. Make a request to POST /api/v1/auth/refresh
        // 3. If successful:
        //    - Save new access and refresh tokens
        //    - Update the ‘Authorization’ header in err.requestOptions
        //    - Repeat the request: return handler.resolve(await _httpClient.fetch(err.requestOptions));
        // 4. If unsuccessful:
        //    - Delete tokens
        //    - “Fail” the request: return handler.next(err);

        // For now, we just “fail” the request
        _debugService.logError('AuthInterceptor: Token refresh logic not implemented.');
      }
      return handler.next(err);
    }
    super.onError(err, handler);
  }
}
