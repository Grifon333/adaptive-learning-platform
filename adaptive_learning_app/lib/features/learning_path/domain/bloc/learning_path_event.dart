part of 'learning_path_bloc.dart';

sealed class LearningPathEvent extends Equatable {
  const LearningPathEvent();
  @override
  List<Object?> get props => [];
}

class GeneratePathRequested extends LearningPathEvent {
  const GeneratePathRequested({required this.studentId, required this.goalConceptId, this.startConceptId});

  final String studentId;
  final String? startConceptId;
  final String goalConceptId;

  @override
  List<Object?> get props => [studentId, startConceptId, goalConceptId];
}

class LearningPathRefreshRequested extends LearningPathEvent {
  const LearningPathRefreshRequested(this.studentId);
  final String studentId;
}

class SelectExistingPath extends LearningPathEvent {
  const SelectExistingPath(this.path);
  final LearningPathDto path;
  @override
  List<Object?> get props => [path];
}
