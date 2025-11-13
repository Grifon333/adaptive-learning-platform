// ignore_for_file: public_member_api_docs, sort_constructors_first

import 'package:flutter/foundation.dart' show immutable;

@immutable
class RegisterRequest {
  final String email;
  final String password;
  final String firstName;
  final String lastName;

  const RegisterRequest({required this.email, required this.password, required this.firstName, required this.lastName});

  Map<String, dynamic> toJson() => {'email': email, 'password': password, 'firstName': firstName, 'lastName': lastName};
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
    return TokenResponse(accessToken: map['accessToken'] as String, refreshToken: map['refreshToken'] as String);
  }
}
