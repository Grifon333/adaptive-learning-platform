import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_graph_dtos.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/repository/admin_graph_repository.dart';
import 'package:adaptive_learning_app/features/admin_graph/domain/graph_bloc/admin_graph_bloc.dart';
import 'package:adaptive_learning_app/features/admin_graph/presentation/screens/admin_resource_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class AdminGraphScreen extends StatelessWidget {
  const AdminGraphScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Inject Repository on the fly (or add to global DI if persistent)
    return BlocProvider(
      create: (context) => AdminGraphBloc(
        repository: AdminGraphRepository(
          httpClient: context.read<DiContainer>().httpClient,
          appConfig: context.read<DiContainer>().appConfig,
        ),
      )..add(LoadGraphRequested()),
      child: const _GraphView(),
    );
  }
}

class _GraphView extends StatelessWidget {
  const _GraphView();

  void _showConceptDialog(BuildContext context, {AdminConceptDto? concept}) {
    final nameController = TextEditingController(text: concept?.name ?? '');
    final descController = TextEditingController(text: concept?.description ?? '');
    final difficultyController = TextEditingController(text: concept?.difficulty.toString() ?? '1.0');
    final timeController = TextEditingController(text: concept?.estimatedTime.toString() ?? '30');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(concept == null ? 'New Concept' : 'Edit Concept'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Name'),
              ),
              TextField(
                controller: descController,
                decoration: const InputDecoration(labelText: 'Description'),
              ),
              TextField(
                controller: difficultyController,
                decoration: const InputDecoration(labelText: 'Difficulty (1-10)'),
                keyboardType: TextInputType.number,
              ),
              TextField(
                controller: timeController,
                decoration: const InputDecoration(labelText: 'Time (min)'),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              final diff = double.tryParse(difficultyController.text) ?? 1.0;
              final time = int.tryParse(timeController.text) ?? 30;

              if (concept == null) {
                context.read<AdminGraphBloc>().add(
                  CreateConceptRequested(nameController.text, descController.text, diff, time),
                );
              } else {
                final changes = AdminConceptDto(
                  id: concept.id,
                  name: nameController.text,
                  description: descController.text,
                  difficulty: diff,
                  estimatedTime: time,
                );
                context.read<AdminGraphBloc>().add(UpdateConceptRequested(concept.id, changes));
              }
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _showLinkDialog(BuildContext context, List<AdminConceptDto> concepts) {
    String? startId;
    String? endId;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Create Connection (Prerequisite)'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Start (Requirement) -> End (Goal)'),
              const SizedBox(height: 16),
              DropdownButton<String>(
                value: startId,
                hint: const Text('Select Start Concept'),
                isExpanded: true,
                items: concepts.map((c) => DropdownMenuItem(value: c.id, child: Text(c.name))).toList(),
                onChanged: (val) => setState(() => startId = val),
              ),
              const SizedBox(height: 16),
              const Icon(Icons.arrow_downward),
              const SizedBox(height: 16),
              DropdownButton<String>(
                value: endId,
                hint: const Text('Select Target Concept'),
                isExpanded: true,
                items: concepts.map((c) => DropdownMenuItem(value: c.id, child: Text(c.name))).toList(),
                onChanged: (val) => setState(() => endId = val),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: (startId != null && endId != null && startId != endId)
                  ? () {
                      context.read<AdminGraphBloc>().add(CreateLinkRequested(startId!, endId!));
                      Navigator.pop(ctx);
                    }
                  : null,
              child: const Text('Link'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Knowledge Graph Admin'),
        actions: [
          BlocBuilder<AdminGraphBloc, AdminGraphState>(
            builder: (context, state) {
              if (state is AdminGraphLoaded) {
                return IconButton(
                  icon: const Icon(Icons.link),
                  onPressed: () => _showLinkDialog(context, state.concepts),
                  tooltip: 'Link Concepts',
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showConceptDialog(context),
        child: const Icon(Icons.add),
      ),
      body: BlocConsumer<AdminGraphBloc, AdminGraphState>(
        listener: (context, state) {
          if (state is AdminGraphError) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text(state.message), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          if (state is AdminGraphLoading) return const Center(child: CircularProgressIndicator());

          if (state is AdminGraphLoaded) {
            if (state.concepts.isEmpty) return const Center(child: Text('No concepts found. Add one!'));

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: state.concepts.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final concept = state.concepts[index];
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(child: Text('${index + 1}')),
                    title: Text(concept.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('Time: ${concept.estimatedTime}m | Diff: ${concept.difficulty}'),
                    trailing: PopupMenuButton(
                      itemBuilder: (context) => [
                        const PopupMenuItem(value: 'resources', child: Text('Manage Resources')), // NEW
                        const PopupMenuItem(value: 'edit', child: Text('Edit Concept')),
                        const PopupMenuItem(
                          value: 'delete',
                          child: Text('Delete Concept', style: TextStyle(color: Colors.red)),
                        ),
                      ],
                      onSelected: (val) {
                        if (val == 'resources') {
                          // Navigate to Resource Screen in "Linking Mode"
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => AdminResourceScreen(conceptIdToLink: concept.id)),
                          );
                        } else if (val == 'edit') {
                          _showConceptDialog(context, concept: concept);
                        } else if (val == 'delete') {
                          context.read<AdminGraphBloc>().add(DeleteConceptRequested(concept.id));
                        }
                      },
                    ),
                  ),
                );
              },
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}
