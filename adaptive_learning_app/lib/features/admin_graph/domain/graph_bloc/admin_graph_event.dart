part of 'admin_graph_bloc.dart';

@immutable
sealed class AdminGraphEvent extends Equatable {
  const AdminGraphEvent();
  @override
  List<Object?> get props => [];
}

class LoadGraphRequested extends AdminGraphEvent {}

class CreateConceptRequested extends AdminGraphEvent {
  const CreateConceptRequested(this.name, this.description, this.difficulty, this.time);
  final String name;
  final String description;
  final double difficulty;
  final int time;
  @override
  List<Object?> get props => [name, description, difficulty, time];
}

class UpdateConceptRequested extends AdminGraphEvent {
  const UpdateConceptRequested(this.id, this.changes);
  final String id;
  final AdminConceptDto changes;
  @override
  List<Object?> get props => [id, changes];
}

class DeleteConceptRequested extends AdminGraphEvent {
  const DeleteConceptRequested(this.id);
  final String id;
}

class CreateLinkRequested extends AdminGraphEvent {
  const CreateLinkRequested(this.startId, this.endId);
  final String startId;
  final String endId;
  @override
  List<Object?> get props => [startId, endId];
}
