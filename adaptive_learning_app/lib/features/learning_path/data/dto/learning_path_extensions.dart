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

extension LearningPathUiLogic on LearningPathDto {
  /// Returns only the steps that should be counted in the progress bar.
  /// Remedial steps are excluded as they are "helpers" not "milestones".
  List<LearningStepDto> get mainSteps => steps.where((s) => !s.isRemedial).toList();

  /// Total count of main steps.
  int get totalMainSteps => mainSteps.length;

  /// Count of completed main steps (Case-Insensitive Check).
  int get completedMainSteps => mainSteps.where((s) => s.status.toLowerCase() == 'completed').length;

  /// Calculated percentage (0.0 to 1.0).
  /// Safe against division by zero.
  double get uiCompletionPercentage {
    if (totalMainSteps == 0) return 0.0;

    // Clamp to ensure we never exceed 100% due to data anomalies
    final percent = completedMainSteps / totalMainSteps;
    return percent > 1.0 ? 1.0 : percent;
  }
}
