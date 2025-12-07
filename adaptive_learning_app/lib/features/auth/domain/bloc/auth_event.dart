part of 'auth_bloc.dart';

@immutable
sealed class AuthEvent extends Equatable {
  const AuthEvent();

  @override
  List<Object?> get props => [];
}

final class AuthCheckRequested extends AuthEvent {}

final class AuthLogoutRequested extends AuthEvent {}

final class AuthLoginRequested extends AuthEvent {
  const AuthLoginRequested({required this.email, required this.password});

  final String email;
  final String password;

  @override
  List<Object?> get props => [email];
}

final class AuthRegisterRequested extends AuthEvent {
  const AuthRegisterRequested({
    required this.email,
    required this.password,
    required this.firstName,
    required this.lastName,
  });

  final String email;
  final String password;
  final String firstName;
  final String lastName;

  @override
  List<Object?> get props => [email];
}

final class AuthSocialLoginRequested extends AuthEvent {
  const AuthSocialLoginRequested({
    required this.email,
    required this.provider,
    required this.providerId,
    required this.firstName,
    required this.lastName,
    this.avatarUrl,
  });

  final String email;
  final String provider;
  final String providerId;
  final String firstName;
  final String lastName;
  final String? avatarUrl;

  @override
  List<Object?> get props => [email, provider, providerId];
}

final class AuthForgotPasswordRequested extends AuthEvent {
  const AuthForgotPasswordRequested(this.email);
  final String email;
  @override
  List<Object?> get props => [email];
}
