import 'package:adaptive_learning_app/di/di_base_repository.dart';

abstract interface class IProfileRepository with DiBaseRepository {
  Future<String> fetchUserProfile(String id);
}
