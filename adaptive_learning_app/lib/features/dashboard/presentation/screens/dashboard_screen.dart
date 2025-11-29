import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/auth/domain/bloc/auth_bloc.dart';
import 'package:adaptive_learning_app/features/dashboard/data/dto/dashboard_dtos.dart';
import 'package:adaptive_learning_app/features/dashboard/domain/bloc/dashboard_bloc.dart';
import 'package:adaptive_learning_app/features/dashboard/presentation/widgets/activity_chart.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authState = context.read<AuthBloc>().state;
    String? studentId;
    if (authState is AuthAuthenticated) studentId = authState.userId;
    // Fallback, if something went wrong (or redirect to login)
    if (studentId == null) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    return BlocProvider(
      create: (context) => DashboardBloc(
        lpRepository: context.di.repositories.learningPathRepository,
        analyticsRepository: context.di.repositories.analyticsRepository,
      )..add(DashboardLoadRequested(studentId!)),
      child: _DashboardView(studentId: studentId),
    );
  }
}

class _DashboardView extends StatelessWidget {
  const _DashboardView({required this.studentId});

  final String studentId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: BlocBuilder<DashboardBloc, DashboardState>(
        builder: (context, state) {
          if (state is DashboardLoading) return const Center(child: CircularProgressIndicator());
          if (state is DashboardFailure) return Center(child: Text('Error: ${state.error}'));
          if (state is DashboardSuccess) {
            final analytics = state.analytics;
            return RefreshIndicator(
              onRefresh: () async {
                context.read<DashboardBloc>().add(DashboardLoadRequested(studentId));
              },
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // 1. Header with Stats
                  _AnalyticsHeader(analytics: analytics),
                  const SizedBox(height: 24),

                  // 2. Chart
                  Text('Activity (Last 7 Days)', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 16),
                  ActivityChart(data: analytics.activityChart),
                  const SizedBox(height: 24),

                  // 3. Recommendations
                  Text(
                    'Recommended for you',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Based on your knowledge and dependency graph',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  _RecommendationsList(recommendations: state.recommendations),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () => context.pushNamed('paths_list'),
                    icon: const Icon(Icons.list_alt),
                    label: const Text('List of trajectories'),
                    style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
                  ),
                ],
              ),
            );
          }
          return SizedBox.shrink();
        },
      ),
    );
  }
}

class _AnalyticsHeader extends StatelessWidget {
  const _AnalyticsHeader({required this.analytics});
  final DashboardDataDto analytics;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue.shade800, Colors.blue.shade600],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          const Text('Your Progress', style: TextStyle(color: Colors.white70, fontSize: 14)),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _StatItem(value: '${(analytics.averageMastery * 100).toInt()}%', label: 'Avg Mastery'),
              _StatItem(value: '${analytics.totalConceptsLearned}', label: 'Concepts'),
              _StatItem(value: '${analytics.currentStreak} 🔥', label: 'Day Streak'),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  const _StatItem({required this.value, required this.label});
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
        ),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
      ],
    );
  }
}

class _RecommendationsList extends StatelessWidget {
  const _RecommendationsList({required this.recommendations});
  final List<LearningStepDto> recommendations;

  @override
  Widget build(BuildContext context) {
    if (recommendations.isEmpty) {
      return const SizedBox(height: 100, child: Center(child: Text('No recommendations yet.')));
    }
    return SizedBox(
      height: 220,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: recommendations.length,
        separatorBuilder: (_, _) => const SizedBox(width: 12),
        itemBuilder: (context, index) => _RecommendationCard(step: recommendations[index]),
      ),
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({required this.step});

  final LearningStepDto step;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 180,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.grey.shade200, blurRadius: 8, offset: const Offset(0, 4))],
        border: Border.all(color: Colors.grey.shade100),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            // Let's move straight on to reviewing the materials.
            context.pushNamed(
              'lesson',
              extra: step, // use DTO
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: Colors.orange.shade50, borderRadius: BorderRadius.circular(8)),
                  child: const Icon(Icons.lightbulb, color: Colors.orange),
                ),
                const Spacer(),
                Text('Concept ID:', style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Colors.grey)),
                Text(
                  step.conceptId.substring(0, 8), // Display part of the ID or name, if available
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 8),
                Text('${step.resources.length} resources', style: const TextStyle(color: Colors.blue, fontSize: 12)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
