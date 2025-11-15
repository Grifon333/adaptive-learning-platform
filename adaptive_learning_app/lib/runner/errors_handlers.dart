part of 'app_runner.dart';

// Method for initializing global error handlers
void _initErrorHandlers(IDebugService debugService) {
  // Intercepting Flutter errors (e.g., rendering errors)
  FlutterError.onError = (details) {
    debugService.logError(
      'Intercepted FlutterError.onError: ${details.exceptionAsString()}',
      error: details.exception,
      stackTrace: details.stack,
    );
    // _showErrorScreen()
  };

  // Interception of asynchronous errors (e.g., errors in Future)
  PlatformDispatcher.instance.onError = (error, stackTrace) {
    debugService.logError('Intercepted PlatformDispatcher.instance.onError', error: error, stackTrace: stackTrace);
    // _showErrorScreen()
    return true;
  };
}

// TODO: _showErrorScreen()
