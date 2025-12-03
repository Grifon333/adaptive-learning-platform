// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class StepCompleteResponseDto {
  const StepCompleteResponseDto({
    required this.stepId,
    required this.status,
    required this.pathCompletionPercentage,
    required this.pathIsCompleted,
  });

  final String stepId;
  final String status;
  final double pathCompletionPercentage;
  final bool pathIsCompleted;

  factory StepCompleteResponseDto.fromJson(Map<String, dynamic> json) {
    return StepCompleteResponseDto(
      stepId: json['step_id'] as String,
      status: json['status'] as String,
      pathCompletionPercentage: (json['path_completion_percentage'] as num).toDouble(),
      pathIsCompleted: json['path_is_completed'] as bool,
    );
  }
}
