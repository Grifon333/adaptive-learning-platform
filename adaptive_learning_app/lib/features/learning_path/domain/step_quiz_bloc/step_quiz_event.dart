part of 'step_quiz_bloc.dart';

@immutable
sealed class StepQuizEvent extends Equatable {
  const StepQuizEvent();
  @override
  List<Object?> get props => [];
}

class LoadQuizRequested extends StepQuizEvent {
  const LoadQuizRequested({required this.conceptId});
  final String conceptId;
}

class QuizAnswerSelected extends StepQuizEvent {
  const QuizAnswerSelected({required this.questionId, required this.optionIndex});
  final String questionId;
  final int optionIndex;
  @override
  List<Object?> get props => [questionId, optionIndex];
}

class SubmitQuizRequested extends StepQuizEvent {
  const SubmitQuizRequested({required this.stepId, required this.conceptId});
  final String stepId;
  final String conceptId;
}
