part of 'learning_path_bloc.dart';

sealed class LearningPathEvent extends Equatable {
  const LearningPathEvent();
  @override
  List<Object?> get props => [];
}

class GeneratePathRequested extends LearningPathEvent {
  const GeneratePathRequested({required this.startConceptId, required this.goalConceptId});

  final String startConceptId;
  final String goalConceptId;

  @override
  List<Object?> get props => [startConceptId, goalConceptId];
}
