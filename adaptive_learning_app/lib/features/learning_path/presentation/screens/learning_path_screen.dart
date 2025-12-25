import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
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
            final steps = state.path.steps;
            if (steps.isEmpty) return const Center(child: Text('Path is empty.'));

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: steps.length,
              separatorBuilder: (ctx, index) => _ConnectorLine(isActive: steps[index].isCompleted),
              itemBuilder: (context, index) {
                final step = steps[index];

                // Resolve concept name using the map from the state
                final concept = state.conceptMap[step.conceptId];

                // Calculate lock state
                final isLocked = step.isLocked(steps);

                return _StepCard(step: step, concept: concept, isLocked: isLocked);
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
  const _StepCard({required this.step, required this.isLocked, this.concept});

  final LearningStepDto step;
  final ConceptDto? concept;
  final bool isLocked;

  @override
  Widget build(BuildContext context) {
    final isCompleted = step.isCompleted;

    // --- CASE 1: Remedial Step (Yellow, Indented, "Review Required") ---
    if (step.isRemedial) {
      return Container(
        // Restore the indentation for remedial steps
        margin: const EdgeInsets.only(left: 32, bottom: 8, top: 8),
        child: Card(
          elevation: isLocked ? 0 : 4,
          color: isLocked ? Colors.grey.shade50 : Colors.orange.shade50,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: isLocked ? Colors.grey.shade200 : Colors.orange.shade200),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.all(16),
            leading: CircleAvatar(
              backgroundColor: isLocked ? Colors.grey.shade200 : Colors.orange.shade100,
              child: Icon(Icons.refresh, color: isLocked ? Colors.grey : Colors.orange),
            ),
            title: Text(
              'Review Required',
              style: TextStyle(fontWeight: FontWeight.bold, color: isLocked ? Colors.grey : Colors.brown),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                // Display the Concept Name instead of ID
                Text(
                  concept?.name ?? 'Unknown Concept',
                  style: TextStyle(fontWeight: FontWeight.bold, color: Colors.brown.shade800),
                ),
                if (step.description != null) ...[
                  const SizedBox(height: 2),
                  Text(step.description!, style: TextStyle(color: Colors.brown.shade600, fontSize: 12)),
                ],
              ],
            ),
            trailing: isCompleted
                ? const Icon(Icons.check_circle, color: Colors.green)
                : Icon(Icons.arrow_forward, color: isLocked ? Colors.grey : Colors.orange),
            onTap: isLocked ? null : () => _onStepTap(context),
          ),
        ),
      );
    }

    // --- CASE 2: Standard Step (White/Green/Blue, Full Width) ---
    Color cardColor = Colors.white;
    Color textColor = Colors.black;
    IconData trailingIcon = Icons.lock;
    Color iconColor = Colors.grey;
    Color avatarBg = Colors.grey.shade300;
    Color avatarText = Colors.grey;

    if (isLocked) {
      cardColor = Colors.grey.shade50;
      textColor = Colors.grey;
      avatarBg = Colors.grey.shade200;
    } else if (isCompleted) {
      trailingIcon = Icons.check_circle;
      iconColor = Colors.green;
      avatarBg = Colors.green.shade100;
      avatarText = Colors.green.shade800;
    } else {
      trailingIcon = Icons.play_circle_fill;
      iconColor = Colors.blue;
      avatarBg = Colors.blue.shade100;
      avatarText = Colors.blue.shade800;
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
          backgroundColor: avatarBg,
          child: Text(
            '${step.stepNumber}',
            style: TextStyle(color: avatarText, fontWeight: FontWeight.bold),
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
            // Display Concept Name
            Text(
              concept?.name ?? 'Unknown',
              style: TextStyle(
                color: isLocked ? Colors.grey.shade400 : Colors.grey.shade600,
                fontWeight: FontWeight.w500,
              ),
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
      final authState = context.read<AuthBloc>().state;
      final studentId = (authState is AuthAuthenticated) ? authState.userId : '';
      context.read<LearningPathBloc>().add(LearningPathRefreshRequested(studentId));
    }
  }
}
