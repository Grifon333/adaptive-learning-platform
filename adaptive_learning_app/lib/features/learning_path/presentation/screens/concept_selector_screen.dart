import 'package:adaptive_learning_app/di/di_container.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/concept_dto.dart';
import 'package:adaptive_learning_app/features/learning_path/domain/bloc/learning_path_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/screens/create_path_mode_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class ConceptSelectorScreen extends StatefulWidget {
  const ConceptSelectorScreen({required this.mode, super.key});

  final CreatePathMode mode;

  @override
  State<ConceptSelectorScreen> createState() => _ConceptSelectorScreenState();
}

class _ConceptSelectorScreenState extends State<ConceptSelectorScreen> {
  late Future<List<ConceptDto>> _conceptsFuture;
  String? _selectedStartId;
  String? _selectedEndId;

  @override
  void initState() {
    super.initState();
    // Load concepts on init
    _conceptsFuture = context.read<DiContainer>().repositories.learningPathRepository.getConcepts();
  }

  @override
  Widget build(BuildContext context) {
    final bool needsStart = widget.mode == CreatePathMode.startEnd || widget.mode == CreatePathMode.startOnly;
    final bool needsEnd = widget.mode == CreatePathMode.startEnd || widget.mode == CreatePathMode.endOnly;

    return Scaffold(
      appBar: AppBar(title: const Text('Trajectory settings')),
      body: FutureBuilder<List<ConceptDto>>(
        future: _conceptsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Text('Failed to load concepts: ${snapshot.error}'),
                  TextButton(
                    onPressed: () => setState(() {
                      _conceptsFuture = context.read<DiContainer>().repositories.learningPathRepository.getConcepts();
                    }),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final concepts = snapshot.data ?? [];
          if (concepts.isEmpty) return const Center(child: Text("No learning concepts available yet."));

          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (needsStart) ...[
                  const Text(
                    'Starting point (what do you already know?):',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  _DropdownMenu(
                    value: _selectedStartId,
                    hint: 'Select start',
                    onChanged: (val) => setState(() => _selectedStartId = val),
                    concepts: concepts,
                  ),
                  const SizedBox(height: 24),
                ],

                if (needsEnd) ...[
                  const Text(
                    'The end goal (what do you want to achieve?):',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  _DropdownMenu(
                    value: _selectedEndId,
                    hint: 'Select a target',
                    onChanged: (val) => setState(() => _selectedEndId = val),
                    concepts: concepts,
                  ),
                ],

                const Spacer(),

                ElevatedButton(
                  onPressed: _canSubmit(needsStart, needsEnd)
                      ? () async {
                          final goalId = _selectedEndId ?? '';
                          if (goalId.isEmpty) return;

                          // Ask user about assessment
                          final result = await showDialog<bool>(
                            context: context,
                            builder: (context) => AlertDialog(
                              title: const Text('Personalize your path?'),
                              content: const Text(
                                'Would you like to take a short assessment to skip topics you already know?',
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(context, false), // No, just generate
                                  child: const Text('Skip'),
                                ),
                                FilledButton(
                                  onPressed: () => Navigator.pop(context, true), // Yes, start test
                                  child: const Text('Start Assessment'),
                                ),
                              ],
                            ),
                          );

                          if (result == true) {
                            if (context.mounted) context.pushNamed('adaptive_assessment', extra: goalId);
                          } else {
                            // Standard generation
                            final authState = context.read<AuthBloc>().state;
                            final studentId = (authState is AuthAuthenticated) ? authState.userId : '';
                            if (studentId.isEmpty) return;

                            if (context.mounted) {
                              context.read<LearningPathBloc>().add(
                                GeneratePathRequested(
                                  studentId: studentId,
                                  startConceptId: _selectedStartId,
                                  goalConceptId: goalId,
                                ),
                              );
                              context.pushNamed('learning-path');
                            }
                          }
                        }
                      : null,
                  style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
                  child: const Text('Generate trajectory'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  bool _canSubmit(bool needsStart, bool needsEnd) {
    if (needsStart && _selectedStartId == null) return false;
    if (needsEnd && _selectedEndId == null) return false;
    return true;
  }
}

class _DropdownMenu extends StatelessWidget {
  const _DropdownMenu({required this.value, required this.hint, required this.onChanged, required this.concepts});

  final String? value;
  final String hint;
  final ValueChanged<String?> onChanged;
  final List<ConceptDto> concepts;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey),
        borderRadius: BorderRadius.circular(8),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          hint: Text(hint),
          isExpanded: true,
          items: concepts.map((c) => DropdownMenuItem(value: c.id, child: Text(c.name))).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}
