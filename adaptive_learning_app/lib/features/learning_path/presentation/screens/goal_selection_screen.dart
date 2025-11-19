import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class GoalSelectionScreen extends StatelessWidget {
  const GoalSelectionScreen({super.key});

  // Hardcoded IDs for demonstration purposes
  final String startNodeId = "ab442026-08d0-4e18-b36a-e685fa3f92e5"; // A
  final String endNodeId = "0a5d2692-2c6b-41dc-838f-ef594a40cd66"; // C

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Goal Selection')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('What do you want to learn today?', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 30),
            Card(
              child: ListTile(
                leading: const Icon(Icons.school, size: 32),
                title: const Text('List Comprehensions'),
                subtitle: const Text('Advanced Python Topic'),
                trailing: const Icon(Icons.arrow_forward_ios),
                onTap: () {
                  // Starting path generation
                  context.read<LearningPathBloc>().add(
                    GeneratePathRequested(startConceptId: startNodeId, goalConceptId: endNodeId),
                  );
                  context.pushNamed('learning-path');
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
