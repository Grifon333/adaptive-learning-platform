import math
from datetime import datetime
from typing import Any


class SequentialPatternMiner:
    """
    Implements Generalized Sequential Pattern (GSP) logic to identify
    behavioral archetypes from event streams (Section 9.5).
    """

    # Definitions of behavioral patterns (tokens)
    # Q_F: Quiz Fail, Q_P: Quiz Pass, H: Hint, V: Video, S: Skip
    GAMING_PATTERNS = [
        ["Q_F", "H", "Q_F"],  # Hint abuse: Fail -> Hint -> Fail immediately
        ["Q_F", "Q_F", "Q_F"],  # Brute force: Rapid guessing
        ["V_S", "Q_F"],  # Skipping video then failing
    ]

    PERSISTENCE_PATTERNS = [
        ["Q_F", "V", "Q_P"],  # Remediation: Fail -> Review -> Pass
        ["Q_F", "H", "Q_P"],  # Effective help-seeking
    ]

    @staticmethod
    def tokenize_event(event: dict[str, Any]) -> str:
        """
        Maps a raw event to a symbolic token for sequence mining.
        """
        evt_type = event.get("event_type")
        context = event.get("context", {})
        metadata = event.get("metadata", {})

        # Check correctness for quizzes
        is_correct = context.get("is_correct", False)

        # Check if video was skipped/short (duration < 10% of expected) -> V_S
        # For MVP we assume metadata['duration'] holds watched time
        duration = metadata.get("duration", 0)

        if evt_type == "QUIZ_SUBMIT":
            return "Q_P" if is_correct else "Q_F"
        elif evt_type == "HINT_REQUEST":
            return "H"
        elif evt_type == "VIDEO_COMPLETE":
            return "V"
        elif evt_type == "VIDEO_PLAY":
            # If duration is very short, treat as partial/skip
            if duration < 30:
                return "V_S"
            return "V"

        return "OTHER"

    @classmethod
    def mine_patterns(cls, events: list[dict[str, Any]], target_patterns: list[list[str]]) -> int:
        """
        Scans the event stream for occurrences of target patterns using a sliding window.
        Returns the total count of matches.
        """
        if not events:
            return 0

        # 1. Convert events to token sequence
        # Sort by time first to ensure sequence validity
        sorted_events = sorted(events, key=lambda x: x["timestamp"])
        tokens = [cls.tokenize_event(e) for e in sorted_events]

        match_count = 0
        n_tokens = len(tokens)

        # 2. Sliding Window Search
        for pattern in target_patterns:
            pat_len = len(pattern)
            if pat_len > n_tokens:
                continue

            for i in range(n_tokens - pat_len + 1):
                window = tokens[i : i + pat_len]
                if window == pattern:
                    match_count += 1

        return match_count


class BehavioralMathEngine:
    @staticmethod
    def calculate_procrastination_index(events: list[dict[str, Any]]) -> float:
        """
        Formula: p_idx = ln(1 + (t_start - t_assigned)_hours)
        """
        sorted_events = sorted(events, key=lambda x: x["timestamp"])
        delays = []
        last_assignment = None

        for event in sorted_events:
            evt_type = event.get("event_type")
            # Parse timestamp (handling potential Z vs +00:00 issues)
            ts_str = event["timestamp"].replace("Z", "+00:00")
            try:
                ts = datetime.fromisoformat(ts_str)
            except ValueError:
                continue

            if evt_type in ["PATH_GENERATED", "STEP_UNLOCKED", "TASK_ASSIGNED"]:
                last_assignment = ts
            elif evt_type in ["VIDEO_PLAY", "QUIZ_ATTEMPT"] and last_assignment:
                delta_hours = (ts - last_assignment).total_seconds() / 3600.0
                # Formula: ln(1 + delta)
                p_val = math.log(1 + max(0, delta_hours))
                delays.append(p_val)
                last_assignment = None

        if not delays:
            return 0.0

        return sum(delays) / len(delays)

    @staticmethod
    def calculate_gaming_score(events: list[dict[str, Any]]) -> float:
        """
        Hybrid Calculation combining Time Heuristics and Sequential Patterns.

        Formula:
        g_score = w1 * R_time + w2 * R_pattern

        where:
        - R_time: Ratio of actions with suspiciously low duration.
        - R_pattern: Density of gaming patterns (GSP) in the event stream.
        """
        if not events:
            return 0.0

        # 1. Time Heuristic
        gaming_actions = 0
        total_actions = 0
        min_video_time = 30
        min_quiz_time = 10

        for event in events:
            evt_type = event.get("event_type")
            meta = event.get("metadata", {})
            duration = meta.get("duration", 0)

            if evt_type in ["VIDEO_COMPLETE", "QUIZ_SUBMIT"]:
                total_actions += 1
                threshold = min_video_time if evt_type == "VIDEO_COMPLETE" else min_quiz_time
                if duration < threshold:
                    gaming_actions += 1

        r_time = (float(gaming_actions) / total_actions) if total_actions > 0 else 0.0

        # 2. Pattern Mining (New Logic - Section 9.5)
        # We look for "Gaming" patterns defined in the Miner
        pattern_matches = SequentialPatternMiner.mine_patterns(events, SequentialPatternMiner.GAMING_PATTERNS)

        # Normalize pattern count by total events (density)
        # We assume if > 10% of interactions match a gaming pattern, it's high gaming.
        r_pattern = min(1.0, pattern_matches / (len(events) * 0.1 or 1))

        # 3. Weighted Combination
        # We give slightly more weight to explicit patterns as they are stronger indicators
        w1, w2 = 0.4, 0.6
        final_score = (w1 * r_time) + (w2 * r_pattern)

        return round(final_score, 4)

    @staticmethod
    def calculate_engagement_score(events: list[dict[str, Any]]) -> float:
        """
        Frequency of events per day + Persistence Patterns.
        """
        if not events:
            return 0.0

        # Base activity score
        count = len(events)
        base_score = min(1.0, count / 50.0)

        # Boost score if "Persistence" patterns are found (e.g. Fail -> Learn -> Pass)
        persistence_matches = SequentialPatternMiner.mine_patterns(events, SequentialPatternMiner.PERSISTENCE_PATTERNS)

        # Bonus: up to 0.2 extra for persistence
        bonus = min(0.2, persistence_matches * 0.05)

        return min(1.0, base_score + bonus)

    @staticmethod
    def calculate_hint_rate(events: list[dict[str, Any]]) -> float:
        """
        Formula: hint_rate = (actions_with_hints / total_problem_steps)
        Events: HINT_REQUEST
        """
        total_attempts = 0
        hints_used = 0

        for event in events:
            evt_type = event.get("event_type")
            if evt_type in ["QUIZ_ATTEMPT", "EXERCISE_STEP", "QUIZ_SUBMIT"]:
                total_attempts += 1
            elif evt_type == "HINT_REQUEST":
                hints_used += 1

        if total_attempts == 0:
            return 0.0

        return min(1.0, hints_used / total_attempts)

    @staticmethod
    def calculate_recent_error_rate(events: list[dict[str, Any]]) -> float:
        """
        Formula: error_rate = (incorrect_attempts / total_attempts)
        Tracks recent frustration.
        """
        total = 0
        errors = 0

        for event in events:
            if event.get("event_type") == "QUIZ_SUBMIT":
                total += 1
                context = event.get("context", {})
                if not context.get("is_correct", False):
                    errors += 1

        if total == 0:
            return 0.0

        return float(errors) / total
