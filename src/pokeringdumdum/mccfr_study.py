"""Reproducible convergence study for sampled and full-tree CFR."""

from __future__ import annotations

import math
import time
from collections.abc import Iterable, Sequence

from pokeringdumdum.cfr import CFRTrainer
from pokeringdumdum.evaluation import exploitability
from pokeringdumdum.mccfr import ExternalSamplingMCCFR


def _mean_ci(values: Sequence[float]) -> tuple[float, float, float]:
    if len(values) < 2:
        raise ValueError("at least two observations are required")
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    margin = 1.96 * math.sqrt(variance / len(values))
    return mean, mean - margin, mean + margin


def run_external_sampling_study(
    checkpoints: Iterable[int], seeds: Iterable[int]
) -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int | str]]]:
    """Run MCCFR over seeds and return raw and aggregated measurements."""
    points = tuple(checkpoints)
    seed_values = tuple(seeds)
    if not points or any(point < 1 for point in points):
        raise ValueError("checkpoints must be positive")
    if tuple(sorted(set(points))) != points:
        raise ValueError("checkpoints must be strictly increasing")
    if len(seed_values) < 2 or len(set(seed_values)) != len(seed_values):
        raise ValueError("at least two unique seeds are required")

    rows: list[dict[str, float | int | str]] = []
    for seed in seed_values:
        trainer = ExternalSamplingMCCFR(seed=seed)
        previous = 0
        started = time.perf_counter()
        for checkpoint in points:
            policy = trainer.train(checkpoint - previous)
            elapsed = time.perf_counter() - started
            report = exploitability(policy)
            rows.append(
                {
                    "algorithm": "external_sampling_mccfr",
                    "seed": seed,
                    "iterations": checkpoint,
                    "exploitability": report.exploitability,
                    "profile_value_player_zero": report.profile_value_player_zero,
                    "elapsed_seconds": elapsed,
                    "terminal_visits": trainer.terminal_visits,
                }
            )
            previous = checkpoint

    summary: list[dict[str, float | int | str]] = []
    for checkpoint in points:
        selected = [row for row in rows if row["iterations"] == checkpoint]
        values = [float(row["exploitability"]) for row in selected]
        runtimes = [float(row["elapsed_seconds"]) for row in selected]
        mean, low, high = _mean_ci(values)
        runtime_mean, runtime_low, runtime_high = _mean_ci(runtimes)
        summary.append(
            {
                "algorithm": "external_sampling_mccfr",
                "iterations": checkpoint,
                "runs": len(selected),
                "mean_exploitability": mean,
                "exploitability_ci95_low": low,
                "exploitability_ci95_high": high,
                "mean_elapsed_seconds": runtime_mean,
                "elapsed_ci95_low": runtime_low,
                "elapsed_ci95_high": runtime_high,
            }
        )
    return rows, summary


def run_full_tree_baseline(
    checkpoints: Iterable[int], algorithm: str = "cfr_plus"
) -> list[dict[str, float | int | str]]:
    """Run one deterministic full-tree trajectory at matching checkpoints."""
    points = tuple(checkpoints)
    if not points or tuple(sorted(set(points))) != points or points[0] < 1:
        raise ValueError("checkpoints must be strictly increasing and positive")
    trainer = CFRTrainer(algorithm)  # type: ignore[arg-type]
    rows: list[dict[str, float | int | str]] = []
    previous = 0
    started = time.perf_counter()
    for checkpoint in points:
        policy = trainer.train(checkpoint - previous)
        elapsed = time.perf_counter() - started
        report = exploitability(policy)
        rows.append(
            {
                "algorithm": algorithm,
                "seed": "deterministic",
                "iterations": checkpoint,
                "exploitability": report.exploitability,
                "profile_value_player_zero": report.profile_value_player_zero,
                "elapsed_seconds": elapsed,
                "terminal_visits": trainer.terminal_visits,
            }
        )
        previous = checkpoint
    return rows
