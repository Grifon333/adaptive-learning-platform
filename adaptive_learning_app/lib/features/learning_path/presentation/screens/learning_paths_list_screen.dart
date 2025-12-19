import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_extensions.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class _PathListData {
  final List<LearningPathDto> paths;
  final Map<String, ConceptDto> conceptMap;
  _PathListData(this.paths, this.conceptMap);
}

class LearningPathsListScreen extends StatefulWidget {
  const LearningPathsListScreen({super.key});

  @override
  State<LearningPathsListScreen> createState() => _LearningPathsListScreenState();
}

class _LearningPathsListScreenState extends State<LearningPathsListScreen> {
  late Future<_PathListData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() {
    final authState = context.read<AuthBloc>().state;
    if (authState is AuthAuthenticated) {
      final repo = context.read<DiContainer>().repositories.learningPathRepository;

      _dataFuture = Future.wait([repo.getAvailablePaths(authState.userId), repo.getConcepts()]).then((results) {
        final paths = results[0] as List<LearningPathDto>;
        final concepts = results[1] as List<ConceptDto>;
        final map = {for (final c in concepts) c.id: c};
        return _PathListData(paths, map);
      });
    } else {
      _dataFuture = Future.value(_PathListData([], {}));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Goals')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await context.pushNamed('create_path_mode');
          setState(_loadData);
        },
        label: const Text('Create'),
        icon: const Icon(Icons.add),
      ),
      body: FutureBuilder<_PathListData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Center(child: Text('Error loading paths: ${snapshot.error}'));

          final data = snapshot.data;
          if (data == null || data.paths.isEmpty) return const Center(child: Text('No active paths found.'));

          final reversedPaths = data.paths.reversed.toList();

          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: reversedPaths.length,
            separatorBuilder: (ctx, index) => const SizedBox(height: 16),
            itemBuilder: (context, index) => _PathCard(path: reversedPaths[index], conceptMap: data.conceptMap),
          );
        },
      ),
    );
  }
}

class _PathCard extends StatelessWidget {
  const _PathCard({required this.path, required this.conceptMap});

  final LearningPathDto path;
  final Map<String, ConceptDto> conceptMap;

  @override
  Widget build(BuildContext context) {
    // Determine the Goal Name
    final goalId = path.goalConcepts.isNotEmpty ? path.goalConcepts.first : null;
    final concept = goalId != null ? conceptMap[goalId] : null;

    final title = concept?.name ?? 'Custom Goal';
    final description = concept?.description ?? 'Personalized learning trajectory';
    final iconText = _getIconForName(title);
    final double percent = path.uiCompletionPercentage;
    final int completed = path.completedMainSteps;
    final int total = path.totalMainSteps;

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
              // Header Row
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 50,
                    height: 50,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(12)),
                    child: Text(iconText, style: const TextStyle(fontSize: 24)),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text(
                          description,
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

              // Progress Section
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: LinearProgressIndicator(
                        value: percent,
                        backgroundColor: Colors.grey.shade200,
                        // Turn green if fully complete
                        color: percent >= 1.0 ? Colors.green : Colors.blue,
                        minHeight: 6,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${(percent * 100).toInt()}%',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: Text('$completed / $total steps', style: TextStyle(color: Colors.grey[500], fontSize: 11)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _getIconForName(String name) {
    final lower = name.toLowerCase();
    if (lower.contains('python')) return '🐍';
    if (lower.contains('data')) return '📊';
    if (lower.contains('dart') || lower.contains('flutter')) return '💙';
    if (lower.contains('math') || lower.contains('algebra')) return '📐';
    return '🎓';
  }
}
