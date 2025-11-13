import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/di/di_typedefs.dart';
import 'package:adaptive_learning_app/features/auth/data/repository/auth_repository.dart';
import 'package:adaptive_learning_app/features/auth/domain/repository/i_auth_repository.dart';

/// {@template di_repositories}
/// Class for initiating and managing application repositories.
/// {@endtemplate}
final class DiRepositories {
  DiRepositories();

  late final IAuthRepository authRepository;

  void init({required OnProgress onProgress, required OnError onError, required DiContainer diContainer}) {
    try {
      authRepository = AuthRepository(
        httpClient: diContainer.httpClient,
        secureStorage: diContainer.services.secureStorage,
      );
      onProgress(authRepository.name);
    } on Object catch (error, stackTrace) {
      onError('Repository initialization error', error, stackTrace);
    }
    onProgress('Repositories initialization complete.');
  }
}
