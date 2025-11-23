import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class LearningPathScreen extends StatelessWidget {
  const LearningPathScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Learning path')),
      body: BlocBuilder<LearningPathBloc, LearningPathState>(
        builder: (context, state) {
          if (state is LearningPathLoading) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is LearningPathFailure) {
            return Center(
              child: Text('Error: ${state.error}', style: const TextStyle(color: Colors.red)),
            );
          } else if (state is LearningPathSuccess) {
            final steps = state.path.steps;
            if (steps.isEmpty) return const Center(child: Text('Path is empty.'));

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: steps.length,
              separatorBuilder: (ctx, index) => _ConnectorLine(isActive: steps[index].status == 'completed'),
              itemBuilder: (context, index) {
                final step = steps[index];

                // BLOCKING LOGIC:
                // Step is available if:
                // 1. It is the first step (index == 0)
                // 2. OR the previous step has the status 'completed'
                final bool isFirst = index == 0;
                final bool isPreviousCompleted = isFirst ? true : steps[index - 1].status == 'completed';
                final bool isLocked = !isPreviousCompleted;

                return _StepCard(step: step, isLocked: isLocked);
              },
            );
          }
          return const Center(child: Text('Оберіть ціль навчання'));
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
  const _StepCard({required this.step, required this.isLocked});

  final LearningStepDto step;
  final bool isLocked;

  @override
  Widget build(BuildContext context) {
    final isCompleted = step.status == 'completed';

    Color cardColor = Colors.white;
    Color textColor = Colors.black;
    IconData trailingIcon = Icons.lock;
    Color iconColor = Colors.grey;

    if (isLocked) {
      cardColor = Colors.grey.shade100;
      textColor = Colors.grey;
    } else if (isCompleted) {
      trailingIcon = Icons.check_circle;
      iconColor = Colors.green;
    } else {
      trailingIcon = Icons.play_circle_fill;
      iconColor = Colors.blue;
    }

    return Card(
      elevation: isLocked ? 0 : 2,
      color: cardColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isLocked ? BorderSide(color: Colors.grey.shade300) : BorderSide.none,
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: CircleAvatar(
          backgroundColor: isLocked
              ? Colors.grey.shade300
              : (isCompleted ? Colors.green.shade100 : Colors.blue.shade100),
          child: Text(
            '${step.stepNumber}',
            style: TextStyle(
              color: isLocked ? Colors.grey : (isCompleted ? Colors.green.shade800 : Colors.blue.shade800),
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        title: Text(
          'Крок ${step.stepNumber}',
          style: TextStyle(fontWeight: FontWeight.bold, color: textColor),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              'Concept: ${step.conceptId.substring(0, 8)}...', // Replace it with the actual name by adding it to the DTO.
              style: TextStyle(color: isLocked ? Colors.grey.shade400 : Colors.grey.shade600),
            ),
            if (!isLocked) ...[
              const SizedBox(height: 4),
              Text('${step.resources.length} матеріалів', style: const TextStyle(fontSize: 12)),
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
            : () async {
                // Transition to the lesson
                await context.pushNamed('lesson', extra: step);

                // STATUS UPDATE:
                // When we return from class, we don't know if the student passed the test.
                // But we know we need to check.
                // The easiest way is to reload the path.
                // In a real application, this can be optimized.
                if (context.mounted) {
                  // Here we assume that we have access to the current IDs.
                  // Or simpler: just refresh the screen or add an event to BLoC
                  // context.read<LearningPathBloc>().add(RefreshPathEvent(...));
                  // For now, the user can click "Back" and re-enter, or we will add auto-refresh.
                }
              },
      ),
    );
  }
}
