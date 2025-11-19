import 'package:flutter/foundation.dart';

@immutable
class EventDto {
  const EventDto({required this.eventType, required this.studentId, required this.metadata});

  final String eventType;
  final String studentId;
  final Map<String, dynamic> metadata;

  Map<String, dynamic> toJson() => {'event_type': eventType, 'student_id': studentId, 'metadata': metadata};
}
