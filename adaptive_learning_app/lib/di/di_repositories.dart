import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/di/di_typedefs.dart';

/// {@template di_repositories}
/// Class for initiating and managing application repositories.
/// {@endtemplate}
final class DiRepositories {
  DiRepositories();

  // TODO: AuthRepo

  void init({required OnProgress onProgress, required OnError onError, required DiContainer diContainer}) {
    try {
      // TODO: Init auth
    } on Object catch (error, stackTrace) {
      onError(
        'Repository initialization error',
        error,
        stackTrace,
      );
    }
    onProgress('Repositories initialization complete.');
  }
}
