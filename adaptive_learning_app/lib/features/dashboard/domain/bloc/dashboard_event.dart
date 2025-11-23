part of 'dashboard_bloc.dart';

@immutable
sealed class DashboardEvent extends Equatable {
  const DashboardEvent();
  @override
  List<Object?> get props => [];
}

final class DashboardLoadRequested extends DashboardEvent {
  const DashboardLoadRequested(this.studentId);
  final String studentId;
}
