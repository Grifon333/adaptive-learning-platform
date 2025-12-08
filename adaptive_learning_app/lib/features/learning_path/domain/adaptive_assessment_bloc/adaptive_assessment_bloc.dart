import 'package:adaptive_learning_app/features/learning_path/data/dto/adaptive_assessment_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'adaptive_assessment_event.dart';
part 'adaptive_assessment_state.dart';

class AdaptiveAssessmentBloc extends Bloc<AdaptiveAssessmentEvent, AdaptiveAssessmentState> {
  AdaptiveAssessmentBloc({required ILearningPathRepository repository})
    : _repository = repository,
      super(AdaptiveAssessmentInitial()) {
    on<AdaptiveAssessmentStarted>(_onStarted);
    on<AdaptiveAssessmentAnswerSubmitted>(_onSubmitted);
  }

  final ILearningPathRepository _repository;

  Future<void> _onStarted(AdaptiveAssessmentStarted event, Emitter<AdaptiveAssessmentState> emit) async {
    emit(AdaptiveAssessmentLoading());
    try {
      final response = await _repository.startAdaptiveAssessment(
        studentId: event.studentId,
        goalConceptId: event.goalConceptId,
      );

      if (response.completed) {
        // Edge case: Test completed immediately (unlikely but possible)
        emit(AdaptiveAssessmentSuccess(finalMastery: response.finalMastery ?? 0.0, message: response.message));
      } else {
        emit(AdaptiveAssessmentInProgress(sessionState: response.sessionState));
      }
    } on Object catch (e) {
      emit(AdaptiveAssessmentFailure(e.toString()));
    }
  }

  Future<void> _onSubmitted(AdaptiveAssessmentAnswerSubmitted event, Emitter<AdaptiveAssessmentState> emit) async {
    final currentState = state;
    if (currentState is AdaptiveAssessmentInProgress) {
      // Optimistic UI or Loading indicator
      emit(
        AdaptiveAssessmentInProgress(
          sessionState: currentState.sessionState,
          questionNumber: currentState.questionNumber,
          isSubmitting: true,
        ),
      );

      try {
        final response = await _repository.submitAdaptiveAnswer(
          sessionState: currentState.sessionState,
          answerIndex: event.answerIndex,
        );

        if (response.completed) {
          emit(AdaptiveAssessmentSuccess(finalMastery: response.finalMastery ?? 0.0, message: response.message));
        } else {
          emit(
            AdaptiveAssessmentInProgress(
              sessionState: response.sessionState,
              questionNumber: currentState.questionNumber + 1,
            ),
          );
        }
      } on Object catch (e) {
        emit(AdaptiveAssessmentFailure(e.toString()));
      }
    }
  }
}
