part of 'profile_bloc.dart';

@immutable
sealed class ProfileEvent extends Equatable {
  const ProfileEvent();
  @override
  List<Object> get props => [];
}

final class ProfileLoadRequested extends ProfileEvent {}

final class ProfileUpdateRequested extends ProfileEvent {
  const ProfileUpdateRequested({required this.cognitive, required this.preferences});
  final Map<String, dynamic> cognitive;
  final Map<String, dynamic> preferences;
  @override
  List<Object> get props => [cognitive, preferences];
}
