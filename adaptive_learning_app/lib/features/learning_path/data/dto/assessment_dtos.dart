// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class AssessmentSessionDto {
  const AssessmentSessionDto({required this.sessionId, required this.totalQuestions, required this.questions});

  final String sessionId;
  final int totalQuestions;
  final List<AssessmentQuestionDto> questions;

  factory AssessmentSessionDto.fromJson(Map<String, dynamic> json) {
    return AssessmentSessionDto(
      sessionId: json['session_id'] as String,
      totalQuestions: json['total_questions'] as int,
      questions: (json['questions'] as List)
          .map((e) => AssessmentQuestionDto.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

@immutable
class AssessmentQuestionDto {
  const AssessmentQuestionDto({
    required this.id,
    required this.text,
    required this.options,
    required this.conceptId,
    required this.difficulty,
  });

  final String id;
  final String text;
  final List<AssessmentOptionDto> options;
  final String conceptId;
  final double difficulty;

  factory AssessmentQuestionDto.fromJson(Map<String, dynamic> json) {
    return AssessmentQuestionDto(
      id: json['id'] as String,
      text: json['text'] as String,
      options: (json['options'] as List).map((e) => AssessmentOptionDto.fromJson(e as Map<String, dynamic>)).toList(),
      conceptId: json['concept_id'] as String,
      difficulty: (json['difficulty'] as num).toDouble(),
    );
  }
}

@immutable
class AssessmentOptionDto {
  const AssessmentOptionDto({required this.text});

  final String text;

  factory AssessmentOptionDto.fromJson(Map<String, dynamic> json) {
    return AssessmentOptionDto(text: json['text'] as String);
  }
}

@immutable
class AssessmentSubmissionDto {
  const AssessmentSubmissionDto({required this.studentId, required this.goalConceptId, required this.answers});

  final String studentId;
  final String goalConceptId;
  final Map<String, int> answers;

  Map<String, dynamic> toJson() => {'student_id': studentId, 'goal_concept_id': goalConceptId, 'answers': answers};
}
