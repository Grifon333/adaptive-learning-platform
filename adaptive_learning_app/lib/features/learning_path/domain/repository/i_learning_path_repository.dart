import 'package:adaptive_learning_app/di/di_base_repository.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/assessment_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/step_complete_response_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/step_quiz_dtos.dart';

abstract interface class ILearningPathRepository with DiBaseRepository {
  Future<LearningPathDto> generatePath({
    required String studentId,
    required String goalConceptId,
    String? startConceptId,
  });

  Future<List<LearningStepDto>> getRecommendations(String studentId);

  Future<List<QuizQuestionDto>> getQuizForConcept(String conceptId);

  Future<List<LearningPathDto>> getAvailablePaths(String studentId);

  Future<AssessmentSessionDto> startAssessment({required String studentId, required String goalConceptId});

  Future<LearningPathDto> submitAssessment(AssessmentSubmissionDto submission);

  Future<List<ConceptDto>> getConcepts();

  Future<void> updateStepProgress(String stepId, int timeDelta);

  Future<StepCompleteResponseDto> completeStep(String stepId);

  Future<StepQuizResultDto> submitStepQuiz(StepQuizSubmissionDto submission);
}
