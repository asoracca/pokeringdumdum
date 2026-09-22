# PokeringDumDum 🃏

An auditable Kuhn poker lab: Python CFR/CFR+, exact exploitability, measured
experiments, and a TypeScript explorer for decisions under hidden information.
Kuhn has three cards, two players and one bet size. This is not full Texas Hold’em
or a claim of real-money profitability.

## Run locally

Python 3.10+; no credentials, paid data or external services at runtime.

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
python -m pokeringdumdum.study
python -m pokeringdumdum.demo
```

Open **http://127.0.0.1:8765**. The compiled explorer and deterministic saved
strategy are checked in, so Node is not needed to run the demo. Select a private
card and public history, inspect action probabilities and cumulative regrets,
then play against the saved policy. The opponent’s private card stays on the
Python server until the hand ends. The policy sees only its own card and history.
The demo compares an always-bet/call policy with a learned mixture using exact
exploitability, explaining why aggression alone is exploitable.

## Measured experiments

`python -m pokeringdumdum.study --config experiments/kuhn.json` generates
`data/study/measurements.csv`, metadata and resumable JSON trainer checkpoints.
The config defines algorithms and increasing iteration/time checkpoints.
Iteration and training-wall-time budgets use separate trajectories. Timing stops
only between complete iterations and may overshoot by one iteration. Evaluation
and checkpoint I/O are timed separately and excluded from the training budget.
These are training-time comparisons, not end-to-end application latency.

Example measured on Python 3.12.14, macOS arm64 (one run; timings vary):

| Algorithm | Iterations | Training seconds | Exploitability (chips/hand) |
|---|---:|---:|---:|
| CFR | 10,000 | 1.1401 | 0.002318 |
| CFR+ | 10,000 | 0.9533 | 0.001142 |

These deterministic full-tree runs have no random seed or sampling uncertainty.
The independent time-budget experiment is in the same CSV, labeled `seconds`.
Raw example results and environment metadata are in `experiments/example/`.
Every run records input configuration, source hashes, revision/dirty status,
Python/package versions and platform. Synthetic inputs only; no live poker data.

## Architecture and validation

- `game.py`: rules, legal actions and net utilities.
- `cfr.py`: existing full-tree trainer and reach-weighted average strategy.
- `evaluation.py`: exact expected value and information-set-respecting best responses.
- `study.py`: budget runner, cumulative timing and checkpoint `snapshot`/`restore`.
- `export.py`: versioned JSON rules, policies, regrets and exact value reports.
- `demo.py`: local server, private hands and saved-policy decisions.
- `explorer/src/main.ts`: explanation UI; no trainer or duplicated payoff rules.

Tests independently enumerate terminal paths and all 64 pure responses per
player, check every deal/payoff, zero-sum utilities, information sets, invalid
policies/actions, checkpoint continuation, hidden-card handling and the export
schema. Three distinct equilibrium mixtures must have value −1/18 and zero
exploitability; no single mixture is treated as canonical.

The v1 contract is `explorer/strategy.schema.json`; tests validate structure and
semantic consistency, and the browser rejects unsupported versions or invalid
policy rows. To regenerate the fixture and compile edits:

```sh
python -m pokeringdumdum.export
cd explorer
pnpm install --frozen-lockfile
pnpm build
```

TypeScript is pinned to 5.9.3; pnpm 11.19.0 and Node 22 are used in CI. The original
plot experiment remains available as `python run_experiment.py`.
See [methodology](docs/METHODOLOGY.md) and [architecture](docs/ARCHITECTURE.md).

## Scope

The pending [PR #2](https://github.com/asoracca/pokeringdumdum/pull/2) already
contains external-sampling MCCFR and a separate educational Hold’em preflop lab.
This stage adds neither another sampling implementation nor another game.
Its sampling study should be reviewed and reused before extension; its existing
wall-time measurements include earlier evaluations between checkpoints and are
not directly comparable with this runner’s training-only clock. The preflop
charts are simplified abstractions, not a solved full Hold’em strategy.

No scaling or Rust speedup claims are made. The local HTTP server is a development
demo, not a production multiplayer service. Saved strategies and compiled assets
support offline use after Python setup. Wall-clock results vary with hardware,
scheduling and instrumentation; iteration outputs are deterministic.
