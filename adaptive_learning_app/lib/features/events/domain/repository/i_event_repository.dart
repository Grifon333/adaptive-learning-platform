import 'package:adaptive_learning_app/di/di_base_repository.dart';

abstract interface class IEventRepository with DiBaseRepository {
  Future<void> sendEvent({required String eventType, required Map<String, dynamic> metadata});
}
