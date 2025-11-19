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
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: steps.length,
              separatorBuilder: (ctx, index) => const SizedBox(height: 16),
              itemBuilder: (context, index) {
                final step = steps[index];
                return Card(
                  elevation: 2,
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(16),
                    leading: CircleAvatar(child: Text('${step.stepNumber}')),
                    title: Text('Step ${step.stepNumber}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text('Concept ID: ${step.conceptId.substring(0, 8)}...'),
                        Text('Time: ${step.estimatedTime ?? 0} min | Difficulty: ${step.difficulty ?? 0.0}'),
                      ],
                    ),
                    trailing: step.status == 'pending'
                        ? const Icon(Icons.play_circle_fill, color: Colors.blue, size: 32)
                        : const Icon(Icons.check_circle, color: Colors.green, size: 32),
                    onTap: () {
                      context.pushNamed(
                        'lesson',
                        pathParameters: {'stepId': step.id},
                        queryParameters: {'conceptId': step.conceptId},
                      );
                    },
                  ),
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
