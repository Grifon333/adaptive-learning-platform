import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/profile/domain/repository/i_profile_repository.dart';

final class ProfileRepository implements IProfileRepository {
  ProfileRepository({required this.httpClient});
  final IHttpClient httpClient;

  @override
  String get name => 'ProfileRepository';

  @override
  Future<String> fetchUserProfile(String id) async {
    // TODO: Implement actual API call to fetch user profile
    // final response = await httpClient.get('/api/v1/users/me/profile');
    // return ProfileEntity.fromJson(response.data).name;
    await Future.delayed(const Duration(milliseconds: 500));
    return 'Іван Петренко (Студент #$id)';
  }
}
