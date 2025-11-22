import 'dart:io';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/events/data/dto/event_dto.dart';
import 'package:adaptive_learning_app/features/events/domain/repository/i_event_repository.dart';

final class EventRepository implements IEventRepository {
  EventRepository({required this.httpClient});

  final IHttpClient httpClient;

  // TODO: Change to real profile ID (through BLoC or Storage)
  final String _studentId = "d3172e75-37c3-4eac-8800-a298f9e61840";

  @override
  String get name => 'EventRepository';

  @override
  Future<void> sendEvent({required String eventType, required Map<String, dynamic> metadata}) async {
    final event = EventDto(eventType: eventType, studentId: _studentId, metadata: metadata);
    final String host = Platform.isAndroid ? '10.0.2.2' : 'localhost';
    final String serviceUrl = 'http://$host:8003';
    await httpClient.post('$serviceUrl/api/v1/events', data: event.toJson());
  }
}
