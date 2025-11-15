/// {@template di_base_repository}
/// Base mixin for all repositories in the application.
/// Each repository must use this mixin to ensure compatibility with the dependency system.
/// {@endtemplate}
mixin class DiBaseRepository {
  DiBaseRepository();

  String get name => 'DiBaseRepository';
}
