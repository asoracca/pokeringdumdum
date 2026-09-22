"""Separate iteration and training-wall-clock experiments; no stochastic trainer."""

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

from pokeringdumdum.cfr import CFRTrainer, InfoSet
from pokeringdumdum.evaluation import exploitability


def snapshot(trainer):
    return {
        "version": 1,
        "algorithm": trainer.algorithm,
        "iterations": trainer.iterations,
        "averaging_delay": trainer.averaging_delay,
        "nodes": [
            {
                "key": list(k),
                "regrets": n.regret_sum.copy(),
                "sums": n.strategy_sum.copy(),
            }
            for k, n in sorted(trainer.info_sets.items())
        ],
    }


def restore(data):
    if data["version"] != 1:
        raise ValueError("unsupported checkpoint")
    trainer = CFRTrainer(data["algorithm"], data["averaging_delay"])
    trainer.iterations = data["iterations"]
    trainer.info_sets = {
        tuple(n["key"]): InfoSet(n["regrets"].copy(), n["sums"].copy())
        for n in data["nodes"]
    }
    return trainer


def validate_config(config):
    if set(config) != {"algorithms", "iterations", "seconds"}:
        raise ValueError("expected algorithms, iterations, seconds")
    if not config["algorithms"] or len(set(config["algorithms"])) != len(
        config["algorithms"]
    ):
        raise ValueError("algorithms must be unique and nonempty")
    for algorithm in config["algorithms"]:
        CFRTrainer(algorithm)
    for key in ("iterations", "seconds"):
        values = config[key]
        if not values or any(
            type(v) not in (int, float) or not math.isfinite(v) or v <= 0
            for v in values
        ):
            raise ValueError("budgets must be finite and positive")
        if sorted(set(values)) != values:
            raise ValueError("budgets must increase strictly")
    if any(type(v) is not int for v in config["iterations"]):
        raise ValueError("iteration budgets must be integers")


def run(config, output):
    validate_config(config)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for mode in ("iterations", "seconds"):
        for algorithm in config["algorithms"]:
            trainer = CFRTrainer(algorithm)
            elapsed = evaluation = checkpoint_time = 0.0
            for budget in config[mode]:
                while (
                    trainer.iterations < budget
                    if mode == "iterations"
                    else elapsed < budget
                ):
                    start = time.perf_counter()
                    trainer.train(1)
                    elapsed += time.perf_counter() - start
                start = time.perf_counter()
                report = exploitability(trainer.average_policy())
                evaluation += time.perf_counter() - start
                start = time.perf_counter()
                (output / f"{mode}-{algorithm}-{budget}.json").write_text(
                    json.dumps(snapshot(trainer), indent=2, allow_nan=False)
                )
                checkpoint_time += time.perf_counter() - start
                rows.append(
                    {
                        "experiment": mode,
                        "algorithm": algorithm,
                        "budget": budget,
                        "iterations": trainer.iterations,
                        "training_seconds": elapsed,
                        "evaluation_seconds": evaluation,
                        "checkpoint_seconds": checkpoint_time,
                        **asdict(report),
                    }
                )
    with (output / "measurements.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "config": config,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "seed": None,
        "seed_note": "Full-tree algorithms are deterministic; no RNG.",
        "input_kind": "synthetic exhaustive Kuhn game",
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True)
        ),
        "clock": "perf_counter; training only; one-iteration overshoot",
        "command_arguments": ["python", "-m", "pokeringdumdum.study", *sys.argv[1:]],
        "package_version": version("pokeringdumdum"),
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path("src/pokeringdumdum").glob("*.py"))
        },
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return rows


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/kuhn.json"))
    parser.add_argument("--output", type=Path, default=Path("data/study"))
    args = parser.parse_args()
    for row in run(json.loads(args.config.read_text()), args.output):
        print(
            f"{row['experiment']:10} {row['algorithm']:8} "
            f"{row['iterations']:6} iterations {row['training_seconds']:.4f}s "
            f"exploitability={row['exploitability']:.6f}"
        )


if __name__ == "__main__":
    main()
