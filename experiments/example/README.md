# Recorded example

Generated with `python -m pokeringdumdum.study` and `experiments/kuhn.json`.
The CSV contains every checkpoint, not a selected best seed or timing run.
Metadata captures Python, platform, exact source hashes and config. The revision
is the base commit; `dirty: true` indicates the measured source was a working diff.
Training times use a per-iteration monotonic timer; evaluation and checkpoint
serialization are excluded and reported separately. One deterministic trajectory
per algorithm per experiment is insufficient for runtime superiority claims.
The fixture is synthetic Kuhn poker; no historical or live inputs are used.
