import 'package:adaptive_learning_app/features/learning_path/data/dto/assessment_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'assessment_event.dart';
part 'assessment_state.dart';

class AssessmentBloc extends Bloc<AssessmentEvent, AssessmentState> {
  AssessmentBloc({required ILearningPathRepository repository}) : _repository = repository, super(AssessmentInitial()) {
    on<AssessmentStarted>(_onStarted);
    on<AssessmentAnswered>(_onAnswered);
    on<AssessmentSubmitted>(_onSubmitted);
  }

  final ILearningPathRepository _repository;
  String? _studentId;
  String? _goalConceptId;

  Future<void> _onStarted(AssessmentStarted event, Emitter<AssessmentState> emit) async {
    emit(AssessmentLoading());
    _studentId = event.studentId;
    _goalConceptId = event.goalConceptId;
    try {
      final session = await _repository.startAssessment(studentId: event.studentId, goalConceptId: event.goalConceptId);
      if (session.questions.isEmpty) {
        emit(const AssessmentFailure("No questions available for this topic."));
      } else {
        emit(AssessmentInProgress(session: session));
      }
    } on Object catch (e) {
      emit(AssessmentFailure(e.toString()));
    }
  }

  void _onAnswered(AssessmentAnswered event, Emitter<AssessmentState> emit) {
    final state = this.state;
    if (state is AssessmentInProgress) {
      final newAnswers = Map<String, int>.from(state.answers);
      newAnswers[event.questionId] = event.optionIndex;

      // Move to next question or stay if it was the last one (UI handles the 'Submit' button)
      emit(
        AssessmentInProgress(
          session: state.session,
          currentQuestionIndex: state.currentQuestionIndex,
          answers: newAnswers,
        ),
      );
    }
  }

  Future<void> _onSubmitted(AssessmentSubmitted event, Emitter<AssessmentState> emit) async {
    final state = this.state;
    if (state is AssessmentInProgress && _studentId != null && _goalConceptId != null) {
      emit(AssessmentLoading());
      try {
        final dto = AssessmentSubmissionDto(
          studentId: _studentId!,
          goalConceptId: _goalConceptId!,
          answers: state.answers,
        );
        final path = await _repository.submitAssessment(dto);
        emit(AssessmentSuccess(path));
      } on Object catch (e) {
        emit(AssessmentFailure(e.toString()));
      }
    }
  }
}
