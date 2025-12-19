enum BadgeType { firstStep, weekWarrior, conceptMaster, speedLearner, scholar, resilient, locked }

class Achievement {
  const Achievement({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    this.isUnlocked = false,
    this.unlockedAt,
  });
  final String id;
  final String title;
  final String description;
  final BadgeType type;
  final bool isUnlocked;
  final DateTime? unlockedAt; // Optional, if we had timestamps
}

class UserLevel {
  const UserLevel({
    required this.currentLevel,
    required this.levelTitle,
    required this.currentXp,
    required this.xpToNextLevel,
    required this.progress,
  });
  final int currentLevel;
  final String levelTitle;
  final int currentXp; // Mapped from concepts learned
  final int xpToNextLevel; // Threshold
  final double progress; // 0.0 to 1.0
}
