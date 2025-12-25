import 'package:adaptive_learning_app/features/dashboard/data/dto/dashboard_dtos.dart';
import 'package:adaptive_learning_app/features/gamification/dto/gamification_dtos.dart';

// --- ENGINE (LOGIC) ---

class GamificationEngine {
  // Config: Level up every 5 concepts
  static const int _conceptsPerLevel = 5;

  /// Calculates User Level based on Total Concepts Learned
  static UserLevel calculateLevel(int totalConceptsLearned) {
    final level = 1 + (totalConceptsLearned ~/ _conceptsPerLevel);
    final currentLevelXp = totalConceptsLearned % _conceptsPerLevel;

    return UserLevel(
      currentLevel: level,
      levelTitle: _getLevelTitle(level),
      currentXp: currentLevelXp,
      xpToNextLevel: _conceptsPerLevel,
      progress: currentLevelXp / _conceptsPerLevel,
    );
  }

  /// Derives Badges based on Dashboard Metrics
  static List<Achievement> getAchievements(DashboardDataDto data) {
    final List<Achievement> badges = [
      Achievement(
        id: 'first_step',
        title: 'First Step',
        description: 'Complete your first learning concept.',
        type: BadgeType.firstStep,
        isUnlocked: data.totalConceptsLearned >= 1,
      ),
      Achievement(
        id: 'concept_master',
        title: 'Concept Master',
        description: 'Master 10 different concepts.',
        type: BadgeType.conceptMaster,
        isUnlocked: data.totalConceptsLearned >= 10,
      ),
      Achievement(
        id: 'week_warrior',
        title: 'Week Warrior',
        description: 'Maintain a 7-day learning streak.',
        type: BadgeType.weekWarrior,
        isUnlocked: data.currentStreak >= 7,
      ),
      Achievement(
        id: 'streak_starter',
        title: 'Streak Starter',
        description: 'Maintain a 3-day learning streak.',
        type: BadgeType.speedLearner, // Reusing icon type
        isUnlocked: data.currentStreak >= 3,
      ),
      Achievement(
        id: 'scholar',
        title: 'High Scholar',
        description: 'Achieve an average mastery > 80%.',
        type: BadgeType.scholar,
        isUnlocked: data.averageMastery >= 0.8,
      ),
      Achievement(
        id: 'resilient',
        title: 'Resilient',
        description: 'Keep going despite difficult topics.',
        type: BadgeType.resilient,
        isUnlocked: data.weakestConcepts.isNotEmpty && data.averageMastery > 0.5,
      ),
    ];
    // 1. First Step (First concept)
    // 2. Concept Master (10 concepts)
    // 3. Week Warrior (7 day streak)
    // 4. Streak Starter (3 day streak)
    // 5. Scholar (High Mastery)
    // 6. Resilient (Weakest concepts exist but overall progress is good)
    // Logic: Has weak concepts but mastery > 50%

    return badges;
  }

  static String _getLevelTitle(int level) {
    if (level < 5) return 'Novice';
    if (level < 10) return 'Apprentice';
    if (level < 20) return 'Adept';
    return 'Master';
  }
}
