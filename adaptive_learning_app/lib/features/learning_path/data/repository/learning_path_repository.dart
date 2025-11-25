import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/repository/i_learning_path_repository.dart';

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
  Future<List<Map<String, dynamic>>> getAvailablePaths() async {
    await Future.delayed(const Duration(milliseconds: 300)); // Simulating a network delay

    // Mock data moved from UI to Data Layer
    return [
      {
        'title': 'Python Basics',
        'description': 'Learn the basics of syntax, variables, and loops.',
        'startNodeId': 'ff9eecf7-81fc-489d-9e8e-2f6360595f02', // Stored in Backend Seed!
        'endNodeId': 'de53b2dd-b583-4d9c-a190-65e83b26c2b6',
        'progress': 0.45,
        'status': 'In Progress',
        'icon': '🐍',
        'stepsCount': 12,
        'completedSteps': 5,
      },
      {
        'title': 'Data Science Intro',
        'description': 'Introduction to data analysis and machine learning.',
        'startNodeId': null,
        'endNodeId': 'de53b2dd-b583-4d9c-a190-65e83b26c2b6',
        'progress': 0.10,
        'status': 'Started',
        'icon': '📊',
        'stepsCount': 20,
        'completedSteps': 2,
      },
      {
        'title': 'Flutter Masterclass',
        'description': 'Creating complex interfaces and state management.',
        'startNodeId': null,
        'endNodeId': '9a4c9a78-eca9-4395-8798-3f0956f95fad', // Stored in Backend Seed!
        'progress': 0.0,
        'status': 'Not Started',
        'icon': '💙',
        'stepsCount': 15,
        'completedSteps': 0,
      },
    ];
  }
}
