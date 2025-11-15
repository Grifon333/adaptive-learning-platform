import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:talker_bloc_logger/talker_bloc_logger.dart';
import 'package:talker_dio_logger/talker_dio_logger_interceptor.dart';
import 'package:talker_flutter/talker_flutter.dart';

/// {@template debug_service}
/// Implementation of debugging service using Talker.
/// {@endtemplate}
class DebugService implements IDebugService {
  DebugService() {
    _talker = TalkerFlutter.init();
    _talkerDioLogger = TalkerDioLogger(talker: _talker);
    _talkerRouteObserver = TalkerRouteObserver(_talker);
    _talkerBlocObserver = TalkerBlocObserver(talker: _talker);
  }

  static const name = 'DebugService';
  late final Talker _talker;
  late final TalkerDioLogger _talkerDioLogger;
  late final TalkerRouteObserver _talkerRouteObserver;
  late final TalkerBlocObserver _talkerBlocObserver;

  @override
  TalkerDioLogger get dioLogger => _talkerDioLogger;

  @override
  TalkerRouteObserver get routeObserver => _talkerRouteObserver;

  @override
  TalkerBlocObserver get blocObserver => _talkerBlocObserver;

  @override
  void log(Object message, {Object? logLevel, Map<String, dynamic>? args}) => _talker.log(message);

  @override
  void logWarning(Object message, {Object? logLevel, Map<String, dynamic>? args}) => _talker.warning(message);

  @override
  void logError(Object message, {Object? error, StackTrace? stackTrace, Object? logLevel, Map<String, dynamic>? args}) {
    _talker.error(message, error, stackTrace);
  }
}
