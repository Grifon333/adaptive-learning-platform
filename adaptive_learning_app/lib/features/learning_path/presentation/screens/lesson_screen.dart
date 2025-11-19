import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

class LessonScreen extends StatefulWidget {
  const LessonScreen({required this.stepId, required this.conceptId, super.key});

  final String stepId;
  final String conceptId;

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  bool _isSubmitting = false;

  Future<void> _completeLesson() async {
    setState(() => _isSubmitting = true);

    try {
      final eventRepository = context.read<DiContainer>().repositories.eventRepository;

      await eventRepository.sendEvent(
        eventType: 'QUIZ_SUBMIT',
        metadata: {'step_id': widget.stepId, 'concept_id': widget.conceptId, 'score': 0.85, 'time_spent_seconds': 120},
      );

      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Result saved!'), backgroundColor: Colors.green));
        context.pop();
      }
    } on Object catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Lesson')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Learning concept: \n${widget.conceptId}', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 20),
            Expanded(
              child: Card(
                color: Colors.grey[100],
                child: const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.video_library, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('Here should be a video or lesson text...'),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text('Control question: What does this code do?', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _isSubmitting ? null : _completeLesson,
              icon: _isSubmitting ? const SizedBox.shrink() : const Icon(Icons.check),
              label: _isSubmitting
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Complete lesson and take quiz'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
            ),
          ],
        ),
      ),
    );
  }
}
