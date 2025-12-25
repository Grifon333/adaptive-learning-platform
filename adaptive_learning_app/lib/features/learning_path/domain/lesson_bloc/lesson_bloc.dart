import 'dart:async';

import 'package:adaptive_learning_app/features/learning_path/data/dto/step_complete_response_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'lesson_event.dart';
part 'lesson_state.dart';

class LessonBloc extends Bloc<LessonEvent, LessonState> {
  LessonBloc({required this.repository, required this.stepId}) : super(LessonInitial()) {
    on<LessonStarted>(_onStarted);
    on<LessonTick>(_onTick);
    on<LessonCompleteRequested>(_onComplete);
    on<LessonStopped>(_onStopped);
  }

  final ILearningPathRepository repository;
  final String stepId;
  Timer? _timer;
  static const int _heartbeatInterval = 30; // Seconds

  Future<void> _onStarted(LessonStarted event, Emitter<LessonState> emit) async {
    emit(const LessonTracking());
    _startTimer();
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: _heartbeatInterval), (_) {
      add(const LessonTick(_heartbeatInterval));
    });
  }

  Future<void> _onTick(LessonTick event, Emitter<LessonState> emit) async {
    if (state is LessonTracking) {
      final current = (state as LessonTracking).totalSecondsTracked;
      emit(LessonTracking(totalSecondsTracked: current + event.seconds));

      // Fire and forget heartbeat to avoid blocking UI or state
      try {
        await repository.updateStepProgress(stepId, event.seconds);
      } on Object catch (_) {
        // Log error silently, don't crash lesson
        // debugPrint('Heartbeat failed: $e');
      }
    }
  }

  Future<void> _onComplete(LessonCompleteRequested event, Emitter<LessonState> emit) async {
    _timer?.cancel();
    try {
      final result = await repository.completeStep(stepId);
      emit(LessonCompletionSuccess(result));
    } on Object catch (e) {
      emit(LessonFailure(e.toString()));
      // Resume timer if failed? Or let user retry manually.
    }
  }

  void _onStopped(LessonStopped event, Emitter<LessonState> emit) {
    _timer?.cancel();
  }

  @override
  Future<void> close() {
    _timer?.cancel();
    return super.close();
  }
}
