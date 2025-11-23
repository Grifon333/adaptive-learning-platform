import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

class LessonScreen extends StatefulWidget {
  const LessonScreen({required this.step, super.key});

  final LearningStepDto step;

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  Future<void> _takeQuiz() async {
    final result = await context.pushNamed(
      'quiz',
      extra: {'stepId': widget.step.id, 'conceptId': widget.step.conceptId},
    );
    if (result == true && mounted) context.pop();
  }

  Future<void> _launchURL(String urlString) async {
    final Uri url = Uri.parse(urlString);
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not launch $urlString')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Step ${widget.step.stepNumber}')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Concept ID: ${widget.step.conceptId}',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            Text(
              'Learning Resources',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: widget.step.resources.isEmpty
                  ? const Center(child: Text('No resources available for this concept.'))
                  : ListView.separated(
                      itemCount: widget.step.resources.length,
                      separatorBuilder: (ctx, index) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final resource = widget.step.resources[index];
                        return _ResourceCard(resource: resource, onTap: () => _launchURL(resource.url));
                      },
                    ),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _takeQuiz,
              icon: const Icon(Icons.quiz),
              label: const Text('Take a knowledge test'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
            ),
          ],
        ),
      ),
    );
  }
}

class _ResourceCard extends StatelessWidget {
  const _ResourceCard({required this.resource, required this.onTap});

  final ResourceDto resource;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isVideo = resource.type.toLowerCase() == 'video';
    final icon = isVideo ? Icons.play_circle_fill : Icons.article;
    final color = isVideo ? Colors.redAccent : Colors.blueAccent;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Icon(icon, size: 40, color: color),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      resource.title,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${resource.type} • ${resource.duration} min',
                      style: TextStyle(color: Colors.grey[600], fontSize: 12),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.open_in_new, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }
}
