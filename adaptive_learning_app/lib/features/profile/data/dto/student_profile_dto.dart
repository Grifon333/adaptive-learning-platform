// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class StudentProfileDto {
  const StudentProfileDto({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.role,
    this.avatarUrl,
    this.cognitiveProfile = const {},
    this.learningPreferences = const {},
    this.learningGoals = const [],
    this.studySchedule = const {},
    this.timezone,
    this.privacySettings = const {},
  });

  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String role;
  final String? avatarUrl;
  final Map<String, dynamic> cognitiveProfile;
  final Map<String, dynamic> learningPreferences;
  final List<String> learningGoals;
  final Map<String, dynamic> studySchedule;
  final String? timezone;
  final Map<String, dynamic> privacySettings;

  String get fullName => '$firstName $lastName';

  factory StudentProfileDto.fromJson(Map<String, dynamic> json) {
    return StudentProfileDto(
      id: json['id'] as String,
      email: json['email'] as String? ?? '', // Fallback for safety
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      role: json['role'] as String? ?? 'student',
      avatarUrl: json['avatar_url'] as String?,
      cognitiveProfile: json['cognitive_profile'] as Map<String, dynamic>? ?? {},
      learningPreferences: json['learning_preferences'] as Map<String, dynamic>? ?? {},
      learningGoals: (json['learning_goals'] as List?)?.map((e) => e as String).toList() ?? [],
      studySchedule: json['study_schedule'] as Map<String, dynamic>? ?? {},
      timezone: json['timezone'] as String?,
      privacySettings: json['privacy_settings'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'first_name': firstName,
    'last_name': lastName,
    'avatar_url': avatarUrl,
    'learning_preferences': learningPreferences,
    'learning_goals': learningGoals,
    'study_schedule': studySchedule,
    'timezone': timezone,
    'privacy_settings': privacySettings,
  };
}
