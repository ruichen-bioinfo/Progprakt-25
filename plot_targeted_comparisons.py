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
        "Run_F": output_dir / "run_F_validation_results.txt",
        "Run_G": output_dir / "run_G_validation_results.txt",
        "Run_H": output_dir / "run_H_validation_results.txt",
        "Run_I": output_dir / "run_I_validation_results.txt",
        "Run_J": output_dir / "run_J_validation_results.txt",
        "Run_K": output_dir / "run_K_validation_results.txt",
        "Run_L": output_dir / "run_L_validation_results.txt",
        "Run_M": output_dir / "run_M_validation_results.txt",
        "Run_N": output_dir / "run_N_validation_results.txt",
        "Run_O": output_dir / "run_O_validation_results.txt",
        "Run_P": output_dir / "run_P_validation_results.txt",
        "Run_Q": output_dir / "run_Q_validation_results.txt"
    }

    all_summaries = {}

    for run_name, file_path in run_files.items():
        if not file_path.exists():
            continue

        metrics = read_metrics(file_path)
        all_summaries[run_name] = summarize_metrics(metrics)

    return all_summaries


def filter_existing_runs(all_summaries, run_names, labels):
    existing_runs = []
    existing_labels = []

    for run_name, label in zip(run_names, labels):
        if run_name in all_summaries:
            existing_runs.append(run_name)
            existing_labels.append(label)

    return existing_runs, existing_labels


