import 'package:adaptive_learning_app/di/di_base_repository.dart';
import 'package:adaptive_learning_app/features/profile/data/dto/student_profile_dto.dart';

abstract interface class IProfileRepository with DiBaseRepository {
  Future<StudentProfileDto> fetchUserProfile();
  Future<StudentProfileDto> updateUserProfile(Map<String, dynamic> updates);
}
