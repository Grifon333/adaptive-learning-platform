part of 'profile_bloc.dart';

@immutable
sealed class ProfileEvent extends Equatable {
  const ProfileEvent();
  @override
  List<Object> get props => [];
}

final class ProfileLoadRequested extends ProfileEvent {}

final class ProfileUpdateRequested extends ProfileEvent {
  const ProfileUpdateRequested({
    this.firstName,
    this.lastName,
    this.avatarUrl,
    this.learningPreferences,
    this.learningGoals,
    this.studySchedule,
    this.timezone,
    this.privacySettings,
    this.cognitiveProfile,
  });

  final String? firstName;
  final String? lastName;
  final String? avatarUrl;
  final Map<String, dynamic>? learningPreferences;
  final List<String>? learningGoals;
  final Map<String, dynamic>? studySchedule;
  final String? timezone;
  final Map<String, dynamic>? privacySettings;
  final Map<String, dynamic>? cognitiveProfile;

  Map<String, dynamic> toUpdateMap() {
    final map = <String, dynamic>{};
    if (firstName != null) map['first_name'] = firstName;
    if (lastName != null) map['last_name'] = lastName;
    if (avatarUrl != null) map['avatar_url'] = avatarUrl;
    if (learningPreferences != null) map['learning_preferences'] = learningPreferences;
    if (learningGoals != null) map['learning_goals'] = learningGoals;
    if (studySchedule != null) map['study_schedule'] = studySchedule;
    if (timezone != null) map['timezone'] = timezone;
    if (privacySettings != null) map['privacy_settings'] = privacySettings;
    return map;
  }
}
