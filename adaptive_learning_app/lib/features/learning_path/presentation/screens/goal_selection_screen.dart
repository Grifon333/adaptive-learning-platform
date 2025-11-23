import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class GoalSelectionScreen extends StatelessWidget {
  const GoalSelectionScreen({super.key});

  // Hard-coded targets for MVP. In the future, this can be loaded from the Knowledge Graph Service.
  static const List<Map<String, String>> _goals = [
    {
      'title': 'Python Basics',
      'subtitle': 'Start your programming journey',
      'startNodeId': 'ff9eecf7-81fc-489d-9e8e-2f6360595f02', // Optional
      'endNodeId': 'de53b2dd-b583-4d9c-a190-65e83b26c2b6',
      'icon': '🐍',
    },
    {
      'title': 'Data Science Intro',
      'subtitle': 'Learn to analyze data',
      'startNodeId': 'start-node-ds-uuid',
      'endNodeId': 'end-node-ds-uuid',
      'icon': '📊',
    },
    {
      'title': 'Flutter Masterclass',
      'subtitle': 'Build beautiful mobile apps',
      'startNodeId': 'start-node-flutter-uuid',
      'endNodeId': 'end-node-flutter-uuid',
      'icon': '💙',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Select your learning goal')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _goals.length,
        separatorBuilder: (ctx, index) => const SizedBox(height: 16),
        itemBuilder: (context, index) => _GoalCard(goal: _goals[index]),
      ),
    );
  }
}

class _GoalCard extends StatelessWidget {
  const _GoalCard({required this.goal});

  final Map<String, String> goal;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          context.read<LearningPathBloc>().add(
            GeneratePathRequested(startConceptId: goal['startNodeId'], goalConceptId: goal['endNodeId']!),
          );
          context.pushNamed('learning-path');
        },
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Row(
            children: [
              Container(
                width: 60,
                height: 60,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(12)),
                child: Text(goal['icon']!, style: const TextStyle(fontSize: 30)),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(goal['title']!, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(goal['subtitle']!, style: TextStyle(color: Colors.grey[600])),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, color: Colors.grey, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}
