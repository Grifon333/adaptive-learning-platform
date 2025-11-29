part of 'assessment_bloc.dart';

@immutable
sealed class AssessmentState extends Equatable {
  const AssessmentState();
  @override
  List<Object?> get props => [];
}

class AssessmentInitial extends AssessmentState {}

class AssessmentLoading extends AssessmentState {}

class AssessmentInProgress extends AssessmentState {
  const AssessmentInProgress({required this.session, this.currentQuestionIndex = 0, this.answers = const {}});

  final AssessmentSessionDto session;
  final int currentQuestionIndex;
  final Map<String, int> answers; // questionId -> optionIndex

  @override
  List<Object?> get props => [session, currentQuestionIndex, answers];
}

class AssessmentSuccess extends AssessmentState {
  const AssessmentSuccess(this.path);
  final LearningPathDto path;
}

class AssessmentFailure extends AssessmentState {
  const AssessmentFailure(this.error);
  final String error;
}
