import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_extensions.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class _UiStep {
  _UiStep(this.step, {this.isHighlighted = false});
  final LearningStepDto step;
  final bool isHighlighted;
}

class LearningPathScreen extends StatelessWidget {
  const LearningPathScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Learning Path')),
      body: BlocBuilder<LearningPathBloc, LearningPathState>(
        builder: (context, state) {
          if (state is LearningPathLoading) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is LearningPathFailure) {
            return Center(
              child: Text('Error: ${state.error}', style: const TextStyle(color: Colors.red)),
            );
          } else if (state is LearningPathSuccess) {
            final rawSteps = state.path.steps;
            if (rawSteps.isEmpty) return const Center(child: Text('Path is empty.'));

            final List<_UiStep> uiSteps = [];
            bool pendingHighlight = false;
            for (final step in rawSteps) {
              if (step.isRemedial) {
                pendingHighlight = true;
              } else {
                uiSteps.add(_UiStep(step, isHighlighted: pendingHighlight));
                pendingHighlight = false; // Reset flag
              }
            }

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: uiSteps.length,
              separatorBuilder: (ctx, index) => _ConnectorLine(isActive: uiSteps[index].step.isCompleted),
              itemBuilder: (context, index) {
                final uiStep = uiSteps[index];
                final stepDto = uiStep.step;

                // Resolve concept name
                final concept = state.conceptMap[stepDto.conceptId];

                // Determine lock state based on the FULL original list logic or simplified UI logic?
                // Using helper extension on the DTO usually requires the full list to check previous steps.
                // We pass the raw list to isLocked to ensure accurate dependency checking.
                final isLocked = stepDto.isLocked(rawSteps);

                return _StepCard(
                  step: stepDto,
                  concept: concept,
                  isLocked: isLocked,
                  isHighlighted: uiStep.isHighlighted,
                );
              },
            );
          }
          return const Center(child: Text('Select a learning goal'));
        },
      ),
    );
  }
}

class _ConnectorLine extends StatelessWidget {
  const _ConnectorLine({required this.isActive});

  final bool isActive;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 20,
      alignment: Alignment.centerLeft,
      padding: const EdgeInsets.only(left: 34),
      child: Container(width: 2, color: isActive ? Colors.green : Colors.grey.shade300),
    );
  }
}

class _StepCard extends StatelessWidget {
  const _StepCard({required this.step, required this.isLocked, required this.isHighlighted, this.concept});

  final LearningStepDto step;
  final ConceptDto? concept;
  final bool isLocked;
  final bool isHighlighted;

  @override
  Widget build(BuildContext context) {
    final isCompleted = step.isCompleted;

    // --- Style Logic ---
    Color cardColor;
    Color borderColor;
    Color textColor;
    Color iconColor;
    IconData trailingIcon;
    Color avatarBg;
    Color avatarText;

    if (isLocked) {
      // Locked State
      cardColor = Colors.grey.shade50;
      borderColor = Colors.grey.shade200;
      textColor = Colors.grey;
      iconColor = Colors.grey;
      trailingIcon = Icons.lock;
      avatarBg = Colors.grey.shade200;
      avatarText = Colors.grey;
    } else if (isCompleted) {
      // Completed State
      cardColor = Colors.white;
      borderColor = Colors.green.shade100;
      textColor = Colors.black;
      iconColor = Colors.green;
      trailingIcon = Icons.check_circle;
      avatarBg = Colors.green.shade100;
      avatarText = Colors.green.shade800;
    } else if (isHighlighted) {
      // Highlighted (Remedial context merged)
      cardColor = Colors.orange.shade50;
      borderColor = Colors.orange.shade200;
      textColor = Colors.brown.shade900;
      iconColor = Colors.orange.shade800;
      trailingIcon = Icons.priority_high; // Indicates attention needed
      avatarBg = Colors.orange.shade100;
      avatarText = Colors.orange.shade900;
    } else {
      // Standard Active State
      cardColor = Colors.white;
      borderColor = Colors.blue.shade100;
      textColor = Colors.black;
      iconColor = Colors.blue;
      trailingIcon = Icons.play_circle_fill;
      avatarBg = Colors.blue.shade100;
      avatarText = Colors.blue.shade800;
    }

    return Card(
      elevation: isLocked ? 0 : 2,
      color: cardColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: borderColor),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: CircleAvatar(
          backgroundColor: avatarBg,
          child: Text(
            '${step.stepNumber}',
            style: TextStyle(color: avatarText, fontWeight: FontWeight.bold),
          ),
        ),
        title: Text(
          concept?.name ?? 'Unknown Concept',
          style: TextStyle(fontWeight: FontWeight.bold, color: textColor),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            if (concept?.description != null)
              Text(
                concept!.description!,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: isLocked
                      ? Colors.grey.shade400
                      : (isHighlighted ? Colors.brown.shade400 : Colors.grey.shade600),
                ),
              ),
            if (!isLocked && isHighlighted) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: Colors.orange.shade100, borderRadius: BorderRadius.circular(4)),
                child: const Text(
                  'Recommended Review',
                  style: TextStyle(fontSize: 11, color: Colors.brown, fontWeight: FontWeight.bold),
                ),
              ),
            ] else if (!isLocked) ...[
              const SizedBox(height: 4),
              Text('${step.resources.length} materials', style: const TextStyle(fontSize: 12)),
            ],
          ],
        ),
        trailing: Icon(trailingIcon, color: iconColor, size: 32),
        onTap: isLocked
            ? () {
                ScaffoldMessenger.of(context).clearSnackBars();
                ScaffoldMessenger.of(
                  context,
                ).showSnackBar(const SnackBar(content: Text('Complete the previous step to unlock this one!')));
              }
            : () => _onStepTap(context),
      ),
    );
  }

  void _onStepTap(BuildContext context) async {
    await context.pushNamed('lesson', extra: step);
    if (context.mounted) {
      // STATUS UPDATE:
      // When we return from class, we don't know if the student passed the test.
      // But we know we need to check.
      // The easiest way is to reload the path.
      // In a real application, this can be optimized.
      final authState = context.read<AuthBloc>().state;
      final studentId = (authState is AuthAuthenticated) ? authState.userId : '';
      context.read<LearningPathBloc>().add(LearningPathRefreshRequested(studentId));
    }
  }
}
