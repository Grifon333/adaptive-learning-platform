import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
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
    on<SelectExistingPath>(_onSelectPath);
  }

  final ILearningPathRepository _repository;
  String? _lastGoalId;
  String? _lastStartId;
  String? _currentStudentId;
  Map<String, ConceptDto>? _cachedConcepts;

  Future<Map<String, ConceptDto>> _getConceptMap() async {
    if (_cachedConcepts != null) return _cachedConcepts!;
    try {
      final concepts = await _repository.getConcepts();
      _cachedConcepts = {for (final c in concepts) c.id: c};
      return _cachedConcepts!;
    } on Object catch (_) {
      return {};
    }
  }

  Future<void> _onGeneratePath(GeneratePathRequested event, Emitter<LearningPathState> emit) async {
    _lastGoalId = event.goalConceptId;
    _lastStartId = event.startConceptId;
    _currentStudentId = event.studentId;
    await _loadPath(emit);
  }

  Future<void> _onRefreshPath(LearningPathRefreshRequested event, Emitter<LearningPathState> emit) async {
    if (_lastGoalId == null && state is LearningPathSuccess) {
      // If we are just refreshing an existing path without goal args
      final currentPath = (state as LearningPathSuccess).path;
      _lastGoalId = currentPath.goalConcepts.first;
      _currentStudentId = currentPath.studentId;
    }
    if (_currentStudentId == null) return;
    await _loadPath(emit);
  }

  Future<void> _loadPath(Emitter<LearningPathState> emit) async {
    if (_currentStudentId == null) return;
    emit(LearningPathLoading());
    try {
      // The backend (LearningPathService) checks the mastery_level in the ML service for each request,
      // so re-generation will return steps with updated statuses (completed/pending).

      // Fetch Path and Concepts in parallel
      final results = await Future.wait([
        _repository.generatePath(
          studentId: _currentStudentId!,
          startConceptId: _lastStartId,
          goalConceptId: _lastGoalId!,
        ),
        _getConceptMap(),
      ]);

      final path = results[0] as LearningPathDto;
      final concepts = results[1] as Map<String, ConceptDto>;

      emit(LearningPathSuccess(path: path, conceptMap: concepts));
    } on Object catch (e, st) {
      addError(e, st);
      emit(LearningPathFailure(e.toString()));
    }
  }

  Future<void> _onSelectPath(SelectExistingPath event, Emitter<LearningPathState> emit) async {
    _lastGoalId = event.path.goalConcepts.firstOrNull;
    _currentStudentId = event.path.studentId;

    emit(LearningPathLoading());
    // We still need concepts for the selected path
    final concepts = await _getConceptMap();

    emit(LearningPathSuccess(path: event.path, conceptMap: concepts));
  }
}
