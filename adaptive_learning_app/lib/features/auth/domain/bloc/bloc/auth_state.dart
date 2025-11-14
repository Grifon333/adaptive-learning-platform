part of 'auth_bloc.dart';

@immutable
sealed class AuthState extends Equatable {
  const AuthState();

  @override
  List<Object?> get props => [];
}

final class AuthUnknown extends AuthState {}

sealed class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated({this.error});

  final String? error;

  @override
  List<Object?> get props => [error ?? ''];
}

final class AuthIdle extends AuthUnauthenticated {
  const AuthIdle() : super(error: null);
}

final class AuthLoginFailure extends AuthUnauthenticated {
  const AuthLoginFailure({required String super.error});
}

final class AuthRegisterFailure extends AuthUnauthenticated {
  const AuthRegisterFailure({required String super.error});
}

final class AuthLoading extends AuthState {}

final class AuthAuthenticated extends AuthState {}

final class AuthRegisterSuccess extends AuthState {}
