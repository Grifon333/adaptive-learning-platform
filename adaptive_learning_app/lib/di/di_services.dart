import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/di/di_typedefs.dart';
import 'package:app_services/app_services.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template di_services}
/// Class for initiating and managing application services.
/// {@endtemplate}
final class DiServices {
  DiServices();

  late final ISecureStorage secureStorage;

  void init({required OnProgress onProgress, required OnError onError, required DiContainer diContainer}) {
    try {
      secureStorage = AppSecureStorage(secretKey: diContainer.appConfig.secretKey);
      onProgress(AppSecureStorage.name);
    } on Object catch (error, stackTrace) {
      onError('Initialization Exception of ${ISecureStorage.name}', error, stackTrace);
    }
    onProgress('Services initialization complete.');
  }
}
