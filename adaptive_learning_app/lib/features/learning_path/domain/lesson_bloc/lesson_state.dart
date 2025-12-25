part of 'lesson_bloc.dart';

@immutable
sealed class LessonState extends Equatable {
  const LessonState();
  @override
  List<Object?> get props => [];
}

class LessonInitial extends LessonState {}

class LessonTracking extends LessonState {
  const LessonTracking({this.totalSecondsTracked = 0});
  final int totalSecondsTracked;
  @override
  List<Object?> get props => [totalSecondsTracked];
}

class LessonCompletionSuccess extends LessonState {
  const LessonCompletionSuccess(this.response);
  final StepCompleteResponseDto response;
}

class LessonFailure extends LessonState {
  const LessonFailure(this.error);
  final String error;
  @override
  List<Object?> get props => [error];
}
