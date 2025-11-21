import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

class QuizScreen extends StatefulWidget {
  const QuizScreen({required this.stepId, required this.conceptId, super.key});

  final String stepId;
  final String conceptId;

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  // TODO: In the future, this should come from the API along with the step details.
  final _question = "What is the main advantage of the BLoC pattern in Flutter?";
  final _options = [
    "Easy to use for beginners",
    "Separation of business logic and interface",
    "Built-in SQL support",
    "Automatic code generation",
  ];
  final _correctIndex = 1;

  int? _selectedOption;
  bool _isSubmitting = false;

  Future<void> _submitAnswer() async {
    if (_selectedOption == null) return;

    setState(() => _isSubmitting = true);

    final isCorrect = _selectedOption == _correctIndex;
    final score = isCorrect ? 1.0 : 0.0;

    try {
      final eventRepo = context.read<DiContainer>().repositories.eventRepository;

      // This event will be the trigger for the future ML service.
      await eventRepo.sendEvent(
        eventType: 'QUIZ_SUBMIT',
        metadata: {
          'step_id': widget.stepId,
          'concept_id': widget.conceptId,
          'is_correct': isCorrect,
          'score': score,
          'selected_option': _selectedOption,
        },
      );

      if (mounted) {
        if (isCorrect) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(const SnackBar(content: Text('Correct! Step completed.'), backgroundColor: Colors.green));
          // Return true to notify the previous screen of success
          context.pop(true);
        } else {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(const SnackBar(content: Text('Incorrect. Please try again.'), backgroundColor: Colors.red));
          setState(() => _isSubmitting = false);
        }
      }
    } on Object catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Sending error: $e'), backgroundColor: Colors.red));
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Knowledge check')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Concept: ${widget.conceptId.substring(0, 8)}...',
              style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Colors.grey),
            ),
            const SizedBox(height: 20),
            Text(_question, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
            const SizedBox(height: 20),

            RadioGroup<int>(
              groupValue: _selectedOption,
              onChanged: (int? val) {
                if (_isSubmitting) return;
                if (val != null) {
                  setState(() => _selectedOption = val);
                }
              },
              child: Column(
                children: List.generate(_options.length, (index) {
                  return RadioListTile<int>(title: Text(_options[index]), value: index);
                }),
              ),
            ),

            // ...List.generate(_options.length, (index) {
            //   return RadioListTile<int>(
            //     title: Text(_options[index]),
            //     value: index,
            //     groupValue: _selectedOption,
            //     onChanged: _isSubmitting ? null : (val) => setState(() => _selectedOption = val),
            //   );
            // }),
            const Spacer(),
            ElevatedButton(
              onPressed: (_selectedOption == null || _isSubmitting) ? null : _submitAnswer,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
                backgroundColor: Theme.of(context).primaryColor,
                foregroundColor: Colors.white,
              ),
              child: _isSubmitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Send answer'),
            ),
          ],
        ),
      ),
    );
  }
}
