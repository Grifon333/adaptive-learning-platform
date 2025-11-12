import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template app_secure_storage}
/// Basic implementation of the secure storage service.
/// {@endtemplate}
final class AppSecureStorage implements ISecureStorage {
  AppSecureStorage({this.secretKey});

  @override
  final String? secretKey;
  static const name = 'BaseAppSecureStorage';

  /// Storage instance
  final _box = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  @override
  Future<void> deleteAll() async => await _box.deleteAll();

  @override
  Future<void> delete(String key) async => await _box.delete(key: key);

  @override
  Future<bool> containsKey(String key) => _box.containsKey(key: key);

  @override
  Future<String?> read(String key) async => _box.read(key: key);

  @override
  Future<void> write(String key, String value) async => await _box.write(key: key, value: value);

  @override
  String get nameImpl => AppSecureStorage.name;
}
