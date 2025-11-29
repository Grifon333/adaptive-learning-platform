import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

// Enum for creation types
enum CreatePathMode { startEnd, endOnly, startOnly, manual }

class CreatePathModeScreen extends StatelessWidget {
  const CreatePathModeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('New trajectory')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Select a creation method', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          _ModeCard(
            title: 'The path "From A to Z"',
            description: 'Indicate what you know now and what you want to achieve.',
            icon: Icons.map,
            color: Colors.blue,
            mode: CreatePathMode.startEnd,
          ),
          const SizedBox(height: 16),
          _ModeCard(
            title: 'Specify only the Goal',
            description: 'The system will find the best start to achieve the goal.',
            icon: Icons.flag,
            color: Colors.redAccent,
            mode: CreatePathMode.endOnly,
          ),
          const SizedBox(height: 16),
          _ModeCard(
            title: 'Specify only Start',
            description: 'Start with a topic and move forward, discovering new things (the tree of knowledge).',
            icon: Icons.trip_origin,
            color: Colors.green,
            mode: CreatePathMode.startOnly,
          ),
          const SizedBox(height: 16),
          _ModeCard(
            title: 'Designer',
            description: 'Create your own path by adding topics manually.',
            icon: Icons.build,
            color: Colors.orange,
            mode: CreatePathMode.manual,
          ),
        ],
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  const _ModeCard({
    required this.title,
    required this.description,
    required this.icon,
    required this.color,
    required this.mode,
  });

  final String title;
  final String description;
  final IconData icon;
  final Color color;
  final CreatePathMode mode;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          if (mode == CreatePathMode.manual) {
            ScaffoldMessenger.of(context).clearSnackBars();
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(const SnackBar(content: Text('Trajectory designer in development')));
          } else if (mode == CreatePathMode.startOnly) {
            // The backend does not yet support Forward Expansion.
            ScaffoldMessenger.of(context).clearSnackBars();
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(const SnackBar(content: Text('"Start Only" mode will be available soon!')));
          } else {
            context.pushNamed('concept_selector', extra: mode);
          }
        },
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: color.withValues(alpha: 0.1), shape: BoxShape.circle),
                child: Icon(icon, color: color, size: 30),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(description, style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }
}
