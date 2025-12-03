// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class EventDto {
  const EventDto({required this.eventType, required this.studentId, required this.metadata, required this.timestamp});

  final String eventType;
  final String studentId;
  final Map<String, dynamic> metadata;
  final DateTime timestamp;

  Map<String, dynamic> toJson() => {
    'event_type': eventType,
    'student_id': studentId,
    'metadata': metadata,
    'timestamp': timestamp.toIso8601String(),
  };

  factory EventDto.fromJson(Map<String, dynamic> json) {
    return EventDto(
      eventType: json['event_type'] as String,
      studentId: json['student_id'] as String,
      metadata: json['metadata'] as Map<String, dynamic>,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}
