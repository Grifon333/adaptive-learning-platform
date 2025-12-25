part of 'admin_graph_bloc.dart';

@immutable
sealed class AdminGraphState extends Equatable {
  const AdminGraphState();
  @override
  List<Object?> get props => [];
}

class AdminGraphInitial extends AdminGraphState {}

class AdminGraphLoading extends AdminGraphState {}

class AdminGraphLoaded extends AdminGraphState {
  const AdminGraphLoaded(this.concepts);
  final List<AdminConceptDto> concepts;
  @override
  List<Object?> get props => [concepts];
}

class AdminGraphError extends AdminGraphState {
  const AdminGraphError(this.message);
  final String message;
  @override
  List<Object?> get props => [message];
}
