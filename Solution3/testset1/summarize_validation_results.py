#!/usr/bin/env python3
from pathlib import Path
from statistics import mean


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


def print_summary_table(all_summaries):
    print(
        f"{'Run':<8}"
        f"{'Sensitivity':>14}"
        f"{'Specificity':>14}"
        f"{'Coverage':>12}"
        f"{'MSE':>12}"
        f"{'Inv_MSE':>12}"
    )

    for run_name, summary in all_summaries.items():
        print(
            f"{run_name:<8}"
            f"{summary['sensitivity']:>14.4f}"
            f"{summary['specificity']:>14.4f}"
            f"{summary['coverage']:>12.4f}"
            f"{summary['mse']:>12.4f}"
            f"{summary['inverse_mse']:>12.4f}"
        )


def main():
    output_dir = Path("output")

    run_files = {
        "Run_A": output_dir / "run_A_validation_results.txt",
        "Run_B": output_dir / "run_B_validation_results.txt",
        "Run_C": output_dir / "run_C_validation_results.txt",
        "Run_D": output_dir / "run_D_validation_results.txt",
        "Run_E": output_dir / "run_E_validation_results.txt",
        "Run_F": output_dir / "run_F_validation_results.txt",
        "Run_G": output_dir / "run_G_validation_results.txt",
        "Run_H": output_dir / "run_H_validation_results.txt",
        "Run_I": output_dir / "run_I_validation_results.txt",
        "Run_J": output_dir / "run_J_validation_results.txt",
        "Run_K": output_dir / "run_K_validation_results.txt",
        "Run_L": output_dir / "run_L_validation_results.txt",
        "Run_M": output_dir / "run_M_validation_results.txt"
    }

    all_summaries = {}

    for run_name, file_path in run_files.items():
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            continue

        metrics = read_metrics(file_path)
        summary = summarize_metrics(metrics)
        all_summaries[run_name] = summary

    print_summary_table(all_summaries)


if __name__ == "__main__":
    main()
