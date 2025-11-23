import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/dashboard/domain/bloc/dashboard_bloc.dart';
import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  // TODO: Get a real ID with AuthBloc
  final String _studentId = "d3172e75-37c3-4eac-8800-a298f9e61840";

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) =>
          DashboardBloc(repository: context.di.repositories.learningPathRepository)
            ..add(DashboardLoadRequested(_studentId)),
      child: const _DashboardView(),
    );
  }
}

class _DashboardView extends StatelessWidget {
  const _DashboardView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: RefreshIndicator(
        onRefresh: () async {
          // TODO: Get a real ID
          context.read<DashboardBloc>().add(const DashboardLoadRequested("d3172e75-37c3-4eac-8800-a298f9e61840"));
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const _HeaderSection(),
            const SizedBox(height: 24),
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
            const _RecommendationsList(),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => context.pushNamed('goals'),
              icon: const Icon(Icons.add_road),
              label: const Text('Create a new trajectory'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(16)),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeaderSection extends StatelessWidget {
  const _HeaderSection();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue.shade800, Colors.blue.shade500],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Welcome back!',
            style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Text('Continue learning to achieve mastery.', style: TextStyle(color: Colors.white70)),
        ],
      ),
    );
  }
}

class _RecommendationsList extends StatelessWidget {
  const _RecommendationsList();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DashboardBloc, DashboardState>(
      builder: (context, state) {
        if (state is DashboardLoading) {
          return const SizedBox(height: 200, child: Center(child: CircularProgressIndicator()));
        }
        if (state is DashboardFailure) {
          return Container(
            height: 100,
            alignment: Alignment.center,
            color: Colors.red.shade50,
            child: Text('Error: ${state.error}', style: const TextStyle(color: Colors.red)),
          );
        }
        if (state is DashboardSuccess) {
          if (state.recommendations.isEmpty) {
            return const SizedBox(height: 100, child: Center(child: Text('No recommendations yet.')));
          }

          return SizedBox(
            height: 220,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: state.recommendations.length,
              separatorBuilder: (_, _) => const SizedBox(width: 12),
              itemBuilder: (context, index) {
                final step = state.recommendations[index];
                return _RecommendationCard(step: step);
              },
            ),
          );
        }
        return const SizedBox.shrink();
      },
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
