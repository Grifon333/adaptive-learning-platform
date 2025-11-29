import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';

/// Extensions for convenient work with statuses
extension LearningStepStatusX on LearningStepDto {
  bool get isCompleted => status == 'completed';
  bool get isPending => status == 'pending';

  // Logic for calculating availability based on the list of steps
  bool isLocked(List<LearningStepDto> allSteps) {
    if (isCompleted || stepNumber == 1) return false;
    // Find the previous step
    final prevIndex = stepNumber - 2; // stepNumber starts from 1
    if (prevIndex < 0) return false;
    // If the previous step is NOT completed, the current one is locked
    return !allSteps[prevIndex].isCompleted;
  }
}
