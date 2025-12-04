import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/step_quiz_bloc/step_quiz_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class QuizScreen extends StatelessWidget {
  const QuizScreen({required this.stepId, required this.conceptId, super.key});

  final String stepId;
  final String conceptId;

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => StepQuizBloc(
        repository: context.di.repositories.learningPathRepository,
        trackingService: context.di.services.trackingService,
      )..add(LoadQuizRequested(conceptId: conceptId)),
      child: _QuizScreenView(stepId: stepId, conceptId: conceptId),
    );
  }
}

class _QuizScreenView extends StatefulWidget {
  const _QuizScreenView({required this.stepId, required this.conceptId});

  final String stepId;
  final String conceptId;

  @override
  State<_QuizScreenView> createState() => _QuizScreenViewState();
}

class _QuizScreenViewState extends State<_QuizScreenView> {
  int _currentQuestionIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Knowledge Check')),
      body: BlocConsumer<StepQuizBloc, StepQuizState>(
        listener: (context, state) {
          if (state is StepQuizSuccess) {
            _showResultDialog(context, state.result);
          }
          if (state is StepQuizFailure) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text(state.error), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          if (state is StepQuizLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is StepQuizLoaded) {
            final questions = state.questions;
            if (questions.isEmpty) return const SizedBox.shrink();

            final currentQuestion = questions[_currentQuestionIndex];
            final selectedOption = state.answers[currentQuestion.id];
            final isLastQuestion = _currentQuestionIndex == questions.length - 1;
            final canProceed = selectedOption != null;

            return Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  LinearProgressIndicator(
                    value: (_currentQuestionIndex + 1) / questions.length,
                    backgroundColor: Colors.grey.shade200,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Question ${_currentQuestionIndex + 1} of ${questions.length}',
                    textAlign: TextAlign.end,
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                  const SizedBox(height: 16),
                  Text(currentQuestion.text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 24),

                  // Options List
                  RadioGroup<int>(
                    groupValue: selectedOption,
                    onChanged: (int? val) {
                      if (!state.isSubmitting && val != null) {
                        context.read<StepQuizBloc>().add(
                          QuizAnswerSelected(questionId: currentQuestion.id, optionIndex: val),
                        );
                      }
                    },
                    child: Column(
                      children: List.generate(currentQuestion.options.length, (index) {
                        final option = currentQuestion.options[index];
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: RadioListTile<int>(
                            title: Text(option.text),
                            value: index,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                              side: BorderSide(color: selectedOption == index ? Colors.blue : Colors.grey.shade300),
                            ),
                            tileColor: selectedOption == index ? Colors.blue.shade50 : null,
                          ),
                        );
                      }),
                    ),
                  ),

                  const Spacer(),

                  ElevatedButton(
                    onPressed: !canProceed || state.isSubmitting
                        ? null
                        : () {
                            if (isLastQuestion) {
                              context.read<StepQuizBloc>().add(
                                SubmitQuizRequested(stepId: widget.stepId, conceptId: widget.conceptId),
                              );
                            } else {
                              setState(() {
                                _currentQuestionIndex++;
                              });
                            }
                          },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.all(16),
                      textStyle: const TextStyle(fontSize: 16),
                    ),
                    child: state.isSubmitting
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(isLastQuestion ? 'Submit Assessment' : 'Next Question'),
                  ),
                ],
              ),
            );
          }

          if (state is StepQuizFailure) {
            return Center(
              child: ElevatedButton(
                onPressed: () => context.read<StepQuizBloc>().add(LoadQuizRequested(conceptId: widget.conceptId)),
                child: const Text('Retry'),
              ),
            );
          }

          return const SizedBox.shrink();
        },
      ),
    );
  }

  void _showResultDialog(BuildContext context, dynamic resultDto) {
    // resultDto is StepQuizResultDto
    final passed = resultDto.passed;
    final adaptation = resultDto.adaptationOccurred;
    final scorePercent = (resultDto.score * 100).toInt();

    // Determine Dialog Content
    String title;
    IconData icon;
    Color color;
    String btnText;

    if (passed) {
      title = 'Congratulations!';
      icon = Icons.check_circle;
      color = Colors.green;
      btnText = 'Continue Path';
    } else if (adaptation) {
      title = 'Learning Path Adapted';
      icon = Icons.alt_route;
      color = Colors.orange;
      btnText = 'View New Steps';
    } else {
      title = 'Keep Learning';
      icon = Icons.warning_amber_rounded;
      color = Colors.redAccent;
      btnText = 'Review Material';
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 64),
            const SizedBox(height: 16),
            Text('Score: $scorePercent%', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(resultDto.message, textAlign: TextAlign.center),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx); // Close Dialog
              if (passed) {
                // Pass: Pop with true to indicate completion
                context.pop(true);
              } else if (adaptation) {
                // Adaptation: Pop with true (or special signal)
                // We want to force the LessonScreen to close so the user sees the updated path list.
                // Sending 'true' satisfies the LessonScreen's condition to context.pop().
                context.pop(true);
              } else {
                // Fail (No adaptation): Stay to review or pop false
                context.pop(false);
              }
            },
            child: Text(btnText),
          ),
        ],
      ),
    );
  }
}
