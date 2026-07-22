"""Compare external-sampling MCCFR with deterministic full-tree CFR+."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from pokeringdumdum.mccfr_study import (
    run_external_sampling_study,
    run_full_tree_baseline,
)


def main() -> None:
    output = Path("data/mccfr")
    output.mkdir(parents=True, exist_ok=True)
    checkpoints = (100, 500, 1_000, 5_000, 10_000)

    sampled_runs, sampled_summary = run_external_sampling_study(
        checkpoints=checkpoints,
        seeds=range(20),
    )
    full_tree = run_full_tree_baseline(checkpoints)
    pd.DataFrame(sampled_runs).to_csv(output / "sampled_runs.csv", index=False)
    pd.DataFrame(sampled_summary).to_csv(output / "sampled_summary.csv", index=False)
    pd.DataFrame(full_tree).to_csv(output / "full_tree_baseline.csv", index=False)

    x = [int(row["iterations"]) for row in sampled_summary]
    mean = [float(row["mean_exploitability"]) for row in sampled_summary]
    low = [float(row["exploitability_ci95_low"]) for row in sampled_summary]
    high = [float(row["exploitability_ci95_high"]) for row in sampled_summary]
    baseline = [float(row["exploitability"]) for row in full_tree]

    figure, axis = plt.subplots(figsize=(8.5, 5.2))
    axis.plot(x, mean, marker="o", label="External-sampling MCCFR (20 seeds)")
    axis.fill_between(x, low, high, alpha=0.2)
    axis.plot(x, baseline, marker="s", label="Full-tree CFR+ (deterministic)")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Iterations")
    axis.set_ylabel("Exact exploitability (chips per hand)")
    axis.set_title("Kuhn poker convergence: sampling versus full traversal")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output / "mccfr_convergence.png", dpi=180)
    documentation_figure = Path("docs/assets/mccfr_convergence.png")
    documentation_figure.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(documentation_figure, dpi=180)
    plt.close(figure)

    print("EXTERNAL-SAMPLING MCCFR")
    for row in sampled_summary:
        print(
            f"{row['iterations']:>6} iterations  "
            f"mean exploitability={row['mean_exploitability']:.5f} "
            f"95% CI=[{row['exploitability_ci95_low']:.5f}, "
            f"{row['exploitability_ci95_high']:.5f}]  "
            f"mean time={row['mean_elapsed_seconds']:.3f}s"
        )
    print("\nFULL-TREE CFR+")
    for row in full_tree:
        print(
            f"{row['iterations']:>6} iterations  "
            f"exploitability={row['exploitability']:.5f}  "
            f"time={row['elapsed_seconds']:.3f}s  "
            f"terminal visits={row['terminal_visits']}"
        )
    print(f"\nSaved study outputs to {output}/")


if __name__ == "__main__":
    main()
