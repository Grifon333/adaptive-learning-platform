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
  Future<void> sendEvent(EventDto event) async {
    final serviceUrl = appConfig.eventServiceUrl;
    await httpClient.post('$serviceUrl/events', data: event.toJson());
  }

  @override
  Future<void> sendBatch(List<EventDto> events) async {
    if (events.isEmpty) return;
    final serviceUrl = appConfig.eventServiceUrl;
    final payload = {'events': events.map((e) => e.toJson()).toList()};
    await httpClient.post('$serviceUrl/events/batch', data: payload);
  }
}
