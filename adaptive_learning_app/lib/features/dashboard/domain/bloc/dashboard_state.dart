part of 'dashboard_bloc.dart';

@immutable
sealed class DashboardState extends Equatable {
  const DashboardState();
  @override
  List<Object?> get props => [];
}

final class DashboardInitial extends DashboardState {}

final class DashboardLoading extends DashboardState {}

final class DashboardSuccess extends DashboardState {
  const DashboardSuccess(this.recommendations);
  final List<LearningStepDto> recommendations;
  @override
  List<Object?> get props => [recommendations];
}

final class DashboardFailure extends DashboardState {
  const DashboardFailure(this.error);
  final String error;
  @override
  List<Object?> get props => [error];
}
