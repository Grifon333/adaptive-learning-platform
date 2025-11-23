import 'package:adaptive_learning_app/di/di_base_repository.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';

abstract interface class ILearningPathRepository with DiBaseRepository {
  Future<LearningPathDto> generatePath({
    required String studentId,
    required String startConceptId,
    required String goalConceptId,
  });

  Future<List<LearningStepDto>> getRecommendations(String studentId);
}
