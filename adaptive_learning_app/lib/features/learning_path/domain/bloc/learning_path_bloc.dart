import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

part 'learning_path_event.dart';
part 'learning_path_state.dart';

class LearningPathBloc extends Bloc<LearningPathEvent, LearningPathState> {
  LearningPathBloc({required ILearningPathRepository repository})
    : _repository = repository,
      super(LearningPathInitial()) {
    on<GeneratePathRequested>(_onGeneratePath);
    on<LearningPathRefreshRequested>(_onRefreshPath);
  }

  final ILearningPathRepository _repository;
  String? _lastGoalId;
  String? _lastStartId;
  String? _currentStudentId;

  Future<void> _onGeneratePath(GeneratePathRequested event, Emitter<LearningPathState> emit) async {
    _lastGoalId = event.goalConceptId;
    _lastStartId = event.startConceptId;
    _currentStudentId = event.studentId;
    await _loadPath(emit);
  }

  Future<void> _onRefreshPath(LearningPathRefreshRequested event, Emitter<LearningPathState> emit) async {
    if (_lastGoalId == null) return;
    _currentStudentId = event.studentId;
    await _loadPath(emit);
  }

  Future<void> _loadPath(Emitter<LearningPathState> emit) async {
    if (_currentStudentId == null) return;
    emit(LearningPathLoading());
    try {
      // The backend (LearningPathService) checks the mastery_level in the ML service for each request,
      // so re-generation will return steps with updated statuses (completed/pending).
      final path = await _repository.generatePath(
        studentId: _currentStudentId!,
        startConceptId: _lastStartId,
        goalConceptId: _lastGoalId!,
      );
      emit(LearningPathSuccess(path));
    } on Object catch (e, st) {
      addError(e, st);
      emit(LearningPathFailure(e.toString()));
    }
  }
}
