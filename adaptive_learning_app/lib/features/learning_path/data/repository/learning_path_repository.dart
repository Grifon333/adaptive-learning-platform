import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';
import 'package:flutter/foundation.dart';

final class LearningPathRepository implements ILearningPathRepository {
  LearningPathRepository({required this.httpClient, required this.appConfig});

  final IHttpClient httpClient;
  final IAppConfig appConfig;

  @override
  String get name => 'LearningPathRepository';

  @override
  Future<LearningPathDto> generatePath({
    required String studentId,
    required String goalConceptId,
    String? startConceptId,
  }) async {
    final request = LearningPathRequest(startConceptId: startConceptId, goalConceptId: goalConceptId);
    final serviceUrl = appConfig.learningPathServiceUrl;
    final response = await httpClient.post('$serviceUrl/students/$studentId/learning-paths', data: request.toJson());
    return LearningPathDto.fromJson(response.data);
  }

  @override
  Future<List<LearningStepDto>> getRecommendations(String studentId) async {
    final serviceUrl = appConfig.learningPathServiceUrl;
    final response = await httpClient.get('$serviceUrl/students/$studentId/recommendations');
    final data = response.data as Map<String, dynamic>;
    final list = data['recommendations'] as List;
    return list.map((e) => LearningStepDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<List<QuizQuestionDto>> getQuizForConcept(String conceptId) async {
    final serviceUrl = appConfig.learningPathServiceUrl;
    final response = await httpClient.get('$serviceUrl/quizzes/$conceptId');
    final data = response.data as Map<String, dynamic>;
    final list = data['questions'] as List;
    return list.map((e) => QuizQuestionDto.fromJson(e)).toList();
  }

  @override
  Future<List<LearningPathDto>> getAvailablePaths(String studentId) async {
    final serviceUrl = appConfig.learningPathServiceUrl;
    try {
      final response = await httpClient.get('$serviceUrl/students/$studentId/learning-paths');
      final List<dynamic> data = response.data;
      return data.map((json) => LearningPathDto.fromJson(json)).toList();
    } on Object catch (e) {
      debugPrint('Error fetching paths: $e');
      return [];
    }
  }
}
