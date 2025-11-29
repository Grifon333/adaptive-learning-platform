import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class LearningPathsListScreen extends StatefulWidget {
  const LearningPathsListScreen({super.key});

  @override
  State<LearningPathsListScreen> createState() => _LearningPathsListScreenState();
}

class _LearningPathsListScreenState extends State<LearningPathsListScreen> {
  late Future<List<LearningPathDto>> _pathsFuture;

  @override
  void initState() {
    super.initState();
    _loadPaths();
  }

  void _loadPaths() {
    final authState = context.read<AuthBloc>().state;
    if (authState is AuthAuthenticated) {
      _pathsFuture = context.read<DiContainer>().repositories.learningPathRepository.getAvailablePaths(
        authState.userId,
      );
    } else {
      _pathsFuture = Future.value([]);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Goals')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await context.pushNamed('create_path_mode');
          setState(_loadPaths);
        },
        label: const Text('Create'),
        icon: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<LearningPathDto>>(
        future: _pathsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Center(child: Text('Error loading paths: ${snapshot.error}'));

          final paths = snapshot.data ?? [];
          if (paths.isEmpty) return const Center(child: Text('No active paths found.'));
          final reversedPaths = paths.reversed.toList();

          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: reversedPaths.length,
            separatorBuilder: (ctx, index) => const SizedBox(height: 16),
            itemBuilder: (context, index) => _PathCard(path: reversedPaths[index]),
          );
        },
      ),
    );
  }
}

class _PathCard extends StatelessWidget {
  const _PathCard({required this.path});

  final LearningPathDto path;

  @override
  Widget build(BuildContext context) {
    final goalId = path.goalConcepts.isNotEmpty ? path.goalConcepts.first : 'Unknown';
    final title = _mapConceptIdToName(goalId);
    final icon = _mapConceptToIcon(goalId);

    final completedSteps = path.steps.where((s) => s.status == 'completed').length;
    final totalSteps = path.steps.length;

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          context.read<LearningPathBloc>().add(SelectExistingPath(path));
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
                    child: Text(icon, style: const TextStyle(fontSize: 24)),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(
                          'description...',
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
                      value: path.completionPercentage,
                      backgroundColor: Colors.grey.shade200,
                      color: path.completionPercentage >= 1.0 ? Colors.green : Colors.blue,
                      minHeight: 6,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${(path.completionPercentage * 100).toInt()}%',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  '$completedSteps / $totalSteps steps',
                  style: TextStyle(color: Colors.grey[500], fontSize: 11),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _mapConceptIdToName(String id) {
    if (id.contains('ff9eecf7')) return 'Python Basics';
    if (id.contains('de53b2dd')) return 'Data Science Intro';
    if (id.contains('21c3597d')) return 'Dart Language';
    if (id.contains('9a4c9a78')) return 'Flutter Advanced';
    return 'Custom Goal';
  }

  String _mapConceptToIcon(String id) {
    if (id.contains('ff9eecf7')) return '🐍';
    if (id.contains('de53b2dd')) return '📊';
    if (id.contains('21c3597d')) return '💙';
    if (id.contains('9a4c9a78')) return '🚀';
    return '🎓';
  }
}
