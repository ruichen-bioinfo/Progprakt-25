#!/usr/bin/env python3
from pathlib import Path
from statistics import mean
import matplotlib.pyplot as plt


def read_metrics(result_file: Path):
    metrics = {
        "sensitivity": [],
        "specificity": [],
        "coverage": [],
        "mse": [],
        "inverse_mse": []
    }

    with result_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or not line.startswith(">"):
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            metrics["sensitivity"].append(float(parts[-5]))
            metrics["specificity"].append(float(parts[-4]))
            metrics["coverage"].append(float(parts[-3]))
            metrics["mse"].append(float(parts[-2]))
            metrics["inverse_mse"].append(float(parts[-1]))

    return metrics


def summarize_metrics(metrics):
    summary = {}

    for name, values in metrics.items():
        if values:
            summary[name] = mean(values)
        else:
            summary[name] = 0.0

    return summary


def collect_summaries(output_dir: Path):
    run_files = {
        "Run_A": output_dir / "run_A_validation_results.txt",
        "Run_B": output_dir / "run_B_validation_results.txt",
        "Run_C": output_dir / "run_C_validation_results.txt",
        "Run_D": output_dir / "run_D_validation_results.txt",
        "Run_E": output_dir / "run_E_validation_results.txt",
        "Run_F": output_dir / "run_F_validation_results.txt"
    }

    all_summaries = {}

    for run_name, file_path in run_files.items():
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            continue

        metrics = read_metrics(file_path)
        summary = summarize_metrics(metrics)
        all_summaries[run_name] = summary

    return all_summaries


def plot_quality_metrics(all_summaries, output_file: Path):
    run_names = list(all_summaries.keys())

    sensitivity = [all_summaries[run]["sensitivity"] for run in run_names]
    specificity = [all_summaries[run]["specificity"] for run in run_names]
    coverage = [all_summaries[run]["coverage"] for run in run_names]

    x = list(range(len(run_names)))
    width = 0.25

    plt.figure(figsize=(10, 6))
    plt.bar([i - width for i in x], sensitivity, width=width, label="Sensitivity")
    plt.bar(x, specificity, width=width, label="Specificity")
    plt.bar([i + width for i in x], coverage, width=width, label="Coverage")

    plt.xticks(x, run_names)
    plt.ylim(0, 1.05)
    plt.ylabel("Mean value")
    plt.title("Mean sensitivity, specificity and coverage")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def plot_shift_metrics(all_summaries, output_file: Path):
    run_names = list(all_summaries.keys())

    mse = [all_summaries[run]["mse"] for run in run_names]
    inverse_mse = [all_summaries[run]["inverse_mse"] for run in run_names]

    x = list(range(len(run_names)))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar([i - width / 2 for i in x], mse, width=width, label="MSE")
    plt.bar([i + width / 2 for i in x], inverse_mse, width=width, label="Inverse MSE")

    plt.xticks(x, run_names)
    plt.ylabel("Mean value")
    plt.title("Mean shift error and inverse mean shift error")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def main():
    output_dir = Path("output")
    plot_dir = Path("plots")
    plot_dir.mkdir(parents=True, exist_ok=True)

    all_summaries = collect_summaries(output_dir)

    if not all_summaries:
        print("No summaries found.")
        return

    plot_quality_metrics(all_summaries, plot_dir / "quality_metrics.png")
    plot_shift_metrics(all_summaries, plot_dir / "shift_metrics.png")

    print("Done. Plots written to plots/")


if __name__ == "__main__":
    main()
