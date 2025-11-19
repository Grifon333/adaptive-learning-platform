import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/di/di_typedefs.dart';
import 'package:adaptive_learning_app/features/auth/data/repository/auth_repository.dart';
import 'package:adaptive_learning_app/features/auth/domain/repository/i_auth_repository.dart';
import 'package:adaptive_learning_app/features/events/data/repository/event_repository.dart';
import 'package:adaptive_learning_app/features/events/domain/repository/i_event_repository.dart';
import 'package:adaptive_learning_app/features/learning_path/data/repository/learning_path_repository.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:adaptive_learning_app/features/profile/data/repository/profile_repository.dart';
import 'package:adaptive_learning_app/features/profile/domain/repository/i_profile_repository.dart';

/// {@template di_repositories}
/// Class for initiating and managing application repositories.
/// {@endtemplate}
final class DiRepositories {
  DiRepositories();

  late final IAuthRepository authRepository;
  late final ILearningPathRepository learningPathRepository;
  late final IEventRepository eventRepository;
  late final IProfileRepository profileRepository;

  void init({required OnProgress onProgress, required OnError onError, required DiContainer diContainer}) {
    try {
      authRepository = AuthRepository(
        httpClient: diContainer.httpClient,
        secureStorage: diContainer.services.secureStorage,
      );
      onProgress(authRepository.name);

      learningPathRepository = LearningPathRepository(httpClient: diContainer.httpClient);
      onProgress(learningPathRepository.name);

      eventRepository = EventRepository(httpClient: diContainer.httpClient);
      onProgress(eventRepository.name);

      profileRepository = ProfileRepository(httpClient: diContainer.httpClient);
      onProgress(profileRepository.name);
    } on Object catch (error, stackTrace) {
      onError('Repository initialization error', error, stackTrace);
    }
    onProgress('Repositories initialization complete.');
  }
}
