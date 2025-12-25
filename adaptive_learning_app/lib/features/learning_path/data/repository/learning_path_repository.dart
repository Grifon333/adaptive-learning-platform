import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/adaptive_assessment_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/step_complete_response_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/step_quiz_dtos.dart';
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

  @override
  Future<List<ConceptDto>> getConcepts() async {
    final serviceUrl = appConfig.knowledgeGraphServiceUrl;

    // We request a larger limit to get all concepts for the selector
    final response = await httpClient.get('$serviceUrl/concepts?limit=100');

    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List;

    return items.map((e) => ConceptDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<void> updateStepProgress(String stepId, int timeDelta) async {
    // NOTE: This endpoint is in User Service, so we use appConfig.baseUrl
    // The previous analysis confirmed User Service is at baseUrl (port 8000)
    final url = '${appConfig.baseUrl}/learning-paths/steps/$stepId/progress';
    await httpClient.patch(url, data: {'time_delta': timeDelta});
  }

  @override
  Future<StepCompleteResponseDto> completeStep(String stepId) async {
    final url = '${appConfig.baseUrl}/learning-paths/steps/$stepId/complete';
    final response = await httpClient.post(url);
    return StepCompleteResponseDto.fromJson(response.data);
  }

  @override
  Future<StepQuizResultDto> submitStepQuiz(StepQuizSubmissionDto submission) async {
    // This goes to Learning Path Service which orchestrates the grading
    final serviceUrl = appConfig.learningPathServiceUrl;
    final response = await httpClient.post('$serviceUrl/steps/quiz/submit', data: submission.toJson());
    return StepQuizResultDto.fromJson(response.data);
  }

  @override
  Future<AdaptiveAssessmentResponseDto> startAdaptiveAssessment({
    required String studentId,
    required String goalConceptId,
  }) async {
    final serviceUrl = appConfig.learningPathServiceUrl;
    final response = await httpClient.post(
      '$serviceUrl/assessments/adaptive/start',
      data: {'student_id': studentId, 'goal_concept_id': goalConceptId},
    );
    return AdaptiveAssessmentResponseDto.fromJson(response.data);
  }

  @override
  Future<AdaptiveAssessmentResponseDto> submitAdaptiveAnswer({
    required AdaptiveSessionStateDto sessionState,
    required int answerIndex,
  }) async {
    final serviceUrl = appConfig.learningPathServiceUrl;
    // Payload: Entire session object + answer index
    final payload = {'session_state': sessionState.toJson(), 'answer_index': answerIndex};
    final response = await httpClient.post('$serviceUrl/assessments/adaptive/submit', data: payload);
    return AdaptiveAssessmentResponseDto.fromJson(response.data);
  }
}
