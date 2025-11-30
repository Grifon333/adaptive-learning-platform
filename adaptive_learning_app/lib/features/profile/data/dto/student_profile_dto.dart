// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class StudentProfileDto {
  const StudentProfileDto({
    required this.id,
    required this.userId,
    required this.cognitiveProfile,
    required this.learningPreferences,
  });

  final String id;
  final String userId;
  final Map<String, dynamic> cognitiveProfile;
  final Map<String, dynamic> learningPreferences;

  factory StudentProfileDto.fromJson(Map<String, dynamic> json) {
    return StudentProfileDto(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      cognitiveProfile: json['cognitive_profile'] as Map<String, dynamic>? ?? {},
      learningPreferences: json['learning_preferences'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() => {'cognitive_profile': cognitiveProfile, 'learning_preferences': learningPreferences};
}
