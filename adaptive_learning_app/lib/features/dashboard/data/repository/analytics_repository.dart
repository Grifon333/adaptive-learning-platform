import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/dashboard/data/dto/dashboard_dtos.dart';
import 'package:adaptive_learning_app/features/dashboard/domain/repository/i_analytics_repository.dart';

final class AnalyticsRepository implements IAnalyticsRepository {
  AnalyticsRepository({required this.httpClient, required this.appConfig});

  final IHttpClient httpClient;
  final IAppConfig appConfig;

  @override
  String get name => 'AnalyticsRepository';

  @override
  Future<DashboardDataDto> getDashboardData(String studentId) async {
    final url = '${appConfig.analyticsServiceUrl}/analytics/dashboard/$studentId';
    final response = await httpClient.get(url);
    return DashboardDataDto.fromJson(response.data);
  }
}
