"""Compare CFR and CFR+ convergence on Kuhn poker."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from pokeringdumdum.cfr import CFRTrainer
from pokeringdumdum.evaluation import exploitability
from pokeringdumdum.game import CARD_NAMES

OUTPUT_DIRECTORY = Path("data")
FIGURE_PATH = Path("docs/assets/convergence.png")
CHECKPOINTS = (10, 50, 100, 500, 1_000, 5_000, 10_000, 50_000)


def run_convergence() -> pd.DataFrame:
    rows = []
    for algorithm in ("cfr", "cfr_plus"):
        trainer = CFRTrainer(algorithm=algorithm)
        previous = 0
        for checkpoint in CHECKPOINTS:
            policy = trainer.train(checkpoint - previous)
            report = exploitability(policy)
            rows.append(
                {
                    "algorithm": algorithm,
                    "iterations": checkpoint,
                    "player_zero_value": report.profile_value_player_zero,
                    "exploitability": report.exploitability,
                    "nash_conv": report.nash_conv,
                }
            )
            previous = checkpoint
    return pd.DataFrame(rows)


def strategy_table(trainer: CFRTrainer) -> pd.DataFrame:
    rows = []
    for (player, card, history), probabilities in sorted(
        trainer.average_policy().items()
    ):
        rows.append(
            {
                "player": player,
                "card": CARD_NAMES[card],
                "history": history or "start",
                "pass_probability": probabilities[0],
                "bet_probability": probabilities[1],
            }
        )
    return pd.DataFrame(rows)


def save_plot(results: pd.DataFrame) -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 5))
    for algorithm, group in results.groupby("algorithm"):
        axis.plot(
            group["iterations"],
            group["exploitability"],
            marker="o",
            label={"cfr": "CFR", "cfr_plus": "CFR+"}[algorithm],
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Training iterations (log scale)")
    axis.set_ylabel("Exploitability in chips/hand (log scale)")
    axis.set_title("PokeringDumDum: Kuhn poker equilibrium convergence")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=160)
    plt.close(figure)


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    results = run_convergence()
    results.to_csv(OUTPUT_DIRECTORY / "convergence.csv", index=False)
    save_plot(results)

    final_trainer = CFRTrainer(algorithm="cfr_plus")
    final_trainer.train(CHECKPOINTS[-1])
    final_strategy = strategy_table(final_trainer)
    final_strategy.to_csv(OUTPUT_DIRECTORY / "final_strategy.csv", index=False)

    print("POKERINGDUMDUM CFR CONVERGENCE")
    print(results.to_string(index=False))
    print("\nCFR+ AVERAGE STRATEGY AT 50,000 ITERATIONS")
    print(final_strategy.to_string(index=False))
    print(f"\nSaved tables to {OUTPUT_DIRECTORY}/ and figure to {FIGURE_PATH}")


if __name__ == "__main__":
    main()
