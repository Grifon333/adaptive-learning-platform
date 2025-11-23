import 'dart:io';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';

final class LearningPathRepository implements ILearningPathRepository {
  LearningPathRepository({required this.httpClient});

  final IHttpClient httpClient;

  @override
  String get name => 'LearningPathRepository';

  @override
  Future<LearningPathDto> generatePath({
    required String studentId,
    required String startConceptId,
    required String goalConceptId,
  }) async {
    final request = LearningPathRequest(startConceptId: startConceptId, goalConceptId: goalConceptId);

    // TODO: Temp solution for microservice communication
    final String host = Platform.isAndroid ? '10.0.2.2' : 'localhost';
    final String serviceUrl = 'http://$host:8002';
    final response = await httpClient.post(
      '$serviceUrl/api/v1/students/$studentId/learning-paths',
      data: request.toJson(),
    );

    return LearningPathDto.fromJson(response.data);
  }

  @override
  Future<List<LearningStepDto>> getRecommendations(String studentId) async {
    // TODO: Temp solution for microservice communication
    final String host = Platform.isAndroid ? '10.0.2.2' : 'localhost';
    final String serviceUrl = 'http://$host:8002'; // LP Service
    final response = await httpClient.get('$serviceUrl/api/v1/students/$studentId/recommendations');
    final data = response.data as Map<String, dynamic>;
    final list = data['recommendations'] as List;
    return list.map((e) => LearningStepDto.fromJson(e as Map<String, dynamic>)).toList();
  }
}
