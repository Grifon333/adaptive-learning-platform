// ignore_for_file: public_member_api_docs, sort_constructors_first

import 'package:flutter/foundation.dart' show immutable;

@immutable
class RegisterRequest {
  final String email;
  final String password;
  final String firstName;
  final String lastName;

  const RegisterRequest({required this.email, required this.password, required this.firstName, required this.lastName});

  Map<String, dynamic> toJson() => {
    'email': email,
    'password': password,
    'first_name': firstName,
    'last_name': lastName,
  };
}

@immutable
class LoginRequest {
  final String email;
  final String password;

  const LoginRequest({required this.email, required this.password});

  Map<String, dynamic> toJson() => {'email': email, 'password': password};
}

@immutable
class TokenResponse {
  final String accessToken;
  final String refreshToken;

  const TokenResponse({required this.accessToken, required this.refreshToken});

  factory TokenResponse.fromJson(Map<String, dynamic> map) {
    return TokenResponse(accessToken: map['access_token'] as String, refreshToken: map['refresh_token'] as String);
  }
}

@immutable
class SocialLoginRequest {
  final String email;
  final String provider; // "google" | "microsoft"
  final String providerId;
  final String firstName;
  final String lastName;
  final String? avatarUrl;

  const SocialLoginRequest({
    required this.email,
    required this.provider,
    required this.providerId,
    required this.firstName,
    required this.lastName,
    this.avatarUrl,
  });

  Map<String, dynamic> toJson() => {
    'email': email,
    'provider': provider,
    'provider_id': providerId,
    'first_name': firstName,
    'last_name': lastName,
    'avatar_url': avatarUrl,
  };
}

@immutable
class ForgotPasswordRequest {
  final String email;

  const ForgotPasswordRequest({required this.email});

  Map<String, dynamic> toJson() => {'email': email};
}
