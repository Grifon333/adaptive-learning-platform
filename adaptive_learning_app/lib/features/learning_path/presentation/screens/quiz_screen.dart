import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/quiz_dtos.dart';
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
  late Future<List<QuizQuestionDto>> _quizFuture;

  int _currentQuestionIndex = 0;
  int? _selectedOptionIndex;
  bool _isSubmitting = false;
  int _correctAnswersCount = 0;

  @override
  void initState() {
    super.initState();
    _quizFuture = context.read<DiContainer>().repositories.learningPathRepository.getQuizForConcept(widget.conceptId);
  }

  Future<void> _submitAnswer(List<QuizQuestionDto> questions) async {
    if (_selectedOptionIndex == null) return;

    setState(() => _isSubmitting = true);

    final currentQuestion = questions[_currentQuestionIndex];
    final isCorrect = currentQuestion.options[_selectedOptionIndex!].isCorrect;

    if (isCorrect) _correctAnswersCount++;

    // If this is the last question, send the result.
    if (_currentQuestionIndex == questions.length - 1) {
      final score = _correctAnswersCount / questions.length;
      // We consider it passed if more than 60% are correct.
      final passed = score >= 0.6;

      try {
        final authState = context.read<AuthBloc>().state;
        final studentId = (authState is AuthAuthenticated) ? authState.userId : null;
        if (studentId == null) throw Exception("User not authenticated");
        final eventRepo = context.read<DiContainer>().repositories.eventRepository;
        await eventRepo.sendEvent(
          studentId: studentId,
          eventType: 'QUIZ_SUBMIT',
          metadata: {'step_id': widget.stepId, 'concept_id': widget.conceptId, 'is_correct': passed, 'score': score},
        );

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(passed ? 'Test passed!' : 'Test failed. Please try again.'),
              backgroundColor: passed ? Colors.green : Colors.red,
            ),
          );
          context.pop(passed);
        }
      } on Object catch (e) {
        // Error handling
        debugPrint(e.toString());
      }
    } else {
      // Let's move on to the next question.
      setState(() {
        _currentQuestionIndex++;
        _selectedOptionIndex = null;
        _isSubmitting = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Knowledge check')),
      body: FutureBuilder<List<QuizQuestionDto>>(
        future: _quizFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          final questions = snapshot.data!;
          if (questions.isEmpty) {
            return const Center(child: Text('There are no tests for this topic yet.'));
          }

          final question = questions[_currentQuestionIndex];

          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                LinearProgressIndicator(value: (_currentQuestionIndex + 1) / questions.length),
                const SizedBox(height: 8),
                Text('Question ${_currentQuestionIndex + 1} of ${questions.length}', textAlign: TextAlign.end),
                const SizedBox(height: 20),
                Text(question.text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                const SizedBox(height: 20),
                RadioGroup<int>(
                  groupValue: _selectedOptionIndex,
                  onChanged: (int? val) {
                    if (_isSubmitting) return;
                    if (val != null) setState(() => _selectedOptionIndex = val);
                  },
                  child: Column(
                    children: List.generate(question.options.length, (index) {
                      return RadioListTile<int>(title: Text(question.options[index].text), value: index);
                    }),
                  ),
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: (_selectedOptionIndex == null || _isSubmitting) ? null : () => _submitAnswer(questions),
                  style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
                  child: Text(_currentQuestionIndex == questions.length - 1 ? 'Complete the test' : 'Next question'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
