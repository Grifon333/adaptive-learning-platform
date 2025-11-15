/// {@template i_secure_storage}
/// Service interface for working with secure storage.
/// {@endtemplate}
abstract interface class ISecureStorage {
  const ISecureStorage._({required this.secretKey});

  final String? secretKey;
  static const name = 'ISecureStorage';

  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
  Future<void> deleteAll();
  Future<bool> containsKey(String key);
  String get nameImpl;
}
