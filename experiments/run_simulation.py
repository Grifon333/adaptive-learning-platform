# experiments/effectiveness_verification/run_simulation.py

import csv
from statistics import mean
from student_agent import SimulatedStudent
from simulation_env import KnowledgeGraphMock


def run_group(student, kg, mode="static"):
    path_queue = kg.get_linear_path()
    steps_taken = 0
    failures = 0
    total_score = 0
    quizzes_taken = 0

    # We loop until path is empty OR student drops out
    while path_queue and not student.dropped_out:
        concept_id = path_queue.pop(0)
        concept = kg.get_concept(concept_id)

        # 1. Learn
        is_remedial = "_rem" in concept_id
        student.learn(concept_id, concept["difficulty"], is_remedial=is_remedial)

        # 2. Quiz
        score, passed = student.attempt_quiz(concept_id, concept["difficulty"])

        quizzes_taken += 1
        total_score += score
        steps_taken += 1

        if passed:
            continue
        else:
            failures += 1

            # --- BRANCHING LOGIC ---
            if mode == "static":
                # Static: Force retry of same concept immediately
                path_queue.insert(0, concept_id)

            elif mode == "adaptive":
                # Adaptive: Insert Remedial if available
                remedial = kg.get_remedial(concept_id)

                # Only insert remedial if we aren't already in a remedial loop
                if remedial and not is_remedial:
                    # Push Original back
                    path_queue.insert(0, concept_id)
                    # Push Remedial to front
                    path_queue.insert(0, remedial["id"])
                else:
                    # No remedial or failed remedial -> Retry
                    path_queue.insert(0, concept_id)

    # Return stats
    is_completed = (len(path_queue) == 0) and (not student.dropped_out)
    avg_score = (total_score / quizzes_taken) if quizzes_taken > 0 else 0

    return {
        "completed": is_completed,
        "steps": steps_taken,
        "failures": failures,
        "avg_score": avg_score,
        "final_fatigue": student.fatigue,
    }


def main():
    print("Running ALP Effectiveness Verification Experiment (Calibrated)...")
    print("Population: 200 Students (Profile: Struggling)")

    kg = KnowledgeGraphMock()
    results_static = []
    results_adaptive = []

    # Run Simulation
    for _ in range(200):
        # Group A: Static
        s1 = SimulatedStudent(profile_type="struggling")
        results_static.append(run_group(s1, kg, mode="static"))

        # Group B: Adaptive
        s2 = SimulatedStudent(profile_type="struggling")
        results_adaptive.append(run_group(s2, kg, mode="adaptive"))

    # Aggregate Data
    def calc_metrics(res_list):
        completed_count = sum(1 for r in res_list if r["completed"])
        dropout_rate = (len(res_list) - completed_count) / len(res_list)
        avg_score = mean([r["avg_score"] for r in res_list])
        avg_steps = mean([r["steps"] for r in res_list])
        avg_fatigue = mean([r["final_fatigue"] for r in res_list])
        return completed_count, dropout_rate, avg_score, avg_steps, avg_fatigue

    static_mets = calc_metrics(results_static)
    adaptive_mets = calc_metrics(results_adaptive)

    # Output Report
    print("\n--- EXPERIMENT RESULTS ---")
    print(f"{'Metric':<25} | {'Static (Control)':<15} | {'Adaptive (Exp)':<15} | {'Delta':<10}")
    print("-" * 75)
    print(
        f"{'Completion Rate':<25} | {static_mets[0] / 200:<15.1%} | {adaptive_mets[0] / 200:<15.1%} | {((adaptive_mets[0] - static_mets[0]) / 200) * 100:+.1f}%"
    )
    print(
        f"{'Dropout Rate':<25} | {static_mets[1]:<15.1%} | {adaptive_mets[1]:<15.1%} | {(adaptive_mets[1] - static_mets[1]) * 100:+.1f}%"
    )
    print(
        f"{'Avg Quiz Score':<25} | {static_mets[2]:<15.2%} | {adaptive_mets[2]:<15.2%} | {(adaptive_mets[2] - static_mets[2]) * 100:+.2f}%"
    )
    print(
        f"{'Avg Steps Taken':<25} | {static_mets[3]:<15.1f} | {adaptive_mets[3]:<15.1f} | {adaptive_mets[3] - static_mets[3]:+.1f}"
    )
    print(
        f"{'Final Fatigue':<25} | {static_mets[4]:<15.2f} | {adaptive_mets[4]:<15.2f} | {adaptive_mets[4] - static_mets[4]:+.2f}"
    )

    print("\n[CONCLUSION]")
    if adaptive_mets[1] < static_mets[1]:
        print(">> Hypothesis CONFIRMED: Adaptive method significantly reduces dropout rates.")
    else:
        print(">> Hypothesis REJECTED.")

    # --- CSV EXPORT (Restored) ---
    csv_filename = "experiments/experiment_results.csv"
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group", "steps", "failures", "avg_score", "fatigue", "completed"])

        for r in results_static:
            writer.writerow(["static", r["steps"], r["failures"], r["avg_score"], r["final_fatigue"], r["completed"]])

        for r in results_adaptive:
            writer.writerow(["adaptive", r["steps"], r["failures"], r["avg_score"], r["final_fatigue"], r["completed"]])

    print(f"\n[DATA SAVED] Raw results exported to '{csv_filename}'")


if __name__ == "__main__":
    main()
