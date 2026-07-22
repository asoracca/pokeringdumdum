# External-sampling MCCFR study

## Question

How does a sampled counterfactual-regret algorithm trade computation for
estimation noise when compared with deterministic full-tree CFR+?

## Why validate on Kuhn poker?

Kuhn poker has a small auditable tree and exact exploitability evaluation. That
makes it possible to detect a sampled solver that appears to learn but converges
to an exploitable policy. Moving directly to a larger game would remove this
strong correctness check.

## Algorithm

Each external-sampling iteration performs one traversal for each player. At the
traverser's information sets the algorithm evaluates every legal action. At
chance nodes and the opponent's information sets it samples one continuation.
The sampled counterfactual values update the traverser's regrets. The opponent's
reach-weighted strategy is accumulated for the reported average policy.

The implementation follows the external-sampling idea described by Lanctot et
al., *Monte Carlo Sampling for Regret Minimization in Extensive Games*:
https://papers.nips.cc/paper/2009/hash/00411460f7c92d2124a67ea0f4cb5f85-Abstract.html

## Experimental design

- checkpoints: 100, 500, 1,000, 5,000, and 10,000 iterations;
- external sampling: 20 independent seeded runs;
- comparator: one deterministic full-tree CFR+ trajectory;
- primary outcome: exact exploitability in chips per hand;
- secondary outcomes: player-zero profile value, terminal visits, and wall time;
- uncertainty: normal-approximation 95% intervals across sampled runs.

The wall-time comparison is descriptive and machine-dependent. An MCCFR
iteration performs two sampled traversals, whereas a full-tree iteration visits
all six deals and every continuation. Iteration counts are therefore not equal
units of work; iterations, terminal visits, and time should all be inspected.

## Interpretation limits

The study establishes behavior only for this implementation and tiny Kuhn poker.
It does not show that one method will dominate in Leduc or no-limit Hold'em.
Normal intervals over 20 seeds are approximate, and runtime measurements include
Python overhead. The next step is to record empirical results, profile hot paths,
and then transfer the verified sampled traversal to Leduc poker.
