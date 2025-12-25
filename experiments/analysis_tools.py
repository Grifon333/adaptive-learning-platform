import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


def generate_visualizations():
    # 1. Load Data
    # Assumes the CSV is in the same directory or the current working directory
    file_path = "experiment_results.csv"
    if not os.path.exists(file_path):
        # Fallback to checking relative to project root if run from there
        file_path = "experiments/experiment_results.csv"

    if not os.path.exists(file_path):
        print(f"Error: Could not find '{file_path}'. Run the simulation first.")
        return

    df = pd.read_csv(file_path)

    # Rename groups for cleaner legends
    df["group"] = df["group"].replace({"static": "Control (Static)", "adaptive": "Experimental (Adaptive)"})

    # Global Style Settings for Academic Publication
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    palette = {"Control (Static)": "#e74c3c", "Experimental (Adaptive)": "#2ecc71"}

    # --- FIGURE 1: Student Persistence (Survival Proxy) ---
    plt.figure(figsize=(10, 6))

    # We use a Cumulative Distribution Function (CDF) to show the "drop-off" rate
    sns.ecdfplot(data=df, x="steps", hue="group", palette=palette, linewidth=2.5)

    plt.title("Student Survival Analysis: Steps Completed Before Dropout/Finish", fontsize=14, fontweight="bold")
    plt.xlabel("Number of Learning Steps Completed")
    plt.ylabel("Proportion of Students Remaining")
    plt.axvline(x=23, color="gray", linestyle="--", alpha=0.5, label="Avg Adaptive Steps")
    plt.legend(title="Group Location")

    plt.tight_layout()
    plt.savefig("fig1_persistence_survival.png", dpi=300)
    print("[Saved] fig1_persistence_survival.png")

    # --- FIGURE 2: Learning Effectiveness (Score Distribution) ---
    plt.figure(figsize=(8, 6))

    # Violin plot shows the density of scores better than a simple box plot
    sns.violinplot(data=df, x="group", y="avg_score", palette=palette, inner="quartile")

    plt.title("Comparison of Learning Effectiveness (Avg Quiz Scores)", fontsize=14, fontweight="bold")
    plt.xlabel("")
    plt.ylabel("Average Quiz Score (0.0 - 1.0)")
    plt.ylim(0, 1.0)

    plt.tight_layout()
    plt.savefig("fig2_score_distribution.png", dpi=300)
    print("[Saved] fig2_score_distribution.png")

    # --- FIGURE 3: Fatigue vs. Outcomes ---
    plt.figure(figsize=(10, 6))

    # Scatter plot with regression line to show correlation
    sns.scatterplot(data=df, x="steps", y="fatigue", hue="group", palette=palette, alpha=0.6, s=60)

    plt.title("Correlation: Study Duration vs. Final Fatigue", fontsize=14, fontweight="bold")
    plt.xlabel("Steps Taken")
    plt.ylabel("Final Fatigue Index (0-1)")
    plt.ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig("fig3_fatigue_analysis.png", dpi=300)
    print("[Saved] fig3_fatigue_analysis.png")


if __name__ == "__main__":
    generate_visualizations()
