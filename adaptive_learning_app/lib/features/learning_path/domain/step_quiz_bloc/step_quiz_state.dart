part of 'step_quiz_bloc.dart';

@immutable
sealed class StepQuizState extends Equatable {
  const StepQuizState();
  @override
  List<Object?> get props => [];
}

class StepQuizInitial extends StepQuizState {}

class StepQuizLoading extends StepQuizState {}

class StepQuizLoaded extends StepQuizState {
  const StepQuizLoaded({required this.questions, this.answers = const {}, this.isSubmitting = false});

  final List<QuizQuestionDto> questions;
  final Map<String, int> answers;
  final bool isSubmitting;

  @override
  List<Object?> get props => [questions, answers, isSubmitting];

  StepQuizLoaded copyWith({List<QuizQuestionDto>? questions, Map<String, int>? answers, bool? isSubmitting}) {
    return StepQuizLoaded(
      questions: questions ?? this.questions,
      answers: answers ?? this.answers,
      isSubmitting: isSubmitting ?? this.isSubmitting,
    );
  }
}

class StepQuizSuccess extends StepQuizState {
  const StepQuizSuccess(this.result);
  final StepQuizResultDto result;
  @override
  List<Object?> get props => [result];
}

class StepQuizFailure extends StepQuizState {
  const StepQuizFailure(this.error);
  final String error;
  @override
  List<Object?> get props => [error];
}
