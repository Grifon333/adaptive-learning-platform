import 'package:adaptive_learning_app/features/profile/domain/repository/i_profile_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'profile_event.dart';
part 'profile_state.dart';

class ProfileBloc extends Bloc<ProfileEvent, ProfileState> {
  ProfileBloc(this._profileRepository) : super(ProfileInitialState()) {
    on<ProfileEvent>((event, emit) async {
      if (event is ProfileFetchProfileEvent) {
        await _fetchProfile(event, emit);
      }
    });
  }

  final IProfileRepository _profileRepository;

  Future<void> _fetchProfile(ProfileFetchProfileEvent event, Emitter<ProfileState> emit) async {
    try {
      emit(ProfileWaitingState());
      final data = await _profileRepository.fetchUserProfile(event.id);
      emit(ProfileSuccessState(data: data));
    } on Object catch (error, stackTrace) {
      emit(ProfileErrorState(message: 'Error loading profile', error: error, stackTrace: stackTrace));
      addError(error, stackTrace);
    }
  }
}
