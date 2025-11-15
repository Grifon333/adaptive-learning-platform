import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

/// {@template i_debug_service}
/// Interface for debugging service.
/// {@endtemplate}
abstract interface class IDebugService {
  static const name = 'IDebugService';
  Interceptor get dioLogger;
  NavigatorObserver get routeObserver;
  BlocObserver get blocObserver;

  void log(Object message, {Object? logLevel, Map<String, dynamic>? args});

  void logWarning(Object message, {Object? logLevel, Map<String, dynamic>? args});

  void logError(Object message, {Object? error, StackTrace? stackTrace, Object? logLevel, Map<String, dynamic>? args});
}
