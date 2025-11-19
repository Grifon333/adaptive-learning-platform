import 'package:flutter/foundation.dart';

@immutable
class LearningPathRequest {
  const LearningPathRequest({required this.startConceptId, required this.goalConceptId});

  final String startConceptId;
  final String goalConceptId;

  Map<String, dynamic> toJson() => {'start_concept_id': startConceptId, 'goal_concept_id': goalConceptId};
}

@immutable
class LearningPathDto {
  const LearningPathDto({
    required this.id,
    required this.status,
    required this.completionPercentage,
    required this.steps,
  });

  final String id;
  final String status;
  final double completionPercentage;
  final List<LearningStepDto> steps;

  factory LearningPathDto.fromJson(Map<String, dynamic> json) {
    return LearningPathDto(
      id: json['id'] as String,
      status: json['status'] as String,
      completionPercentage: (json['completion_percentage'] as num).toDouble(),
      steps: (json['steps'] as List).map((e) => LearningStepDto.fromJson(e as Map<String, dynamic>)).toList(),
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
    required this.resourceIds,
    this.estimatedTime,
    this.difficulty,
  });

  final String id;
  final int stepNumber;
  final String conceptId;
  final String status;
  final List<String> resourceIds;
  final int? estimatedTime;
  final double? difficulty;

  factory LearningStepDto.fromJson(Map<String, dynamic> json) {
    return LearningStepDto(
      id: json['id'] as String,
      stepNumber: json['step_number'] as int,
      conceptId: json['concept_id'] as String,
      status: json['status'] as String,
      resourceIds: (json['resource_ids'] as List).map((e) => e as String).toList(),
      estimatedTime: json['estimated_time'] as int?,
      difficulty: (json['difficulty'] as num?)?.toDouble(),
    );
  }
}