def plot_quality_subset(all_summaries, run_names, labels, title, output_file: Path):
    run_names, labels = filter_existing_runs(all_summaries, run_names, labels)

    if not run_names:
        return

    sensitivity = [all_summaries[run]["sensitivity"] for run in run_names]
    specificity = [all_summaries[run]["specificity"] for run in run_names]
    coverage = [all_summaries[run]["coverage"] for run in run_names]

    x = list(range(len(run_names)))
    width = 0.25

    plt.figure(figsize=(9, 5))
    plt.bar([i - width for i in x], sensitivity, width=width, label="Sensitivity")
    plt.bar(x, specificity, width=width, label="Specificity")
    plt.bar([i + width for i in x], coverage, width=width, label="Coverage")

    plt.xticks(x, labels)
    plt.ylim(0, 1.05)
    plt.ylabel("Mean value")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def plot_shift_subset(all_summaries, run_names, labels, title, output_file: Path):
    run_names, labels = filter_existing_runs(all_summaries, run_names, labels)

    if not run_names:
        return

    mse = [all_summaries[run]["mse"] for run in run_names]
    inverse_mse = [all_summaries[run]["inverse_mse"] for run in run_names]

    x = list(range(len(run_names)))
    width = 0.35

    plt.figure(figsize=(9, 5))
    plt.bar([i - width / 2 for i in x], mse, width=width, label="MSE")
    plt.bar([i + width / 2 for i in x], inverse_mse, width=width, label="Inverse MSE")

    plt.xticks(x, labels)
    plt.ylabel("Mean value")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def main():
    output_dir = Path("output")
    plot_dir = Path("plots_targeted")
    plot_dir.mkdir(parents=True, exist_ok=True)

    all_summaries = collect_summaries(output_dir)

    # 1. Gotoh: Matrixvergleich
    matrix_runs = ["Run_A", "Run_B", "Run_D", "Run_G"]
    matrix_labels = ["BLOSUM62", "PAM250", "Dayhoff", "Blake-Cohen"]

    plot_quality_subset(
        all_summaries,
        matrix_runs,
        matrix_labels,
        "Gotoh: matrix comparison",
        plot_dir / "gotoh_matrix_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        matrix_runs,
        matrix_labels,
        "Gotoh: matrix comparison (shift metrics)",
        plot_dir / "gotoh_matrix_shift.png"
    )

    # 2. Gotoh: gap open Vergleich
    gap_runs = ["Run_H", "Run_C", "Run_A", "Run_I"]
    gap_labels = ["go=-8", "go=-10", "go=-12", "go=-14"]

    plot_quality_subset(
        all_summaries,
        gap_runs,
        gap_labels,
        "Gotoh + BLOSUM62: gap open comparison",
        plot_dir / "gap_open_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        gap_runs,
        gap_labels,
        "Gotoh + BLOSUM62: gap open comparison (shift metrics)",
        plot_dir / "gap_open_shift.png"
    )

    # 3. BLOSUM62: Gotoh vs Needleman-Wunsch
    blosum_algo_runs = ["Run_A", "Run_E"]
    blosum_algo_labels = ["Gotoh", "NW"]

    plot_quality_subset(
        all_summaries,
        blosum_algo_runs,
        blosum_algo_labels,
        "BLOSUM62: Gotoh vs Needleman-Wunsch",
        plot_dir / "blosum_algo_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        blosum_algo_runs,
        blosum_algo_labels,
        "BLOSUM62: Gotoh vs Needleman-Wunsch (shift metrics)",
        plot_dir / "blosum_algo_shift.png"
    )

    # 4. PAM250: Gotoh vs Needleman-Wunsch
    pam_algo_runs = ["Run_B", "Run_F"]
    pam_algo_labels = ["Gotoh", "NW"]

    plot_quality_subset(
        all_summaries,
        pam_algo_runs,
        pam_algo_labels,
        "PAM250: Gotoh vs Needleman-Wunsch",
        plot_dir / "pam_algo_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        pam_algo_runs,
        pam_algo_labels,
        "PAM250: Gotoh vs Needleman-Wunsch (shift metrics)",
        plot_dir / "pam_algo_shift.png"
    )


    # 5. Gotoh: gap extend Vergleich
    gap_extend_runs = ["Run_A", "Run_J", "Run_K"]
    gap_extend_labels = ["ge=-1", "ge=-2", "ge=-3"]

    plot_quality_subset(
        all_summaries,
        gap_extend_runs,
        gap_extend_labels,
        "Gotoh + BLOSUM62: gap extend comparison",
        plot_dir / "gap_extend_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        gap_extend_runs,
        gap_extend_labels,
        "Gotoh + BLOSUM62: gap extend comparison (shift metrics)",
        plot_dir / "gap_extend_shift.png"
    )


    # 6. BLOSUM62: global vs freeshift
    mode_runs = ["Run_A", "Run_L"]
    mode_labels = ["global", "freeshift"]

    plot_quality_subset(
        all_summaries,
        mode_runs,
        mode_labels,
        "BLOSUM62 + Gotoh: global vs freeshift",
        plot_dir / "mode_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        mode_runs,
        mode_labels,
        "BLOSUM62 + Gotoh: global vs freeshift (shift metrics)",
        plot_dir / "mode_shift.png"
    )


    # 7. PAM250: global vs freeshift
    pam_mode_runs = ["Run_B", "Run_M"]
    pam_mode_labels = ["global", "freeshift"]

    plot_quality_subset(
        all_summaries,
        pam_mode_runs,
        pam_mode_labels,
        "PAM250 + Gotoh: global vs freeshift",
        plot_dir / "pam_mode_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        pam_mode_runs,
        pam_mode_labels,
        "PAM250 + Gotoh: global vs freeshift (shift metrics)",
        plot_dir / "pam_mode_shift.png"
    )


    # 8. PAM250: refined gap tuning
    pam_refined_runs = ["Run_B", "Run_N", "Run_O", "Run_P", "Run_Q"]
    pam_refined_labels = [
        "go=-12 ge=-1",
        "go=-14 ge=-2",
        "go=-14 ge=-3",
        "go=-16 ge=-2",
        "go=-16 ge=-3"
    ]

    plot_quality_subset(
        all_summaries,
        pam_refined_runs,
        pam_refined_labels,
        "PAM250 + Gotoh: refined gap tuning",
        plot_dir / "pam_refined_quality.png"
    )
    plot_shift_subset(
        all_summaries,
        pam_refined_runs,
        pam_refined_labels,
        "PAM250 + Gotoh: refined gap tuning (shift metrics)",
        plot_dir / "pam_refined_shift.png"
    )

    print("Done. Plots written to plots_targeted/")


if __name__ == "__main__":
    main()
