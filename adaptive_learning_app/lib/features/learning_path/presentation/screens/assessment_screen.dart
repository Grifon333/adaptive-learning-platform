import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/assessment_bloc/assessment_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class AssessmentScreen extends StatelessWidget {
  const AssessmentScreen({required this.goalConceptId, super.key});

  final String goalConceptId;

  @override
  Widget build(BuildContext context) {
    final authState = context.read<AuthBloc>().state;
    final studentId = (authState is AuthAuthenticated) ? authState.userId : '';

    return BlocProvider(
      create: (context) =>
          AssessmentBloc(repository: context.di.repositories.learningPathRepository)
            ..add(AssessmentStarted(studentId: studentId, goalConceptId: goalConceptId)),
      child: const _AssessmentView(),
    );
  }
}

class _AssessmentView extends StatefulWidget {
  const _AssessmentView();

  @override
  State<_AssessmentView> createState() => _AssessmentViewState();
}

class _AssessmentViewState extends State<_AssessmentView> {
  final PageController _pageController = PageController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Initial Assessment')),
      body: BlocConsumer<AssessmentBloc, AssessmentState>(
        listener: (context, state) {
          if (state is AssessmentSuccess) {
            // Update the global path bloc so the dashboard/path list updates
            context.read<LearningPathBloc>().add(SelectExistingPath(state.path));

            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Path personalized successfully!'), backgroundColor: Colors.green),
            );
            // Navigate to the path screen
            context.goNamed('learning-path');
          } else if (state is AssessmentFailure) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text('Error: ${state.error}'), backgroundColor: Colors.red));
          }
        },
        builder: (context, state) {
          if (state is AssessmentLoading) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [CircularProgressIndicator(), SizedBox(height: 16), Text("Analyzing your results...")],
              ),
            );
          }
          if (state is AssessmentInProgress) {
            final questions = state.session.questions;
            return Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: LinearProgressIndicator(value: state.answers.length / questions.length),
                ),
                Expanded(
                  child: PageView.builder(
                    controller: _pageController,
                    physics: const NeverScrollableScrollPhysics(), // Disable swipe
                    itemCount: questions.length,
                    itemBuilder: (context, index) {
                      final q = questions[index];
                      return Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'Question ${index + 1}/${questions.length}',
                              style: Theme.of(context).textTheme.labelLarge,
                            ),
                            const SizedBox(height: 16),
                            Text(q.text, style: Theme.of(context).textTheme.titleLarge),
                            const SizedBox(height: 32),

                            RadioGroup(
                              groupValue: state.answers[q.id],
                              onChanged: (int? val) {
                                if (val != null) {
                                  context.read<AssessmentBloc>().add(
                                    AssessmentAnswered(questionId: q.id, optionIndex: val),
                                  );
                                }
                              },
                              child: Column(
                                children: List.generate(q.options.length, (optIndex) {
                                  final isSelected = state.answers[q.id] == optIndex;
                                  return Card(
                                    color: isSelected ? Colors.blue.shade50 : null,
                                    child: RadioListTile<int>(value: optIndex, title: Text(q.options[optIndex].text)),
                                  );
                                }),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      if (_pageController.hasClients && _pageController.page! > 0)
                        TextButton(
                          onPressed: () => _pageController.previousPage(
                            duration: const Duration(milliseconds: 300),
                            curve: Curves.easeInOut,
                          ),
                          child: const Text('Back'),
                        )
                      else
                        const SizedBox.shrink(),

                      ElevatedButton(
                        onPressed: () {
                          final currentPage = _pageController.page?.toInt() ?? 0;
                          final currentQ = questions[currentPage];

                          // Enforce answer
                          if (!state.answers.containsKey(currentQ.id)) {
                            ScaffoldMessenger.of(
                              context,
                            ).showSnackBar(const SnackBar(content: Text('Please select an answer')));
                            return;
                          }

                          if (currentPage < questions.length - 1) {
                            _pageController.nextPage(
                              duration: const Duration(milliseconds: 300),
                              curve: Curves.easeInOut,
                            );
                          } else {
                            // Submit
                            context.read<AssessmentBloc>().add(AssessmentSubmitted());
                          }
                        },
                        child: Text(
                          // Simple check if we are on the last page
                          // Note: PageController.page is double, use state index or length
                          (state.answers.length == questions.length &&
                                  (_pageController.hasClients && _pageController.page == questions.length - 1.0))
                              ? 'Submit'
                              : 'Next',
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}
