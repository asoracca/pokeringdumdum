"""Independent terminal-path oracle: no production rule/evaluator traversal."""

import random
from itertools import permutations, product

import pytest

from pokeringdumdum.cfr import CFRTrainer
from pokeringdumdum.evaluation import (
    best_response_value_player_zero,
    expected_value,
    exploitability,
)
from pokeringdumdum.game import acting_player, terminal_utility_player_zero

KEYS = [(len(h) % 2, c, h) for h in ("", "p", "b", "pb") for c in range(3)]
PATHS = ("pp", "bp", "bb", "pbp", "pbb")


def oracle(policy):
    total = 0
    for a, b in permutations(range(3), 2):
        for path in PATHS:
            probability = 1 / 6
            for i, action in enumerate(path):
                key = (i % 2, (a, b)[i % 2], path[:i])
                probability *= policy[key][action == "b"]
            payoff = (
                1
                if path == "bp"
                else -1
                if path == "pbp"
                else ((1 if a > b else -1) * (1 if path == "pp" else 2))
            )
            total += probability * payoff
    return total


def test_independent_evaluation_and_best_responses():
    rng = random.Random(412)
    for _ in range(4):
        policy = {k: (p, 1 - p) for k in KEYS for p in [rng.random()]}
        assert expected_value(policy) == pytest.approx(oracle(policy))
        for player in (0, 1):
            keys = [k for k in KEYS if k[0] == player]
            values = [
                oracle(policy | dict(zip(keys, choices, strict=True)))
                for choices in product(((1, 0), (0, 1)), repeat=6)
            ]
            assert best_response_value_player_zero(policy, player) == pytest.approx(
                (max if player == 0 else min)(values)
            )


@pytest.mark.parametrize("alpha", [0, 1 / 6, 1 / 3])
def test_equilibrium_family(alpha):
    policy = {}
    bets = {
        "": [alpha, 0, 3 * alpha],
        "pb": [0, alpha + 1 / 3, 1],
        "p": [1 / 3, 0, 1],
        "b": [0, 1 / 3, 1],
    }
    for player, card, history in KEYS:
        p = bets[history][card]
        policy[player, card, history] = (1 - p, p)
    assert expected_value(policy) == pytest.approx(-1 / 18)
    assert exploitability(policy).exploitability == pytest.approx(0, abs=1e-14)


def test_all_utilities_and_information_sets():
    groups = {}
    for cards in permutations(range(3), 2):
        for h in ("", "p", "b", "pb"):
            player = acting_player(h)
            groups.setdefault((player, cards[player], h), set()).add(cards[1 - player])
        for path in PATHS:
            contributions = (
                [1, 1]
                if path == "pp"
                else [2, 1]
                if path == "bp"
                else ([1, 2] if path == "pbp" else [2, 2])
            )
            winner = (
                0 if path == "bp" else 1 if path == "pbp" else int(cards[1] > cards[0])
            )
            utilities = [-x for x in contributions]
            utilities[winner] += sum(contributions)
            assert sum(utilities) == 0
            assert terminal_utility_player_zero(cards, path) == utilities[0]
    assert len(groups) == 12
    assert all(len(hidden) == 2 for hidden in groups.values())


def test_checkpoint_resume():
    from pokeringdumdum.study import restore, snapshot

    trainer = CFRTrainer()
    trainer.train(23)
    resumed = restore(snapshot(trainer))
    assert resumed.train(31) == trainer.train(31)
    assert snapshot(resumed) == snapshot(trainer)
