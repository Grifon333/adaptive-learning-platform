import math
from datetime import datetime
from typing import Any


class BehavioralMathEngine:
    """
    Implements the formulas from Section 9.2 of the Technical Specification.
    """

    @staticmethod
    def calculate_procrastination_index(events: list[dict[str, Any]]) -> float:
        """
        Formula: p_idx = ln(1 + (t_start - t_assigned)_hours)

        Logic:
        1. Find 'STEP_ASSIGNED' or 'PATH_GENERATED' events (t_assigned).
        2. Find the FIRST subsequent interaction (t_start).
        3. Compute delta in hours.
        """
        # Sort events by time just in case
        sorted_events = sorted(events, key=lambda x: x["timestamp"])

        delays = []
        last_assignment = None

        for event in sorted_events:
            evt_type = event.get("event_type")
            ts = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))

            if evt_type in ["PATH_GENERATED", "STEP_UNLOCKED", "TASK_ASSIGNED"]:
                last_assignment = ts
            elif evt_type in ["VIDEO_PLAY", "QUIZ_ATTEMPT"] and last_assignment:
                # Interaction found
                delta_hours = (ts - last_assignment).total_seconds() / 3600.0
                # Apply formula: ln(1 + delta)
                p_val = math.log(1 + delta_hours)
                delays.append(p_val)
                last_assignment = None  # Reset until next assignment

        if not delays:
            return 0.0

        # Return average delay index
        return sum(delays) / len(delays)

    @staticmethod
    def calculate_gaming_score(events: list[dict[str, Any]]) -> float:
        """
        Formula: g_score = sum(1 if t_duration < t_threshold) / w

        Logic:
        Check 'QUIZ_SUBMIT' or 'VIDEO_COMPLETE' events.
        If 'duration' (metadata) is suspiciously low compared to expected, flag it.
        """
        gaming_count = 0
        total_actions = 0

        # Hardcoded thresholds for MVP (should come from KG metadata in production)
        min_video_time = 30  # seconds
        min_quiz_time = 10  # seconds

        for event in events:
            evt_type = event.get("event_type")
            meta = event.get("metadata", {})
            duration = meta.get("duration", 0)  # Actual time spent

            is_gaming = False

            if evt_type == "VIDEO_COMPLETE":
                total_actions += 1
                if duration < min_video_time:
                    is_gaming = True

            elif evt_type == "QUIZ_SUBMIT":
                total_actions += 1
                if duration < min_quiz_time:
                    is_gaming = True

            if is_gaming:
                gaming_count += 1

        if total_actions == 0:
            return 0.0

        return float(gaming_count) / total_actions

    @staticmethod
    def calculate_engagement_score(events: list[dict[str, Any]]) -> float:
        """
        Simple heuristic: Frequency of events per day in the last window.
        """
        if not events:
            return 0.0

        count = len(events)
        # Normalize (e.g., 50 events is 1.0)
        return min(1.0, count / 50.0)

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

            if evt_type in ["QUIZ_ATTEMPT", "EXERCISE_STEP"]:
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
                # Assuming context.is_correct is available or implied by metadata
                context = event.get("context", {})
                if not context.get("is_correct", False):
                    errors += 1

        if total == 0:
            return 0.0

        return float(errors) / total
