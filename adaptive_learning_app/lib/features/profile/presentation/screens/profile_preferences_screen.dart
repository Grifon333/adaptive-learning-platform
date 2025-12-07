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
  // Cognitive
  late double _attention;
  late double _memory;

  // Learning Styles (VARK)
  late double _visual;
  late double _auditory;
  late double _reading;
  late double _kinesthetic;

  @override
  void initState() {
    super.initState();
    final cog = widget.profile.cognitiveProfile;
    final prefs = widget.profile.learningPreferences;

    _attention = (cog['attention'] as num?)?.toDouble() ?? 0.5;
    _memory = (cog['memory'] as num?)?.toDouble() ?? 0.5;

    _visual = (prefs['visual'] as num?)?.toDouble() ?? 0.25;
    _auditory = (prefs['auditory'] as num?)?.toDouble() ?? 0.25;
    _reading = (prefs['reading'] as num?)?.toDouble() ?? 0.25;
    _kinesthetic = (prefs['kinesthetic'] as num?)?.toDouble() ?? 0.25;
  }

  void _save() {
    context.read<ProfileBloc>().add(
      ProfileUpdateRequested(
        cognitiveProfile: {'attention': _attention, 'memory': _memory},
        learningPreferences: {
          'visual': _visual,
          'auditory': _auditory,
          'reading': _reading,
          'kinesthetic': _kinesthetic,
          'pace': 'medium',
        },
      ),
    );
    context.pop();
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Preferences updated successfully')));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Personalization Settings'),
        actions: [IconButton(icon: const Icon(Icons.check), onPressed: _save)],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _SectionHeader(title: 'Cognitive Profile', subtitle: 'AI uses this to adjust session length and complexity.'),
          _SliderWidget(
            label: 'Attention Span',
            icon: Icons.access_time,
            value: _attention,
            onChanged: (v) => setState(() => _attention = v),
          ),
          _SliderWidget(
            label: 'Memory Retention',
            icon: Icons.psychology,
            value: _memory,
            onChanged: (v) => setState(() => _memory = v),
          ),
          const Divider(height: 32),
          _SectionHeader(
            title: 'Learning Style (VARK)',
            subtitle: 'This influences the type of resources recommended (Video vs Text vs Interactive).',
          ),
          _SliderWidget(
            label: 'Visual (Video/Images)',
            icon: Icons.visibility,
            value: _visual,
            onChanged: (v) => setState(() => _visual = v),
          ),
          _SliderWidget(
            label: 'Auditory (Listening)',
            icon: Icons.headphones,
            value: _auditory,
            onChanged: (v) => setState(() => _auditory = v),
          ),
          _SliderWidget(
            label: 'Reading/Writing (Text)',
            icon: Icons.article,
            value: _reading,
            onChanged: (v) => setState(() => _reading = v),
          ),
          _SliderWidget(
            label: 'Kinesthetic (Interactive)',
            icon: Icons.touch_app,
            value: _kinesthetic,
            onChanged: (v) => setState(() => _kinesthetic = v),
          ),
          const SizedBox(height: 32),
          FilledButton.icon(
            onPressed: _save,
            icon: const Icon(Icons.save),
            label: const Text('Save Preferences'),
            style: FilledButton.styleFrom(padding: const EdgeInsets.all(16)),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600])),
        const SizedBox(height: 16),
      ],
    );
  }
}

class _SliderWidget extends StatelessWidget {
  const _SliderWidget({required this.label, required this.icon, required this.value, required this.onChanged});

  final String label;
  final IconData icon;
  final double value;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Icon(icon, size: 20, color: Colors.blueGrey),
            const SizedBox(width: 8),
            Expanded(
              child: Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
            ),
            Text('${(value * 100).toInt()}%', style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        Slider(value: value, onChanged: onChanged, activeColor: Colors.blue, inactiveColor: Colors.blue.shade50),
        const SizedBox(height: 8),
      ],
    );
  }
}
