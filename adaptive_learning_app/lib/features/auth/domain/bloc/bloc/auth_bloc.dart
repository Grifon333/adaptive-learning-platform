import 'package:adaptive_learning_app/app/http/auth_interceptor.dart';
import 'package:adaptive_learning_app/features/auth/domain/repository/i_auth_repository.dart';
import 'package:dio/dio.dart';
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

  String _parseDioError(DioException e) {
    if (e.response != null && e.response?.data is Map) {
      final data = e.response!.data as Map<String, dynamic>;
      if (data.containsKey('detail') && data['detail'] is List && (data['detail'] as List).isNotEmpty) {
        final firstError = (data['detail'] as List).first;
        if (firstError is Map && firstError.containsKey('msg')) return firstError['msg'] as String;
      } else if (data.containsKey('detail')) {
        return data['detail'] as String;
      }
    }
    return e.message ?? 'An unknown error has occurred.';
  }

  Future<void> _onCheckRequested(AuthCheckRequested event, Emitter<AuthState> emit) async {
    final hasToken = await _secureStorage.containsKey(SecureStorageKeys.accessToken);
    emit(hasToken ? AuthAuthenticated() : const AuthIdle());
  }

  Future<void> _onLoginRequested(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _authRepository.login(email: event.email, password: event.password);
      emit(AuthAuthenticated());
    } on Object catch (e, st) {
      addError(e, st);
      String errorMessage = 'An unknown error has occurred.';
      if (e is DioException) errorMessage = _parseDioError(e);
      emit(AuthLoginFailure(error: errorMessage));
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
      emit(const AuthIdle());
    } on Object catch (e, st) {
      addError(e, st);
      String errorMessage = 'An unknown error has occurred.';
      if (e is DioException) errorMessage = _parseDioError(e);
      emit(AuthRegisterFailure(error: errorMessage));
    }
  }

  Future<void> _onLogoutRequested(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    await _authRepository.logout();
    emit(const AuthIdle());
  }
}
