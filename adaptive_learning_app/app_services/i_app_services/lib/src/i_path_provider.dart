/// {@template i_path_provider}
/// Service interface for getting paths to directories.
/// {@endtemplate}
abstract interface class IPathProvider {
  static const name = 'IPathProvider';

  Future<String?> getAppDocumentsDirectoryPath();
}
