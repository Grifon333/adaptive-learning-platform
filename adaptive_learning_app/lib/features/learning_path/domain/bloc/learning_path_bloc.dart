import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'learning_path_event.dart';
part 'learning_path_state.dart';

class LearningPathBloc extends Bloc<LearningPathEvent, LearningPathState> {
  LearningPathBloc({required ILearningPathRepository repository})
    : _repository = repository,
      super(LearningPathInitial()) {
    on<GeneratePathRequested>(_onGeneratePath);
  }

  final ILearningPathRepository _repository;
  // TODO: Replace with actual student ID retrieval logic
  final String _studentId = "dummy-student-id";

  Future<void> _onGeneratePath(GeneratePathRequested event, Emitter<LearningPathState> emit) async {
    emit(LearningPathLoading());
    try {
      final path = await _repository.generatePath(
        studentId: _studentId,
        startConceptId: event.startConceptId,
        goalConceptId: event.goalConceptId,
      );
      emit(LearningPathSuccess(path));
    } on Object catch (e, st) {
      addError(e, st);
      emit(LearningPathFailure(e.toString()));
    }
  }
}
