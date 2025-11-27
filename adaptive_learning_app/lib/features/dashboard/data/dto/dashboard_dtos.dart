// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class DashboardDataDto {
  const DashboardDataDto({
    required this.studentId,
    required this.averageMastery,
    required this.totalConceptsLearned,
    required this.currentStreak,
    required this.weakestConcepts,
    required this.activityChart,
  });

  final String studentId;
  final double averageMastery;
  final int totalConceptsLearned;
  final int currentStreak;
  final List<WeaknessItemDto> weakestConcepts;
  final List<ActivityPointDto> activityChart;

  factory DashboardDataDto.fromJson(Map<String, dynamic> json) {
    return DashboardDataDto(
      studentId: json['student_id'] as String,
      averageMastery: (json['average_mastery'] as num).toDouble(),
      totalConceptsLearned: json['total_concepts_learned'] as int,
      currentStreak: json['current_streak'] as int,
      weakestConcepts: (json['weakest_concepts'] as List)
          .map((e) => WeaknessItemDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      activityChart: (json['activity_last_7_days'] as List)
          .map((e) => ActivityPointDto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

@immutable
class WeaknessItemDto {
  const WeaknessItemDto({required this.conceptId, required this.masteryLevel});

  final String conceptId;
  final double masteryLevel;

  factory WeaknessItemDto.fromJson(Map<String, dynamic> json) {
    return WeaknessItemDto(
      conceptId: json['concept_id'] as String,
      masteryLevel: (json['mastery_level'] as num).toDouble(),
    );
  }
}

@immutable
class ActivityPointDto {
  const ActivityPointDto({required this.date, required this.count});

  final String date;
  final int count;

  factory ActivityPointDto.fromJson(Map<String, dynamic> json) {
    return ActivityPointDto(date: json['date'] as String, count: json['count'] as int);
  }
}
