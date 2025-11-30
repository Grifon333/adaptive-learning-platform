import 'package:adaptive_learning_app/features/profile/data/dto/student_profile_dto.dart';
import 'package:adaptive_learning_app/features/profile/domain/repository/i_profile_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'profile_event.dart';
part 'profile_state.dart';

class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  ProfileBloc(this._repository) : super(ProfileInitial()) {
    on<ProfileLoadRequested>(_onLoad);
    on<ProfileUpdateRequested>(_onUpdate);
  }

  final IProfileRepository _repository;

  Future<void> _onLoad(ProfileLoadRequested event, Emitter<ProfileState> emit) async {
    emit(ProfileLoading());
    try {
      final profile = await _repository.fetchUserProfile();
      emit(ProfileLoaded(profile));
    } on Object catch (e) {
      emit(ProfileError(e.toString()));
    }
  }

  Future<void> _onUpdate(ProfileUpdateRequested event, Emitter<ProfileState> emit) async {
    emit(ProfileLoading());
    try {
      final updates = {'cognitive_profile': event.cognitive, 'learning_preferences': event.preferences};
      final profile = await _repository.updateUserProfile(updates);
      emit(ProfileLoaded(profile));
    } on Object catch (e) {
      emit(ProfileError("Update failed: $e"));
    }
  }
}
