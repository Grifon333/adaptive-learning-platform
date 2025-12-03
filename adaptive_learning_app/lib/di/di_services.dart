import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/di/di_typedefs.dart';
import 'package:adaptive_learning_app/features/events/service/tracking_service.dart';
import 'package:app_services/app_services.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template di_services}
/// Class for initiating and managing application services.
/// {@endtemplate}
final class DiServices {
  DiServices();

  late final ISecureStorage secureStorage;
  late final IPathProvider pathProvider;
  late final TrackingService trackingService;

  void init({required OnProgress onProgress, required OnError onError, required DiContainer diContainer}) {
    try {
      secureStorage = AppSecureStorage(secretKey: diContainer.appConfig.secretKey);
      onProgress(AppSecureStorage.name);

      pathProvider = const AppPathProvider();
      onProgress(IPathProvider.name);
    } on Object catch (error, stackTrace) {
      onError('Initialization Exception of ${ISecureStorage.name}', error, stackTrace);
    }
    onProgress('Services initialization complete.');
  }

  Future<void> initLogic({required DiContainer diContainer}) async {
    trackingService = TrackingService(
      repository: diContainer.repositories.eventRepository,
      pathProvider: pathProvider,
      debugService: diContainer.debugService,
    );
    await trackingService.init();
  }
}
