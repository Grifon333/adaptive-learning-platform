part of 'profile_bloc.dart';

@immutable
sealed class ProfileState extends Equatable {
  const ProfileState();
  @override
  List<Object> get props => [];
}

final class ProfileInitial extends ProfileState {}

final class ProfileLoading extends ProfileState {}

final class ProfileLoaded extends ProfileState {
  const ProfileLoaded(this.profile);
  final StudentProfileDto profile;
  @override
  List<Object> get props => [profile];
}

final class ProfileError extends ProfileState {
  const ProfileError(this.message);
  final String message;
  @override
  List<Object> get props => [message];
}
