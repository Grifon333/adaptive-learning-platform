import 'dart:io';

import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_resource_dtos.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/repository/admin_graph_repository.dart';
import 'package:adaptive_learning_app/features/admin_graph/domain/resource_bloc/admin_resource_bloc.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class AdminResourceScreen extends StatelessWidget {
  const AdminResourceScreen({super.key, this.conceptIdToLink});

  final String? conceptIdToLink; // If provided, tapping a resource links it to this concept

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => AdminResourceBloc(
        repository: AdminGraphRepository(
          httpClient: context.read<DiContainer>().httpClient,
          appConfig: context.read<DiContainer>().appConfig,
        ),
      )..add(LoadResourcesRequested()),
      child: _ResourceView(conceptIdToLink: conceptIdToLink),
    );
  }
}

class _ResourceView extends StatelessWidget {
  const _ResourceView({this.conceptIdToLink});
  final String? conceptIdToLink;

  void _showEditor(BuildContext context, {AdminResourceDto? resource}) {
    final titleCtrl = TextEditingController(text: resource?.title ?? '');
    final urlCtrl = TextEditingController(text: resource?.url ?? '');
    final typeCtrl = TextEditingController(text: resource?.type ?? 'Video');
    final durCtrl = TextEditingController(text: resource?.duration.toString() ?? '10');

    // Local state for the dialog to handle UI updates during upload
    showDialog(
      context: context,
      barrierDismissible: false, // Prevent closing while uploading
      builder: (ctx) => BlocProvider.value(
        value: context.read<AdminResourceBloc>(), // Share the existing BLoC
        child: StatefulBuilder(
          builder: (context, setState) {
            return BlocConsumer<AdminResourceBloc, AdminResourceState>(
              listener: (context, state) {
                if (state is ResourceUploadSuccess) {
                  urlCtrl.text = state.url;
                  typeCtrl.text = state.detectedType;
                  ScaffoldMessenger.of(
                    context,
                  ).showSnackBar(const SnackBar(content: Text('File uploaded successfully!')));
                }
                if (state is ResourceError) {
                  ScaffoldMessenger.of(
                    context,
                  ).showSnackBar(SnackBar(content: Text(state.message), backgroundColor: Colors.red));
                }
              },
              builder: (context, state) {
                final isUploading = state is ResourceUploading;
                final progress = (state is ResourceUploading) ? state.progress : 0.0;

                return AlertDialog(
                  title: Text(resource == null ? 'New Resource' : 'Edit Resource'),
                  content: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // --- File Upload Section ---
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: isUploading
                                    ? null
                                    : () async {
                                        final FilePickerResult? result = await FilePicker.platform.pickFiles();
                                        if (result != null && result.files.single.path != null) {
                                          final file = File(result.files.single.path!);
                                          context.read<AdminResourceBloc>().add(UploadFileRequested(file));
                                        }
                                      },
                                icon: const Icon(Icons.upload_file),
                                label: const Text('Upload File'),
                              ),
                            ),
                          ],
                        ),
                        if (isUploading) ...[
                          const SizedBox(height: 8),
                          LinearProgressIndicator(value: progress),
                          Text('${(progress * 100).toInt()}% uploaded', style: const TextStyle(fontSize: 12)),
                        ],
                        const SizedBox(height: 16),
                        const Divider(),
                        const SizedBox(height: 16),

                        // --- Manual Fields ---
                        TextField(
                          controller: titleCtrl,
                          decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder()),
                          enabled: !isUploading,
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: urlCtrl,
                          decoration: const InputDecoration(
                            labelText: 'URL',
                            hintText: 'http://... or uploaded path',
                            border: OutlineInputBorder(),
                          ),
                          enabled: !isUploading,
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: typeCtrl,
                          decoration: const InputDecoration(
                            labelText: 'Type (Video/Book/Article)',
                            border: OutlineInputBorder(),
                          ),
                          enabled: !isUploading,
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: durCtrl,
                          decoration: const InputDecoration(labelText: 'Duration (min)', border: OutlineInputBorder()),
                          keyboardType: TextInputType.number,
                          enabled: !isUploading,
                        ),
                      ],
                    ),
                  ),
                  actions: [
                    TextButton(onPressed: isUploading ? null : () => Navigator.pop(ctx), child: const Text('Cancel')),
                    ElevatedButton(
                      onPressed: isUploading
                          ? null
                          : () {
                              if (titleCtrl.text.isEmpty || urlCtrl.text.isEmpty) {
                                ScaffoldMessenger.of(
                                  context,
                                ).showSnackBar(const SnackBar(content: Text('Title and URL are required')));
                                return;
                              }
                              final dto = AdminResourceDto(
                                id: resource?.id ?? '',
                                title: titleCtrl.text,
                                type: typeCtrl.text,
                                url: urlCtrl.text,
                                duration: int.tryParse(durCtrl.text) ?? 10,
                              );
                              context.read<AdminResourceBloc>().add(SaveResourceRequested(dto));
                              Navigator.pop(ctx);
                            },
                      child: const Text('Save'),
                    ),
                  ],
                );
              },
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(conceptIdToLink == null ? 'All Resources' : 'Select Resource to Link')),
      floatingActionButton: FloatingActionButton(onPressed: () => _showEditor(context), child: const Icon(Icons.add)),
      body: BlocConsumer<AdminResourceBloc, AdminResourceState>(
        listener: (context, state) {
          if (state is ResourceOperationSuccess) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text(state.message), backgroundColor: Colors.green));
            if (conceptIdToLink != null) Navigator.pop(context); // Close after linking
          }
          if (state is ResourceError) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text(state.message), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          if (state is ResourceLoading) return const Center(child: CircularProgressIndicator());
          if (state is ResourceLoaded) {
            if (state.resources.isEmpty) return const Center(child: Text('No resources found.'));

            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: state.resources.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final res = state.resources[index];
                return Card(
                  color: conceptIdToLink != null ? Colors.blue.shade50 : null,
                  child: ListTile(
                    leading: Icon(res.type.toLowerCase().contains('video') ? Icons.play_circle : Icons.article),
                    title: Text(res.title, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text('${res.duration} min | ${res.url}'),
                    onTap: conceptIdToLink != null
                        ? () {
                            context.read<AdminResourceBloc>().add(
                              LinkResourceRequested(conceptId: conceptIdToLink!, resourceId: res.id),
                            );
                          }
                        : null,
                    trailing: conceptIdToLink == null
                        ? PopupMenuButton(
                            itemBuilder: (_) => [
                              const PopupMenuItem(value: 'edit', child: Text('Edit')),
                              const PopupMenuItem(
                                value: 'delete',
                                child: Text('Delete', style: TextStyle(color: Colors.red)),
                              ),
                            ],
                            onSelected: (val) {
                              if (val == 'edit') _showEditor(context, resource: res);
                              if (val == 'delete') {
                                context.read<AdminResourceBloc>().add(DeleteResourceRequested(res.id));
                              }
                            },
                          )
                        : const Icon(Icons.add_link),
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
