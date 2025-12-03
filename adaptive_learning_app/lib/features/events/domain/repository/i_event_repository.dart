import 'package:adaptive_learning_app/di/di_base_repository.dart';
import 'package:adaptive_learning_app/features/events/data/dto/event_dto.dart';

abstract interface class IEventRepository with DiBaseRepository {
  Future<void> sendEvent(EventDto event);
  Future<void> sendBatch(List<EventDto> events);
}
