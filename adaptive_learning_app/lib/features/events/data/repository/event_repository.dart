import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/events/data/dto/event_dto.dart';
import 'package:adaptive_learning_app/features/events/domain/repository/i_event_repository.dart';

final class EventRepository implements IEventRepository {
  EventRepository({required this.httpClient, required this.appConfig});

  final IHttpClient httpClient;
  final IAppConfig appConfig;

  @override
  String get name => 'EventRepository';

  @override
  Future<void> sendEvent({
    required String studentId,
    required String eventType,
    required Map<String, dynamic> metadata,
  }) async {
    final event = EventDto(eventType: eventType, studentId: studentId, metadata: metadata);
    final serviceUrl = appConfig.eventServiceUrl;
    await httpClient.post('$serviceUrl/events', data: event.toJson());
  }
}
