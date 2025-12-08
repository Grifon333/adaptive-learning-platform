part of 'adaptive_assessment_bloc.dart';

@immutable
sealed class AdaptiveAssessmentState extends Equatable {
  const AdaptiveAssessmentState();
  @override
  List<Object?> get props => [];
}

class AdaptiveAssessmentInitial extends AdaptiveAssessmentState {}

class AdaptiveAssessmentLoading extends AdaptiveAssessmentState {}

class AdaptiveAssessmentInProgress extends AdaptiveAssessmentState {
  const AdaptiveAssessmentInProgress({required this.sessionState, this.questionNumber = 1, this.isSubmitting = false});

  final AdaptiveSessionStateDto sessionState;
  final int questionNumber;
  final bool isSubmitting;

  @override
  List<Object?> get props => [sessionState, questionNumber, isSubmitting];
}

class AdaptiveAssessmentSuccess extends AdaptiveAssessmentState {
  const AdaptiveAssessmentSuccess({required this.finalMastery, this.message});
  final double finalMastery;
  final String? message;

  @override
  List<Object?> get props => [finalMastery, message];
}

class AdaptiveAssessmentFailure extends AdaptiveAssessmentState {
  const AdaptiveAssessmentFailure(this.error);
  final String error;
  @override
  List<Object?> get props => [error];
}
