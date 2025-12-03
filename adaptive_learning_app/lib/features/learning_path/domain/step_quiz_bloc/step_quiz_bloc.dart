import 'package:adaptive_learning_app/features/events/service/tracking_service.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/step_quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:meta/meta.dart';

part 'step_quiz_event.dart';
part 'step_quiz_state.dart';

class StepQuizBloc extends Bloc<StepQuizEvent, StepQuizState> {
  StepQuizBloc({required this.repository, required this.trackingService}) : super(StepQuizInitial()) {
    on<LoadQuizRequested>(_onLoad);
    on<QuizAnswerSelected>(_onAnswer);
    on<SubmitQuizRequested>(_onSubmit);
  }

  final ILearningPathRepository repository;
  final TrackingService trackingService;

  Future<void> _onLoad(LoadQuizRequested event, Emitter<StepQuizState> emit) async {
    emit(StepQuizLoading());
    try {
      final questions = await repository.getQuizForConcept(event.conceptId);
      if (questions.isEmpty) {
        emit(const StepQuizFailure("No questions available for this concept."));
      } else {
        trackingService.log('QUIZ_START', metadata: {'conceptId': event.conceptId, 'questionCount': questions.length});
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
        // Log the submission attempt
        trackingService.log(
          'QUIZ_SUBMIT',
          metadata: {'stepId': event.stepId, 'conceptId': event.conceptId, 'answersCount': state.answers.length},
        );

        final submission = StepQuizSubmissionDto(
          stepId: event.stepId,
          conceptId: event.conceptId,
          answers: state.answers,
        );
        final result = await repository.submitStepQuiz(submission);

        // Log completion with result
        trackingService.log(
          'QUIZ_COMPLETE',
          metadata: {'stepId': event.stepId, 'passed': result.passed, 'score': result.score},
        );

        emit(StepQuizSuccess(result));
      } on Object catch (e) {
        emit(StepQuizFailure("Submission failed: $e"));
        emit(state.copyWith(isSubmitting: false));
      }
    }
  }
}
