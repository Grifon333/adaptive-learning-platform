import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'dashboard_event.dart';
part 'dashboard_state.dart';

class DashboardBloc extends Bloc<DashboardEvent, DashboardState> {
  DashboardBloc({required ILearningPathRepository repository}) : _repository = repository, super(DashboardInitial()) {
    on<DashboardLoadRequested>(_onLoad);
  }

  final ILearningPathRepository _repository;

  Future<void> _onLoad(DashboardLoadRequested event, Emitter<DashboardState> emit) async {
    emit(DashboardLoading());
    try {
      final recommendations = await _repository.getRecommendations(event.studentId);
      emit(DashboardSuccess(recommendations));
    } on Object catch (e) {
      emit(DashboardFailure(e.toString()));
    }
  }
}
