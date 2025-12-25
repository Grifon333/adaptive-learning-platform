// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class AdaptiveAssessmentResponseDto {
  const AdaptiveAssessmentResponseDto({
    required this.sessionState,
    required this.completed,
    this.finalMastery,
    this.message,
  });

  final AdaptiveSessionStateDto sessionState;
  final bool completed;
  final double? finalMastery;
  final String? message;

  factory AdaptiveAssessmentResponseDto.fromJson(Map<String, dynamic> json) {
    return AdaptiveAssessmentResponseDto(
      sessionState: AdaptiveSessionStateDto.fromJson(json['session_state'] as Map<String, dynamic>),
      completed: json['completed'] as bool,
      finalMastery: (json['final_mastery'] as num?)?.toDouble(),
      message: json['message'] as String?,
    );
  }
}

@immutable
class AdaptiveSessionStateDto {
  const AdaptiveSessionStateDto({
    required this.studentId,
    required this.history,
    this.goalConceptId,
    this.currentQuestion,
    // We keep extra fields in a map to ensure we don't lose data required by the backend
    this.extraData = const {},
  });

  final String studentId;
  final String? goalConceptId;
  final List<dynamic> history;
  final AdaptiveQuestionDto? currentQuestion;
  final Map<String, dynamic> extraData;

  factory AdaptiveSessionStateDto.fromJson(Map<String, dynamic> json) {
    // Extract known fields
    final studentId = json['student_id'] as String;
    final goalConceptId = json['goal_concept_id'] as String?;
    final history = json['history'] as List? ?? [];
    final currentQuestion = json['current_question'] != null
        ? AdaptiveQuestionDto.fromJson(json['current_question'] as Map<String, dynamic>)
        : null;

    // Remove known fields to store the rest as extraData
    final extra = Map<String, dynamic>.from(json)
      ..remove('student_id')
      ..remove('goal_concept_id')
      ..remove('history')
      ..remove('current_question');

    return AdaptiveSessionStateDto(
      studentId: studentId,
      goalConceptId: goalConceptId,
      history: history,
      currentQuestion: currentQuestion,
      extraData: extra,
    );
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{'student_id': studentId, 'history': history, ...extraData};
    if (goalConceptId != null) map['goal_concept_id'] = goalConceptId;
    if (currentQuestion != null) map['current_question'] = currentQuestion!.toJson();
    return map;
  }
}

@immutable
class AdaptiveQuestionDto {
  const AdaptiveQuestionDto({
    required this.id,
    required this.text,
    required this.options,
    required this.difficulty,
    required this.conceptId,
  });

  final String id;
  final String text;
  final List<AdaptiveOptionDto> options;
  final double difficulty;
  final String conceptId;

  factory AdaptiveQuestionDto.fromJson(Map<String, dynamic> json) {
    return AdaptiveQuestionDto(
      id: json['id'] as String,
      text: json['text'] as String,
      options: (json['options'] as List).map((e) => AdaptiveOptionDto.fromJson(e as Map<String, dynamic>)).toList(),
      difficulty: (json['difficulty'] as num).toDouble(),
      conceptId: json['concept_id'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'text': text,
    'options': options.map((e) => e.toJson()).toList(),
    'difficulty': difficulty,
    'concept_id': conceptId,
  };
}

@immutable
class AdaptiveOptionDto {
  const AdaptiveOptionDto({required this.text, this.id});

  final int? id; // Sometimes index, sometimes ID
  final String text;

  factory AdaptiveOptionDto.fromJson(Map<String, dynamic> json) {
    return AdaptiveOptionDto(id: json['id'] as int?, text: json['text'] as String);
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{'text': text};
    if (id != null) map['id'] = id;
    return map;
  }
}
