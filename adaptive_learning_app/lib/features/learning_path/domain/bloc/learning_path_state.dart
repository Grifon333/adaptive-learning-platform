part of 'learning_path_bloc.dart';

sealed class LearningPathState extends Equatable {
  const LearningPathState();
  @override
  List<Object?> get props => [];
}

class LearningPathInitial extends LearningPathState {}

class LearningPathLoading extends LearningPathState {}

class LearningPathSuccess extends LearningPathState {
  const LearningPathSuccess(this.path);
  final LearningPathDto path;
  @override
  List<Object?> get props => [path];
}

class LearningPathFailure extends LearningPathState {
  const LearningPathFailure(this.error);
  final String error;
  @override
  List<Object?> get props => [error];
}
