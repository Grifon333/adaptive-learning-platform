part of 'learning_path_bloc.dart';

sealed class LearningPathEvent extends Equatable {
  const LearningPathEvent();
  @override
  List<Object?> get props => [];
}

class GeneratePathRequested extends LearningPathEvent {
  const GeneratePathRequested({required this.goalConceptId, this.startConceptId});

  final String? startConceptId;
  final String goalConceptId;

  @override
  List<Object?> get props => [startConceptId, goalConceptId];
}

class LearningPathRefreshRequested extends LearningPathEvent {}
