import 'package:adaptive_learning_app/app/http/auth_interceptor.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/auth/data/dto/auth_dtos.dart';
import 'package:adaptive_learning_app/features/auth/domain/repository/i_auth_repository.dart';
import 'package:dio/dio.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template auth_repository}
/// Implementation of the authorization repository
/// {@endtemplate}
final class AuthRepository implements IAuthRepository {
  AuthRepository({required this.httpClient, required this.secureStorage});

  final IHttpClient httpClient;
  final ISecureStorage secureStorage;

  @override
  String get name => 'AuthRepository';

  @override
  Future<void> login({required String email, required String password}) async {
    final request = LoginRequest(email: email, password: password);
    final response = await httpClient.post(
      '/auth/login',
      data: request.toJson(),
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );
    final tokenResponse = TokenResponse.fromJson(response.data);
    await secureStorage.write(SecureStorageKeys.accessToken, tokenResponse.accessToken);
    await secureStorage.write(SecureStorageKeys.refreshToken, tokenResponse.refreshToken);
  }

  @override
  Future<void> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  }) async {
    final request = RegisterRequest(email: email, password: password, firstName: firstName, lastName: lastName);
    await httpClient.post('/auth/register', data: request.toJson());
  }
}
