#!/usr/bin/env python3
from math import sqrt
from pathlib import Path
import matplotlib.pyplot as plt


def parse_alignment_line(line: str):
    colon = line.find(":")
    if colon < 0:
        raise ValueError(f"Invalid alignment line, missing ':': {line}")

    seq_id = line[:colon].strip()
    sequence = line[colon + 1:].strip()

    if not seq_id or not sequence:
        raise ValueError(f"Invalid alignment line: {line}")

    return seq_id, sequence


def compute_reference_identity(ref_seq1: str, ref_seq2: str):
    aligned_positions = 0
    identical_positions = 0

    for c1, c2 in zip(ref_seq1, ref_seq2):
        if c1 == "-" or c2 == "-":
            continue

        aligned_positions += 1
        if c1 == c2:
            identical_positions += 1

    if aligned_positions == 0:
        return 0.0

    return identical_positions / aligned_positions


def pearson_correlation(x_values, y_values):
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0

    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)

    numerator = 0.0
    denom_x = 0.0
    denom_y = 0.0

    for x, y in zip(x_values, y_values):
        dx = x - mean_x
        dy = y - mean_y
        numerator += dx * dy
        denom_x += dx * dx
        denom_y += dy * dy

    if denom_x == 0.0 or denom_y == 0.0:
        return 0.0

    return numerator / sqrt(denom_x * denom_y)


def read_validation_data(result_file: Path):
    identities = []
    sensitivities = []
    specificities = []
    coverages = []
    mses = []
    inverse_mses = []

    with result_file.open("r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        if not line.startswith(">"):
            continue

        header = line
        parts = header.split()
        if len(parts) < 8:
            continue

        sensitivity = float(parts[-5])
        specificity = float(parts[-4])
        coverage = float(parts[-3])
        mse = float(parts[-2])
        inverse_mse = float(parts[-1])

        seq_lines = []
        while i < len(lines) and len(seq_lines) < 4:
            current = lines[i].strip()
            i += 1
            if current:
                seq_lines.append(current)

        if len(seq_lines) < 4:
            break

        _, ref_seq1 = parse_alignment_line(seq_lines[2])
        _, ref_seq2 = parse_alignment_line(seq_lines[3])

        identity = compute_reference_identity(ref_seq1, ref_seq2)

        identities.append(identity)
        sensitivities.append(sensitivity)
        specificities.append(specificity)
        coverages.append(coverage)
        mses.append(mse)
        inverse_mses.append(inverse_mse)

    return {
        "identity": identities,
        "sensitivity": sensitivities,
        "specificity": specificities,
        "coverage": coverages,
        "mse": mses,
        "inverse_mse": inverse_mses
    }


def plot_run_correlations(run_name: str, data, output_file: Path):
    x = data["identity"]

    metrics = [
        ("sensitivity", "Sensitivity"),
        ("specificity", "Specificity"),
        ("coverage", "Coverage"),
        ("mse", "MSE"),
        ("inverse_mse", "Inverse MSE")
    ]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()

    for idx, (key, label) in enumerate(metrics):
        y = data[key]
        r = pearson_correlation(x, y)

        axes[idx].scatter(x, y)
        axes[idx].set_title(f"{label} vs identity\nr = {r:.3f}")
        axes[idx].set_xlabel("Sequence identity")
        axes[idx].set_ylabel(label)

    # letztes Feld leer lassen
    axes[5].axis("off")

    fig.suptitle(f"{run_name}: sequence identity vs alignment quality", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def print_correlations(run_name: str, data):
    x = data["identity"]

    print(f"\n{run_name}")
    print(f"  Sensitivity   r = {pearson_correlation(x, data['sensitivity']):.4f}")
    print(f"  Specificity   r = {pearson_correlation(x, data['specificity']):.4f}")
    print(f"  Coverage      r = {pearson_correlation(x, data['coverage']):.4f}")
    print(f"  MSE           r = {pearson_correlation(x, data['mse']):.4f}")
    print(f"  Inverse MSE   r = {pearson_correlation(x, data['inverse_mse']):.4f}")


def main():
    output_dir = Path("output")
    plot_dir = Path("plots_identity")
    plot_dir.mkdir(parents=True, exist_ok=True)

    result_files = sorted(output_dir.glob("run_*_validation_results.txt"))

    if not result_files:
        print("No validation result files found.")
        return

    for result_file in result_files:
        run_name = result_file.stem.replace("_validation_results", "")
        data = read_validation_data(result_file)

        if not data["identity"]:
            print(f"Skipping {run_name}: no valid blocks found.")
            continue

        print_correlations(run_name, data)
        plot_run_correlations(run_name, data, plot_dir / f"{run_name}_identity_correlation.png")

    print("\nDone. Plots written to plots_identity/")


if __name__ == "__main__":
    main()
