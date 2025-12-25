import 'package:adaptive_learning_app/di/di_base_repository.dart';

/// {@template i_auth_repository}
/// Interface for working with the authorization repository
/// {@endtemplate}
abstract interface class IAuthRepository with DiBaseRepository {
  Future<void> login({required String email, required String password});

  Future<void> socialLogin({
    required String email,
    required String provider,
    required String providerId,
    required String firstName,
    required String lastName,
    String? avatarUrl,
  });

  Future<void> forgotPassword(String email);

  Future<void> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  });

  Future<void> logout();
}
