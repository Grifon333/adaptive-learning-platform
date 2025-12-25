// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class StepQuizSubmissionDto {
  const StepQuizSubmissionDto({required this.stepId, required this.conceptId, required this.answers});

  final String stepId;
  final String conceptId;
  final Map<String, int> answers; // questionId -> optionIndex

  Map<String, dynamic> toJson() => {'step_id': stepId, 'concept_id': conceptId, 'answers': answers};
}

@immutable
class StepQuizResultDto {
  const StepQuizResultDto({
    required this.passed,
    required this.score,
    required this.message,
    this.adaptationOccurred = false,
  });

  final bool passed;
  final double score;
  final String message;
  final bool adaptationOccurred;

  factory StepQuizResultDto.fromJson(Map<String, dynamic> json) {
    return StepQuizResultDto(
      passed: json['passed'] as bool,
      score: (json['score'] as num).toDouble(),
      message: json['message'] as String,
      adaptationOccurred: json['adaptation_occurred'] as bool? ?? false,
    );
  }
}
