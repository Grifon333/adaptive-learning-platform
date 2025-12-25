import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:adaptive_learning_app/features/debug/i_debug_service.dart';
import 'package:adaptive_learning_app/features/events/data/dto/event_dto.dart';
import 'package:adaptive_learning_app/features/events/domain/repository/i_event_repository.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template tracking_service}
/// Service for logging user actions.
/// Implements "Store-and-Forward" via local file storage.
/// {@endtemplate}
class TrackingService {
  TrackingService({required this.repository, required this.pathProvider, required this.debugService});

  final IEventRepository repository;
  final IPathProvider pathProvider;
  final IDebugService debugService;

  final List<EventDto> _buffer = [];
  Timer? _flushTimer;
  static const int _batchSize = 10;
  static const Duration _flushInterval = Duration(seconds: 30);
  String? _currentUserId;

  set userId(String? userId) => _currentUserId = userId;

  Future<void> init() async {
    await _loadFromDisk();
    _startTimer();
  }

  void log(String eventType, {Map<String, dynamic>? metadata}) {
    if (_currentUserId == null) return; // Don't log if not logged in

    final event = EventDto(
      eventType: eventType,
      studentId: _currentUserId!,
      metadata: metadata ?? {},
      timestamp: DateTime.now().toUtc(),
    );

    _buffer.add(event);
    debugService.log('Event Buffered: $eventType (Buffer: ${_buffer.length})');

    if (_buffer.length >= _batchSize) {
      _flush();
    } else {
      _saveToDisk(); // Persist immediately to prevent data loss on crash
    }
  }

  void _startTimer() {
    _flushTimer?.cancel();
    _flushTimer = Timer.periodic(_flushInterval, (_) => _flush());
  }

  Future<void> _flush() async {
    if (_buffer.isEmpty) return;

    final batch = List<EventDto>.from(_buffer);
    try {
      await repository.sendBatch(batch);
      _buffer.removeWhere((e) => batch.contains(e));
      await _saveToDisk();
      debugService.log('Events Flushed: ${batch.length}');
    } on Object catch (e) {
      debugService.logWarning('Failed to flush events (Offline?): $e');
      // Keep in buffer/disk and retry next time
    }
  }

  Future<File> get _file async {
    final path = await pathProvider.getAppDocumentsDirectoryPath();
    return File('$path/events_queue.json');
  }

  Future<void> _saveToDisk() async {
    try {
      final file = await _file;
      final jsonList = _buffer.map((e) => e.toJson()).toList();
      await file.writeAsString(json.encode(jsonList));
    } on Object catch (e) {
      debugService.logError('Failed to save events to disk', error: e);
    }
  }

  Future<void> _loadFromDisk() async {
    try {
      final file = await _file;
      if (!await file.exists()) return;

      final content = await file.readAsString();
      if (content.isEmpty) return;

      final List<dynamic> jsonList = json.decode(content);
      final loadedEvents = jsonList.map((e) => EventDto.fromJson(e)).toList();

      _buffer.addAll(loadedEvents);
      debugService.log('Restored ${_buffer.length} events from disk');
    } on Object catch (e) {
      debugService.logError('Failed to load events from disk', error: e);
    }
  }

  void dispose() {
    _flushTimer?.cancel();
    _flush(); // Try one last send
  }
}
