import 'package:adaptive_learning_app/app/http/auth_interceptor.dart';
import 'package:adaptive_learning_app/features/auth/domain/repository/i_auth_repository.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:i_app_services/i_app_services.dart';
import 'package:meta/meta.dart';

part 'auth_event.dart';
part 'auth_state.dart';

/// {@template auth_bloc}
/// Bloc for managing authorization status.
/// {@endtemplate}
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc({required IAuthRepository authRepository, required ISecureStorage secureStorage})
    : _authRepository = authRepository,
      _secureStorage = secureStorage,
      super(AuthUnknown()) {
    on<AuthCheckRequested>(_onCheckRequested);
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthRegisterRequested>(_onRegisterRequested);
    on<AuthLogoutRequested>(_onLogoutRequested);

    add(AuthCheckRequested());
  }

  final IAuthRepository _authRepository;
  final ISecureStorage _secureStorage;

  Future<void> _onCheckRequested(AuthCheckRequested event, Emitter<AuthState> emit) async {
    final hasToken = await _secureStorage.containsKey(SecureStorageKeys.accessToken);
    emit(hasToken ? AuthAuthenticated() : const AuthUnauthenticated());
  }

  Future<void> _onLoginRequested(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _authRepository.login(email: event.email, password: event.password);
      emit(AuthAuthenticated());
    } on Object catch (err, st) {
      emit(AuthUnauthenticated(error: err.toString()));
      addError(err, st);
    }
  }

  Future<void> _onRegisterRequested(AuthRegisterRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _authRepository.register(
        email: event.email,
        password: event.password,
        firstName: event.firstName,
        lastName: event.lastName,
      );
      emit(AuthRegisterSuccess());
    } on Object catch (err, st) {
      emit(AuthUnauthenticated(error: err.toString()));
      addError(err, st);
    }
  }

  Future<void> _onLogoutRequested(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    // TODO: _authRepository.logout();
    await _secureStorage.deleteAll();
    emit(const AuthUnauthenticated());
  }
}
