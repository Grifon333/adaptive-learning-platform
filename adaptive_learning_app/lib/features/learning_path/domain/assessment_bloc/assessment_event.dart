part of 'assessment_bloc.dart';

@immutable
sealed class AssessmentEvent extends Equatable {
  const AssessmentEvent();
  @override
  List<Object?> get props => [];
}

class AssessmentStarted extends AssessmentEvent {
  const AssessmentStarted({required this.studentId, required this.goalConceptId});
  final String studentId;
  final String goalConceptId;
}

class AssessmentAnswered extends AssessmentEvent {
  const AssessmentAnswered({required this.questionId, required this.optionIndex});
  final String questionId;
  final int optionIndex;
}

class AssessmentSubmitted extends AssessmentEvent {}
