import 'package:adaptive_learning_app/features/auth/domain/repository/i_auth_repository.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:meta/meta.dart';

part 'auth_event.dart';
part 'auth_state.dart';

/// {@template auth_bloc}
/// Bloc for managing authorization status.
/// {@endtemplate}
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc(this._authRepository) : super(AuthInitial()) {
    on<AuthLoginRequested>(_onLoginRequested);
    on<AuthRegisterRequested>(_onRegisterRequested);
  }

  final IAuthRepository _authRepository;

  Future<void> _onLoginRequested(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(AuthLoading());
    try {
      await _authRepository.login(email: event.email, password: event.password);
      emit(AuthSuccess());
    } on Object catch (err, st) {
      emit(AuthFailure(err.toString()));
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
      emit(AuthFailure(err.toString()));
      addError(err, st);
    }
  }
}
