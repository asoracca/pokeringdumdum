# Measured Kuhn study and explorer

The original CFR update order is preserved: all six chance deals contribute
regret deltas before application. CFR+ clips accumulated regrets and uses linear
average weights. Public action probabilities come from that reach-weighted
average, while displayed regrets are the trainer’s cumulative update state.
These quantities answer different questions; regrets are not action EVs.

`study.run` starts a fresh trainer for each algorithm and experiment type. A
monotonic `perf_counter` brackets each complete iteration. Time targets are
cumulative training seconds; checkpoint evaluation and JSON serialization have
separate cumulative columns. This per-iteration instrumentation has overhead;
no statistical runtime superiority or scaling claim follows from one run.
Snapshots store iteration count, algorithm, averaging delay, regrets and strategy
sums. `restore(json.loads(path.read_text()))` continues the same deterministic
trajectory; elapsed timing belongs to an experiment and is not resumed.

The independent test oracle sums fixed terminal paths and independently computes
payoffs. For best responses it enumerates all pure information-set policies. This
avoids accidentally using the opponent’s card when maximizing an action. Kuhn
has multiple equilibria, checked at three distinct values of its free parameter.

Python exports a complete finite state table, actions, display labels, payoffs,
policy rows and reports. JSON schema v1 locks the interchange structure; Python
tests check schema plus legal-action consistency. TypeScript additionally checks
version, game, row uniqueness, probabilities and finite regret values at load.
Changing rules or schema requires regenerating the fixture and updating consumers.
CI regenerates both fixture and compiled JavaScript to detect stale artifacts.

The play server stores deals privately. API responses expose the human’s card and
public history, and reveal the opponent only on termination. Its policy lookup is
`(1, opponent_card, public_history)`; the human’s card never enters that key.
The server validates legal moves and uses Python utilities. A seeded `Hand` class
makes tests reproducible; interactive deals use fresh system-generated seeds.
The exported payoff table describes all possible deals, never the active deal.

Official references used for the implementation:
[Python 3.12 timing](https://docs.python.org/3.12/library/time.html),
[TypeScript strict checking](https://www.typescriptlang.org/tsconfig/strict), and
[JSON Schema validation](https://python-jsonschema.readthedocs.io/en/v4.26.0/validate/).
