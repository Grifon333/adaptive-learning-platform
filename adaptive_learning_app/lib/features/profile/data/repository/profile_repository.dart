import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/profile/data/dto/student_profile_dto.dart';
import 'package:adaptive_learning_app/features/profile/domain/repository/i_profile_repository.dart';

final class ProfileRepository implements IProfileRepository {
  ProfileRepository({required this.httpClient});
  final IHttpClient httpClient;

  @override
  String get name => 'ProfileRepository';

  @override
  Future<StudentProfileDto> fetchUserProfile() async {
    final response = await httpClient.get('/users/me/profile');
    return StudentProfileDto.fromJson(response.data);
  }

  @override
  Future<StudentProfileDto> updateUserProfile(Map<String, dynamic> updates) async {
    final response = await httpClient.put('/users/me/profile', data: updates);
    return StudentProfileDto.fromJson(response.data);
  }
}
