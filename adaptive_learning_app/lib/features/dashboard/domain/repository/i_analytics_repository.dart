import 'package:adaptive_learning_app/di/di_base_repository.dart';
import 'package:adaptive_learning_app/features/dashboard/data/dto/dashboard_dtos.dart';

abstract interface class IAnalyticsRepository with DiBaseRepository {
  Future<DashboardDataDto> getDashboardData(String studentId);
}
