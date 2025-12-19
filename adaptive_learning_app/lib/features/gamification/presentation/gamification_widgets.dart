import 'package:adaptive_learning_app/features/gamification/dto/gamification_dtos.dart';
import 'package:flutter/material.dart';

// --- WIDGET 1: DASHBOARD CARD ---

class GamificationSummaryCard extends StatelessWidget {
  const GamificationSummaryCard({required this.userLevel, required this.currentStreak, required this.onTap, super.key});

  final UserLevel userLevel;
  final int currentStreak;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              // Level Circle
              Stack(
                alignment: Alignment.center,
                children: [
                  CircularProgressIndicator(
                    value: userLevel.progress,
                    strokeWidth: 6,
                    backgroundColor: theme.colorScheme.surfaceContainerHigh,
                    color: theme.colorScheme.primary,
                  ),
                  Text(
                    '${userLevel.currentLevel}',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 16),

              // Text Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      userLevel.levelTitle,
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      '${userLevel.currentXp}/${userLevel.xpToNextLevel} XP to Level ${userLevel.currentLevel + 1}',
                      style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
                    ),
                  ],
                ),
              ),

              // Streak Flame
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.orange.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.orange.withValues(alpha: 0.5)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.local_fire_department, color: Colors.orange, size: 20),
                    const SizedBox(width: 4),
                    Text(
                      '$currentStreak',
                      style: theme.textTheme.labelLarge?.copyWith(
                        color: Colors.orange[800],
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// --- WIDGET 2: BADGE GRID ITEM ---

class AchievementBadgeWidget extends StatelessWidget {
  const AchievementBadgeWidget({required this.achievement, super.key});
  final Achievement achievement;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUnlocked = achievement.isUnlocked;
    final color = isUnlocked ? _getBadgeColor(achievement.type) : theme.colorScheme.outlineVariant;

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: color.withValues(alpha: 0.2),
            border: Border.all(color: color, width: isUnlocked ? 2 : 1),
            boxShadow: isUnlocked
                ? [BoxShadow(color: color.withValues(alpha: 0.3), blurRadius: 8, spreadRadius: 2)]
                : [],
          ),
          child: Icon(
            isUnlocked ? _getBadgeIcon(achievement.type) : Icons.lock,
            color: isUnlocked ? color : theme.colorScheme.outline,
            size: 32,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          achievement.title,
          textAlign: TextAlign.center,
          style: theme.textTheme.labelMedium?.copyWith(
            fontWeight: isUnlocked ? FontWeight.bold : FontWeight.normal,
            color: isUnlocked ? theme.colorScheme.onSurface : theme.colorScheme.outline,
          ),
        ),
      ],
    );
  }

  Color _getBadgeColor(BadgeType type) {
    switch (type) {
      case BadgeType.weekWarrior:
        return Colors.orange;
      case BadgeType.conceptMaster:
        return Colors.purple;
      case BadgeType.scholar:
        return Colors.blue;
      case BadgeType.firstStep:
        return Colors.green;
      default:
        return Colors.indigo;
    }
  }

  IconData _getBadgeIcon(BadgeType type) {
    switch (type) {
      case BadgeType.weekWarrior:
        return Icons.bolt;
      case BadgeType.conceptMaster:
        return Icons.school;
      case BadgeType.scholar:
        return Icons.auto_stories;
      case BadgeType.firstStep:
        return Icons.flag;
      case BadgeType.resilient:
        return Icons.shield;
      default:
        return Icons.star;
    }
  }
}
