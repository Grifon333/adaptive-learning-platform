import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/adaptive_assessment_bloc/adaptive_assessment_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class AdaptiveAssessmentScreen extends StatelessWidget {
  const AdaptiveAssessmentScreen({required this.goalConceptId, super.key});

  final String goalConceptId;

  @override
  Widget build(BuildContext context) {
    final authState = context.read<AuthBloc>().state;
    final studentId = (authState is AuthAuthenticated) ? authState.userId : '';

    return BlocProvider(
      create: (context) =>
          AdaptiveAssessmentBloc(repository: context.di.repositories.learningPathRepository)
            ..add(AdaptiveAssessmentStarted(studentId: studentId, goalConceptId: goalConceptId)),
      child: const _AdaptiveAssessmentView(),
    );
  }
}

class _AdaptiveAssessmentView extends StatefulWidget {
  const _AdaptiveAssessmentView();

  @override
  State<_AdaptiveAssessmentView> createState() => _AdaptiveAssessmentViewState();
}

class _AdaptiveAssessmentViewState extends State<_AdaptiveAssessmentView> {
  int? _selectedOptionIndex;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Adaptive Assessment')),
      body: BlocConsumer<AdaptiveAssessmentBloc, AdaptiveAssessmentState>(
        listener: (context, state) {
          if (state is AdaptiveAssessmentSuccess) {
            _showSuccessDialog(context, state);
          } else if (state is AdaptiveAssessmentFailure) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text('Error: ${state.error}'), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          if (state is AdaptiveAssessmentLoading) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [CircularProgressIndicator(), SizedBox(height: 16), Text("Calibrating difficulty...")],
              ),
            );
          }

          if (state is AdaptiveAssessmentInProgress) {
            final question = state.sessionState.currentQuestion;
            if (question == null) return const Center(child: Text("Data error: No question loaded."));

            // Reset selection if we moved to a new question (based on object identity or text)
            // *Optimization*: In a real app, track question ID to reset properly.
            // Here we rely on the parent rebuilding.

            return Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Progress / Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Question ${state.questionNumber}',
                        style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Colors.grey),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(12)),
                        child: Row(
                          children: [
                            const Icon(Icons.show_chart, size: 16, color: Colors.blue),
                            const SizedBox(width: 4),
                            Text(
                              'Difficulty: ${question.difficulty.toStringAsFixed(1)}',
                              style: const TextStyle(fontSize: 12, color: Colors.blue, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Question Text
                  Text(
                    question.text,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 32),

                  // Options
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        children: List.generate(question.options.length, (index) {
                          final option = question.options[index];
                          final isSelected = _selectedOptionIndex == index;
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: InkWell(
                              onTap: state.isSubmitting ? null : () => setState(() => _selectedOptionIndex = index),
                              borderRadius: BorderRadius.circular(12),
                              child: Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: isSelected ? Colors.blue.shade50 : Colors.white,
                                  border: Border.all(color: isSelected ? Colors.blue : Colors.grey.shade300, width: 2),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Row(
                                  children: [
                                    Icon(
                                      isSelected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                                      color: isSelected ? Colors.blue : Colors.grey,
                                    ),
                                    const SizedBox(width: 16),
                                    Expanded(
                                      child: Text(
                                        option.text,
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          );
                        }),
                      ),
                    ),
                  ),

                  // Submit Button
                  ElevatedButton(
                    onPressed: (_selectedOptionIndex == null || state.isSubmitting)
                        ? null
                        : () {
                            context.read<AdaptiveAssessmentBloc>().add(
                              AdaptiveAssessmentAnswerSubmitted(_selectedOptionIndex!),
                            );
                            // Reset local selection for UI immediately or wait for BLoC?
                            // Better to wait for new state to reset, but simple setState nulling here
                            // might cause visual flash before new question loads.
                            // We will keep selection until new question arrives (handled by key or logic).
                            setState(() => _selectedOptionIndex = null);
                          },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.all(16),
                      textStyle: const TextStyle(fontSize: 18),
                    ),
                    child: state.isSubmitting
                        ? const SizedBox(
                            height: 24,
                            width: 24,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Submit Answer'),
                  ),
                ],
              ),
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }

  void _showSuccessDialog(BuildContext context, AdaptiveAssessmentSuccess state) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Assessment Complete'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.emoji_events, size: 64, color: Colors.amber),
            const SizedBox(height: 16),
            Text(
              'Your initial mastery: ${(state.finalMastery * 100).toInt()}%',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(state.message ?? 'Generating your personalized path...', textAlign: TextAlign.center),
          ],
        ),
        actions: [
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              // Trigger refresh of learning path list or dashboard
              final authState = context.read<AuthBloc>().state;
              if (authState is AuthAuthenticated) {
                context.read<LearningPathBloc>().add(LearningPathRefreshRequested(authState.userId));
              }
              // Go to Dashboard or Path list
              context.goNamed('dashboard');
            },
            child: const Text('Start Learning'),
          ),
        ],
      ),
    );
  }
}
