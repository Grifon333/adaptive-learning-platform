import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class LearningPathsListScreen extends StatelessWidget {
  const LearningPathsListScreen({super.key});

  // Mock data that combines information about the path and parameters for its generation
  static const List<Map<String, dynamic>> _availablePaths = [
    {
      'title': 'Python Basics',
      'description': 'Learn the basics of syntax, variables, and loops.',
      'startNodeId': 'ff9eecf7-81fc-489d-9e8e-2f6360595f02',
      'endNodeId': 'de53b2dd-b583-4d9c-a190-65e83b26c2b6',
      'progress': 0.45,
      'status': 'In Progress',
      'icon': '🐍',
      'stepsCount': 12,
      'completedSteps': 5,
    },
    {
      'title': 'Data Science Intro',
      'description': 'Introduction to data analysis and machine learning.',
      'startNodeId': null,
      'endNodeId': '9a4c9a78-eca9-4395-8798-3f0956f95fad',
      'progress': 0.10,
      'status': 'Started',
      'icon': '📊',
      'stepsCount': 20,
      'completedSteps': 2,
    },
    {
      'title': 'Flutter Masterclass',
      'description': 'Creating complex interfaces and state management.',
      'startNodeId': null,
      'endNodeId': '9a4c9a78-eca9-4395-8798-3f0956f95fad',
      'progress': 0.0,
      'status': 'Not Started',
      'icon': '💙',
      'stepsCount': 15,
      'completedSteps': 0,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Goals')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.pushNamed('create_path_mode'),
        label: const Text('Create'),
        icon: const Icon(Icons.add),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _availablePaths.length,
        separatorBuilder: (ctx, index) => const SizedBox(height: 16),
        itemBuilder: (context, index) {
          final path = _availablePaths[index];
          return _PathCard(path: path);
        },
      ),
    );
  }
}

class _PathCard extends StatelessWidget {
  const _PathCard({required this.path});

  final Map<String, dynamic> path;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          context.read<LearningPathBloc>().add(
            GeneratePathRequested(startConceptId: path['startNodeId'], goalConceptId: path['endNodeId']),
          );
          context.pushNamed('learning-path');
        },
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 50,
                    height: 50,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(12)),
                    child: Text(path['icon'], style: const TextStyle(fontSize: 24)),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(path['title'], style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(
                          path['description'],
                          style: TextStyle(color: Colors.grey[600], fontSize: 13),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.play_circle_outline, color: Colors.blue, size: 28),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: LinearProgressIndicator(
                      value: path['progress'],
                      backgroundColor: Colors.grey.shade200,
                      color: path['progress'] == 1.0 ? Colors.green : Colors.blue,
                      minHeight: 6,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${(path['progress'] * 100).toInt()}%',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  '${path['completedSteps']} / ${path['stepsCount']} steps',
                  style: TextStyle(color: Colors.grey[500], fontSize: 11),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
