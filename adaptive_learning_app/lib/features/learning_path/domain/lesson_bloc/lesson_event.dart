part of 'lesson_bloc.dart';

@immutable
sealed class LessonEvent extends Equatable {
  const LessonEvent();
  @override
  List<Object?> get props => [];
}

class LessonStarted extends LessonEvent {}

class LessonTick extends LessonEvent {
  const LessonTick(this.seconds);
  final int seconds;
}

class LessonCompleteRequested extends LessonEvent {}

class LessonStopped extends LessonEvent {}
