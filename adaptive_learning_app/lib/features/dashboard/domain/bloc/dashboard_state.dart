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
  const DashboardSuccess({required this.recommendations, required this.analytics});
  final List<LearningStepDto> recommendations;
  final DashboardDataDto analytics;
  @override
  List<Object?> get props => [recommendations, analytics];
}

final class DashboardFailure extends DashboardState {
  const DashboardFailure(this.error);
  final String error;
  @override
  List<Object?> get props => [error];
}
