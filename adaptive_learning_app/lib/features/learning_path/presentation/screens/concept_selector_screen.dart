import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
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
  // List of available concepts (in reality - loaded from the API)
  final List<Map<String, String>> _concepts = [
    {'id': 'ff9eecf7-81fc-489d-9e8e-2f6360595f02', 'name': 'Python Basics'},
    {'id': '0b63688c-5068-4898-9831-7ead26d587b3', 'name': 'Lists, Dictionaries, Sets'},
    {'id': '674c74c6-8525-4a85-86ec-04ab12a032d2', 'name': 'Sorting and Searching'},
    {'id': 'de53b2dd-b583-4d9c-a190-65e83b26c2b6', 'name': 'Pandas and NumPy basics'},
    {'id': '21c3597d-b920-494f-b862-1f6da27da305', 'name': 'Dart basics for Flutter'},
    {'id': '45232220-1b22-4eba-a97f-e50606b2b5ef', 'name': 'Stateless and Stateful widgets'},
    {'id': '9a4c9a78-eca9-4395-8798-3f0956f95fad', 'name': 'State Management and Architecture'},
  ];

  String? _selectedStartId;
  String? _selectedEndId;

  @override
  Widget build(BuildContext context) {
    final bool needsStart = widget.mode == CreatePathMode.startEnd || widget.mode == CreatePathMode.startOnly;
    final bool needsEnd = widget.mode == CreatePathMode.startEnd || widget.mode == CreatePathMode.endOnly;

    return Scaffold(
      appBar: AppBar(title: const Text('Trajectory settings')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (needsStart) ...[
              const Text('Starting point (what do you already know?):', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              _buildDropdown(
                value: _selectedStartId,
                hint: 'Select start',
                onChanged: (val) => setState(() => _selectedStartId = val),
              ),
              const SizedBox(height: 24),
            ],

            if (needsEnd) ...[
              const Text('The end goal (what do you want to achieve?):', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              _buildDropdown(
                value: _selectedEndId,
                hint: 'Select a target',
                onChanged: (val) => setState(() => _selectedEndId = val),
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
                        if (context.mounted) {
                          context.pushNamed('assessment', extra: goalId);
                        }
                      } else {
                        // Standard generation (Previous logic)
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
      ),
    );
  }

  bool _canSubmit(bool needsStart, bool needsEnd) {
    if (needsStart && _selectedStartId == null) return false;
    if (needsEnd && _selectedEndId == null) return false;
    return true;
  }

  Widget _buildDropdown({required String? value, required String hint, required ValueChanged<String?> onChanged}) {
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
          items: _concepts.map((c) {
            return DropdownMenuItem(value: c['id'], child: Text(c['name']!));
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}
