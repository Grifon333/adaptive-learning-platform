import 'package:adaptive_learning_app/features/dashboard/domain/bloc/dashboard_bloc.dart';
import 'package:adaptive_learning_app/features/gamification/domain/gamification_logic.dart';
import 'package:adaptive_learning_app/features/gamification/presentation/gamification_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class AchievementsScreen extends StatelessWidget {
  const AchievementsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Achievements')),
      body: BlocBuilder<DashboardBloc, DashboardState>(
        builder: (context, state) {
          if (state is! DashboardSuccess) {
            return const Center(child: CircularProgressIndicator());
          }

          final badges = GamificationEngine.getAchievements(state.analytics);
          final unlockedCount = badges.where((b) => b.isUnlocked).length;

          return Column(
            children: [
              // Header Stats
              Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  children: [
                    Text(
                      '$unlockedCount / ${badges.length}',
                      style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Text('Badges Unlocked'),
                  ],
                ),
              ),

              const Divider(),

              // Grid
              Expanded(
                child: GridView.builder(
                  padding: const EdgeInsets.all(16),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 3,
                    childAspectRatio: 0.8,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                  ),
                  itemCount: badges.length,
                  itemBuilder: (context, index) {
                    return Tooltip(
                      message: badges[index].description,
                      triggerMode: TooltipTriggerMode.tap,
                      child: AchievementBadgeWidget(achievement: badges[index]),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
