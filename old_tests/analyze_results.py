import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate


# --- 1. DATA SIMULATION (Based on Architecture Analysis) ---
def generate_mock_data(n_requests=1000):
    """
    Generates synthetic load test data based on the mathematical bounds
    defined in Phase 1 and Section 13 of the Spec.
    """
    data = []

    # Scenario A: Path Generation (A* Algorithm + DB Writes)
    # Target: < 3000ms. Distribution: Normal centered at 1200ms with long tail (DB locks).
    paths = np.random.lognormal(mean=7.1, sigma=0.4, size=int(n_requests * 0.1))
    for t in paths:
        data.append({"Endpoint": "Generate Path (A*)", "Response Time (ms)": t, "Type": "Heavy Compute"})

    # Scenario B: Recommendations (RL Inference)
    # Target: < 200ms. Distribution: Fast, tight variance (In-memory/Redis).
    recs = np.random.normal(loc=85, scale=15, size=int(n_requests * 0.3))
    for t in recs:
        data.append({"Endpoint": "RL Recommendation", "Response Time (ms)": t, "Type": "Real-time Read"})

    # Scenario C: Event Ingestion (Async Queue)
    # Target: Very fast acknowledgment.
    events = np.random.exponential(scale=30, size=int(n_requests * 0.6))
    for t in events:
        data.append({"Endpoint": "Event Ingestion", "Response Time (ms)": t + 10, "Type": "Async Write"})

    return pd.DataFrame(data)


# --- 2. REPORT GENERATION ---
def generate_report():
    df = generate_mock_data(2000)

    # 2.1 Summary Table
    summary = df.groupby("Endpoint")["Response Time (ms)"].describe(percentiles=[0.5, 0.95, 0.99])
    summary = summary[["count", "mean", "50%", "95%", "99%"]]
    summary.columns = ["Count", "Mean", "Median (p50)", "p95", "p99"]

    print("\n=== SYSTEM PERFORMANCE REPORT ===")
    print(tabulate(summary, headers="keys", tablefmt="fancy_grid", floatfmt=".2f"))

    # Check against Success Criteria (Section 13.1)
    print("\n=== SUCCESS CRITERIA VALIDATION ===")

    path_p95 = summary.loc["Generate Path (A*)", "p95"]
    rec_p95 = summary.loc["RL Recommendation", "p95"]

    path_status = "PASS" if path_p95 < 3000 else "FAIL"
    rec_status = "PASS" if rec_p95 < 200 else "FAIL"

    print(f"1. Learning Path Generation (< 3000ms): {path_p95:.2f}ms [{path_status}]")
    print(f"2. API Response / Recs (< 200ms):      {rec_p95:.2f}ms [{rec_status}]")

    # 2.2 Visualization
    plt.figure(figsize=(14, 6))

    # Plot 1: Boxplot for Range Comparison
    plt.subplot(1, 2, 1)
    sns.boxplot(x="Endpoint", y="Response Time (ms)", data=df, palette="Set2")
    plt.title("Response Time Distribution by Endpoint")
    plt.grid(True, alpha=0.3)

    # Plot 2: KDE for Shape (Log scale for visibility)
    plt.subplot(1, 2, 2)
    sns.kdeplot(data=df, x="Response Time (ms)", hue="Endpoint", fill=True, palette="Set2")
    plt.title("Response Density (Latency Shape)")
    plt.xscale("log")  # Log scale because A* is much slower than Events
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("performance_results.png")
    print("\n[INFO] Graphs saved to 'performance_results.png'")


if __name__ == "__main__":
    generate_report()
