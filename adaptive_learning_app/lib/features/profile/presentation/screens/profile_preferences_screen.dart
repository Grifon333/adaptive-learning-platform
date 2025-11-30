import 'package:adaptive_learning_app/features/profile/data/dto/student_profile_dto.dart';
import 'package:adaptive_learning_app/features/profile/domain/bloc/profile_bloc.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class ProfilePreferencesScreen extends StatefulWidget {
  const ProfilePreferencesScreen({required this.profile, super.key});
  final StudentProfileDto profile;

  @override
  State<ProfilePreferencesScreen> createState() => _ProfilePreferencesScreenState();
}

class _ProfilePreferencesScreenState extends State<ProfilePreferencesScreen> {
  late double _attention;
  late double _visual;
  late double _reading;

  @override
  void initState() {
    super.initState();
    _attention = (widget.profile.cognitiveProfile['attention'] as num?)?.toDouble() ?? 0.5;
    _visual = (widget.profile.learningPreferences['visual'] as num?)?.toDouble() ?? 0.5;
    _reading = (widget.profile.learningPreferences['reading'] as num?)?.toDouble() ?? 0.5;
  }

  void _save() {
    context.read<ProfileBloc>().add(
      ProfileUpdateRequested(
        cognitive: {'attention': _attention},
        preferences: {'visual': _visual, 'reading': _reading},
      ),
    );
    context.pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Personalization Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _SectionHeader('Cognitive Profile'),
          const Text('Affects estimated time and path complexity.'),
          _SliderWidget('Attention Span', _attention, (v) => setState(() => _attention = v)),
          const Divider(height: 32),
          _SectionHeader('Learning Style (VARK)'),
          const Text('Affects resource sorting (Video vs Text).'),
          _SliderWidget('Visual (Video preference)', _visual, (v) => setState(() => _visual = v)),
          _SliderWidget('Reading/Writing (Text preference)', _reading, (v) => setState(() => _reading = v)),
          const SizedBox(height: 32),
          ElevatedButton(onPressed: _save, child: const Text('Save Preferences')),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
    );
  }
}

class _SliderWidget extends StatelessWidget {
  const _SliderWidget(this.label, this.value, this.onChanged);

  final String label;
  final double value;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
            Text('${(value * 100).toInt()}%', style: const TextStyle(color: Colors.grey)),
          ],
        ),
        Slider(value: value, onChanged: onChanged),
      ],
    );
  }
}
