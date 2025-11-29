// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class LearningPathRequest {
  const LearningPathRequest({required this.goalConceptId, this.startConceptId});

  final String? startConceptId;
  final String goalConceptId;

  Map<String, dynamic> toJson() {
    final map = {'goal_concept_id': goalConceptId};
    if (startConceptId != null) map['start_concept_id'] = startConceptId!;
    return map;
  }
}

@immutable
class LearningPathDto {
  const LearningPathDto({
    required this.id,
    required this.studentId,
    required this.goalConcepts,
    required this.status,
    required this.completionPercentage,
    required this.steps,
  });

  final String id;
  final String studentId;
  final List<String> goalConcepts;
  final String status;
  final double completionPercentage;
  final List<LearningStepDto> steps;

  factory LearningPathDto.fromJson(Map<String, dynamic> json) {
    return LearningPathDto(
      id: json['id'] as String,
      studentId: json['student_id'] as String,
      goalConcepts: (json['goal_concepts'] as List).map((e) => e as String).toList(),
      status: json['status'] as String,
      completionPercentage: (json['completion_percentage'] as num).toDouble(),
      steps: (json['steps'] as List).map((e) => LearningStepDto.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}

@immutable
class ResourceDto {
  const ResourceDto({
    required this.id,
    required this.title,
    required this.type,
    required this.url,
    required this.duration,
  });

  final String id;
  final String title;
  final String type; // "Video", "Text" etc.
  final String url;
  final int duration;

  factory ResourceDto.fromJson(Map<String, dynamic> json) {
    return ResourceDto(
      id: json['id'] as String,
      title: json['title'] as String,
      type: json['type'] as String,
      url: json['url'] as String,
      duration: (json['duration'] as num).toInt(),
    );
  }
}

@immutable
class LearningStepDto {
  const LearningStepDto({
    required this.id,
    required this.stepNumber,
    required this.conceptId,
    required this.status,
    required this.resources,
    this.estimatedTime,
    this.difficulty,
    this.isRemedial = false,
    this.description,
  });

  final String id;
  final int stepNumber;
  final String conceptId;
  final String status;
  final List<ResourceDto> resources;
  final int? estimatedTime;
  final double? difficulty;
  final bool isRemedial;
  final String? description;

  factory LearningStepDto.fromJson(Map<String, dynamic> json) {
    return LearningStepDto(
      id: json['id'] as String,
      stepNumber: json['step_number'] as int,
      conceptId: json['concept_id'] as String,
      status: json['status'] as String,
      resources: (json['resources'] as List).map((e) => ResourceDto.fromJson(e as Map<String, dynamic>)).toList(),
      estimatedTime: json['estimated_time'] as int?,
      difficulty: (json['difficulty'] as num?)?.toDouble(),
      isRemedial: json['is_remedial'] as bool? ?? false,
      description: json['description'] as String?,
    );
  }
}
