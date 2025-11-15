import 'package:i_app_services/i_app_services.dart';
import 'package:path_provider/path_provider.dart';

/// {@template app_path_provider}
/// Basic implementation of the path provider service
/// {@endtemplate}
class AppPathProvider implements IPathProvider {
  const AppPathProvider();

  static const name = 'BaseAppPathProvider';

  @override
  Future<String> getAppDocumentsDirectoryPath() async {
    return (await getApplicationDocumentsDirectory()).path;
  }
}
