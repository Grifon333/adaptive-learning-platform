import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/step_quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'step_quiz_event.dart';
part 'step_quiz_state.dart';

class StepQuizBloc extends Bloc<StepQuizEvent, StepQuizState> {
  StepQuizBloc({required this.repository}) : super(StepQuizInitial()) {
    on<LoadQuizRequested>(_onLoad);
    on<QuizAnswerSelected>(_onAnswer);
    on<SubmitQuizRequested>(_onSubmit);
  }

  final ILearningPathRepository repository;

  Future<void> _onLoad(LoadQuizRequested event, Emitter<StepQuizState> emit) async {
    emit(StepQuizLoading());
    try {
      final questions = await repository.getQuizForConcept(event.conceptId);
      if (questions.isEmpty) {
        emit(const StepQuizFailure("No questions available for this concept."));
      } else {
        emit(StepQuizLoaded(questions: questions));
      }
    } on Object catch (e) {
      emit(StepQuizFailure("Failed to load quiz: $e"));
    }
  }

  void _onAnswer(QuizAnswerSelected event, Emitter<StepQuizState> emit) {
    final state = this.state;
    if (state is StepQuizLoaded) {
      final newAnswers = Map<String, int>.from(state.answers);
      newAnswers[event.questionId] = event.optionIndex;
      emit(state.copyWith(answers: newAnswers));
    }
  }

  Future<void> _onSubmit(SubmitQuizRequested event, Emitter<StepQuizState> emit) async {
    final state = this.state;
    if (state is StepQuizLoaded) {
      emit(state.copyWith(isSubmitting: true));
      try {
        final submission = StepQuizSubmissionDto(
          stepId: event.stepId,
          conceptId: event.conceptId,
          answers: state.answers,
        );
        final result = await repository.submitStepQuiz(submission);
        emit(StepQuizSuccess(result));
      } on Object catch (e) {
        emit(StepQuizFailure("Submission failed: $e"));
        // Revert to loaded state (without submitting flag) to allow retry
        emit(state.copyWith(isSubmitting: false));
      }
    }
  }
}
