part of 'adaptive_assessment_bloc.dart';

@immutable
sealed class AdaptiveAssessmentEvent extends Equatable {
  const AdaptiveAssessmentEvent();
  @override
  List<Object?> get props => [];
}

class AdaptiveAssessmentStarted extends AdaptiveAssessmentEvent {
  const AdaptiveAssessmentStarted({required this.studentId, required this.goalConceptId});
  final String studentId;
  final String goalConceptId;
}

class AdaptiveAssessmentAnswerSubmitted extends AdaptiveAssessmentEvent {
  const AdaptiveAssessmentAnswerSubmitted(this.answerIndex);
  final int answerIndex;
}
