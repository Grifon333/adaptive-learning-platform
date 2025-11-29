import 'package:adaptive_learning_app/features/dashboard/data/dto/dashboard_dtos.dart';
import 'package:adaptive_learning_app/features/dashboard/domain/repository/i_analytics_repository.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'dashboard_event.dart';
part 'dashboard_state.dart';

class DashboardBloc extends Bloc<DashboardEvent, DashboardState> {
  DashboardBloc({required ILearningPathRepository lpRepository, required IAnalyticsRepository analyticsRepository})
    : _lpRepository = lpRepository,
      _analyticsRepository = analyticsRepository,
      super(DashboardInitial()) {
    on<DashboardLoadRequested>(_onLoad);
  }

  final ILearningPathRepository _lpRepository;
  final IAnalyticsRepository _analyticsRepository;

  Future<void> _onLoad(DashboardLoadRequested event, Emitter<DashboardState> emit) async {
    emit(DashboardLoading());
    try {
      // Execute requests in parallel for speed
      final results = await Future.wait([
        _lpRepository.getRecommendations(event.studentId),
        _analyticsRepository.getDashboardData(event.studentId),
      ]);

      final recommendations = results[0] as List<LearningStepDto>;
      final analytics = results[1] as DashboardDataDto;

      emit(DashboardSuccess(recommendations: recommendations, analytics: analytics));
    } on Object catch (e) {
      emit(DashboardFailure(e.toString()));
    }
  }
}
