from pathlib import Path
from statistics import mean
import matplotlib.pyplot as plt


def extract_family(seq_id: str):
    if "_" not in seq_id:
        return seq_id
    return seq_id.rsplit("_", 1)[0]


def read_family_metrics(result_file: Path):
    families = {}

    with result_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or not line.startswith(">"):
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            id1 = parts[0][1:]
            id2 = parts[1]

            sensitivity = float(parts[-5])
            specificity = float(parts[-4])
            coverage = float(parts[-3])
            mse = float(parts[-2])
            inverse_mse = float(parts[-1])

            family1 = extract_family(id1)
            family2 = extract_family(id2)

            family = family1 if family1 == family2 else family1

            if family not in families:
                families[family] = {
                    "sensitivity": [],
                    "specificity": [],
                    "coverage": [],
                    "mse": [],
                    "inverse_mse": []
                }

            families[family]["sensitivity"].append(sensitivity)
            families[family]["specificity"].append(specificity)
            families[family]["coverage"].append(coverage)
            families[family]["mse"].append(mse)
            families[family]["inverse_mse"].append(inverse_mse)

    summary = {}

    for family, values in families.items():
        summary[family] = {
            "sensitivity": mean(values["sensitivity"]),
            "specificity": mean(values["specificity"]),
            "coverage": mean(values["coverage"]),
            "mse": mean(values["mse"]),
            "inverse_mse": mean(values["inverse_mse"]),
            "count": len(values["sensitivity"])
        }

    return summary


def print_rankings(run_name: str, family_summary):
    print(f"\n{run_name} - hardest families by MSE")
    hardest_by_mse = sorted(family_summary.items(), key=lambda x: x[1]["mse"], reverse=True)[:10]
    for family, values in hardest_by_mse:
        print(
            f"  {family:<25} "
            f"MSE={values['mse']:.4f} "
            f"Sens={values['sensitivity']:.4f} "
            f"n={values['count']}"
        )

    print(f"\n{run_name} - hardest families by sensitivity")
    hardest_by_sens = sorted(family_summary.items(), key=lambda x: x[1]["sensitivity"])[:10]
    for family, values in hardest_by_sens:
        print(
            f"  {family:<25} "
            f"Sens={values['sensitivity']:.4f} "
            f"MSE={values['mse']:.4f} "
            f"n={values['count']}"
        )

    print(f"\n{run_name} - easiest families by sensitivity")
    easiest_by_sens = sorted(family_summary.items(), key=lambda x: x[1]["sensitivity"], reverse=True)[:10]
    for family, values in easiest_by_sens:
        print(
            f"  {family:<25} "
            f"Sens={values['sensitivity']:.4f} "
            f"MSE={values['mse']:.4f} "
            f"n={values['count']}"
        )


def get_top_families_by_metric(summary, metric, top_n=10, reverse=True):
    ranked = sorted(summary.items(), key=lambda x: x[1][metric], reverse=reverse)
    return [family for family, _ in ranked[:top_n]]


def plot_family_comparison(summary_a, summary_b, run_a_name, run_b_name, families, metric, title, output_file: Path):
    families = [family for family in families if family in summary_a and family in summary_b]

    if not families:
        return

    values_a = [summary_a[family][metric] for family in families]
    values_b = [summary_b[family][metric] for family in families]

    x = list(range(len(families)))
    width = 0.35

    plt.figure(figsize=(12, 6))
    plt.bar([i - width / 2 for i in x], values_a, width=width, label=run_a_name)
    plt.bar([i + width / 2 for i in x], values_b, width=width, label=run_b_name)

    plt.xticks(x, families, rotation=45, ha="right")
    plt.ylabel(metric.upper())
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def plot_family_scatter(summary_a, summary_b, run_a_name, run_b_name, metric, output_file: Path):
    common_families = sorted(set(summary_a.keys()) & set(summary_b.keys()))

    if not common_families:
        return

    x = [summary_a[family][metric] for family in common_families]
    y = [summary_b[family][metric] for family in common_families]

    plt.figure(figsize=(7, 7))
    plt.scatter(x, y)

    min_val = min(x + y)
    max_val = max(x + y)
    plt.plot([min_val, max_val], [min_val, max_val])

    plt.xlabel(f"{run_a_name} {metric}")
    plt.ylabel(f"{run_b_name} {metric}")
    plt.title(f"Family mean {metric}: {run_a_name} vs {run_b_name}")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def run_comparison(run_a_name, run_b_name, output_dir: Path, plot_dir: Path):
    run_a_file = output_dir / f"{run_a_name}_validation_results.txt"
    run_b_file = output_dir / f"{run_b_name}_validation_results.txt"

    if not run_a_file.exists():
        print(f"Missing file: {run_a_file}")
        return

    if not run_b_file.exists():
        print(f"Missing file: {run_b_file}")
        return

    summary_a = read_family_metrics(run_a_file)
    summary_b = read_family_metrics(run_b_file)

    print_rankings(run_a_name, summary_a)
    print_rankings(run_b_name, summary_b)

    hardest_mse_families = get_top_families_by_metric(summary_a, "mse", top_n=10, reverse=True)
    plot_family_comparison(
        summary_a,
        summary_b,
        run_a_name,
        run_b_name,
        hardest_mse_families,
        "mse",
        f"Hardest families by MSE: {run_a_name} vs {run_b_name}",
        plot_dir / f"family_hardest_mse_{run_a_name}_vs_{run_b_name}.png"
    )

    hardest_sens_families = get_top_families_by_metric(summary_a, "sensitivity", top_n=10, reverse=False)
    plot_family_comparison(
        summary_a,
        summary_b,
        run_a_name,
        run_b_name,
        hardest_sens_families,
        "sensitivity",
        f"Hardest families by sensitivity: {run_a_name} vs {run_b_name}",
        plot_dir / f"family_hardest_sensitivity_{run_a_name}_vs_{run_b_name}.png"
    )

    plot_family_scatter(
        summary_a,
        summary_b,
        run_a_name,
        run_b_name,
        "mse",
        plot_dir / f"family_scatter_mse_{run_a_name}_vs_{run_b_name}.png"
    )

    plot_family_scatter(
        summary_a,
        summary_b,
        run_a_name,
        run_b_name,
        "sensitivity",
        plot_dir / f"family_scatter_sensitivity_{run_a_name}_vs_{run_b_name}.png"
    )


def main():
    output_dir = Path("output")
    plot_dir = Path("plots_family")
    plot_dir.mkdir(parents=True, exist_ok=True)

    run_comparison("Run_A", "Run_J", output_dir, plot_dir)
    run_comparison("Run_A", "Run_E", output_dir, plot_dir)

    print("\nDone. Plots written to plots_family/")


if __name__ == "__main__":
    main()
