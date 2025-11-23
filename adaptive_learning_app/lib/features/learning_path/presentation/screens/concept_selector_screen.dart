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
    {'id': 'de53b2dd-b583-4d9c-a190-65e83b26c2b6', 'name': 'Data Science Intro'},
    {'id': '21c3597d-b920-494f-b862-1f6da27da305', 'name': 'Dart Language'},
    {'id': '9a4c9a78-eca9-4395-8798-3f0956f95fad', 'name': 'Flutter Advanced'},
    {'id': 'c1', 'name': 'Algorithms'},
    {'id': 'c2', 'name': 'Databases'},
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
                  ? () {
                      context.read<LearningPathBloc>().add(
                        GeneratePathRequested(startConceptId: _selectedStartId, goalConceptId: _selectedEndId ?? ''),
                      );
                      context.pushNamed('learning-path');
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
