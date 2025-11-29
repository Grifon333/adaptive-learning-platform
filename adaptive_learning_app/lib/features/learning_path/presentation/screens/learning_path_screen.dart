import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_extensions.dart';
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
              separatorBuilder: (ctx, index) => _ConnectorLine(isActive: steps[index].isCompleted),
              itemBuilder: (context, index) {
                final step = steps[index];
                return _StepCard(step: step, isLocked: step.isLocked(steps));
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
  const _StepCard({required this.step, required this.isLocked});

  final LearningStepDto step;
  final bool isLocked;

  @override
  Widget build(BuildContext context) {
    final isCompleted = step.isCompleted;

    if (step.isRemedial) {
      return Container(
        margin: const EdgeInsets.only(left: 32, bottom: 8, top: 8),
        child: Card(
          elevation: isLocked ? 0 : 4,
          color: isLocked ? Colors.grey.shade50 : Colors.orange.shade50,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.orange.shade200),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.all(16),
            leading: CircleAvatar(
              backgroundColor: Colors.orange.shade100,
              child: const Icon(Icons.refresh, color: Colors.orange),
            ),
            title: const Text(
              'Review Required',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.brown),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(
                  step.description ?? 'Please review this topic to improve mastery.',
                  style: TextStyle(color: Colors.brown.shade600),
                ),
              ],
            ),
            trailing: isCompleted
                ? const Icon(Icons.check_circle, color: Colors.green)
                : const Icon(Icons.arrow_forward, color: Colors.orange),
            onTap: isLocked ? null : () => _onStepTap(context),
          ),
        ),
      );
    }

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
          'Step ${step.stepNumber}',
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
