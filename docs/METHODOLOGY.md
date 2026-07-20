# Methodology

## Why Kuhn poker first?

Kuhn poker is a minimal imperfect-information game: each player sees a private
card, betting reveals information, bluffing is necessary, and an exact equilibrium
value is known. The entire game tree is small enough that every result can be
audited. That makes it a better first research environment than jumping directly
to no-limit hold'em and hiding mistakes behind a large simulation.

## Game

Two players ante one chip and receive one card from J, Q, K. Player zero may check
or bet. After a check, player one may check or bet; after a bet, the other player
may fold or call. A check-check showdown is worth one net chip and a called bet is
worth two.

## Algorithms

PokeringDumDum implements full-tree counterfactual regret minimization (CFR) and
regret-matching-plus (CFR+). Each iteration traverses all six ordered private-card
deals. Regret updates are accumulated across the full chance traversal before
being applied, so every decision in an iteration uses the same policy.

The reported strategy is the reach-weighted average strategy, not merely the final
regret-matched policy. CFR+ clips cumulative regrets below zero and uses linear
iteration weights in the average.

## Evaluation

Expected value is calculated by exact tree traversal. Best responses enumerate all
64 deterministic policies available to the responding player. This respects the
information constraint: a player chooses one action per information set and cannot
condition on the opponent's hidden card.

`NashConv` is the sum of both players' unilateral improvement opportunities.
Reported exploitability is `NashConv / 2`, in chips per hand. Lower is better and
zero is a Nash equilibrium.

At 50,000 iterations in the fixed experiment, vanilla CFR reaches approximately
0.0010 chips/hand exploitability and CFR+ reaches approximately 0.00048. These are
deterministic full-tree results, not averages selected from favorable random seeds.

## Limitations

Kuhn poker is not Texas Hold'em. It has three cards, a single bet size, and a tiny
game tree. The project demonstrates equilibrium reasoning and experimental rigor;
it does not claim to produce profitable real-money poker play. The natural next
step is Leduc poker, then sampled CFR variants—not a leap straight to a casino bot.
