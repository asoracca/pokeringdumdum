"""Exact policy evaluation and exploitability for Kuhn poker."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from pokeringdumdum.cfr import InfoSetKey, Policy
from pokeringdumdum.game import ACTIONS, CARDS, DEALS, acting_player, is_terminal
from pokeringdumdum.game import terminal_utility_player_zero as terminal_utility


@dataclass(frozen=True)
class ExploitabilityReport:
    profile_value_player_zero: float
    best_response_value_player_zero: float
    best_response_value_player_one: float
    nash_conv: float
    exploitability: float


def expected_value(policy: Policy) -> float:
    """Return exact expected utility for player zero across all six deals."""
    total = sum(_history_value(cards, "", policy) for cards in DEALS)
    return total / len(DEALS)


def _history_value(cards: tuple[int, int], history: str, policy: Policy) -> float:
    if is_terminal(history):
        return terminal_utility(cards, history)
    player = acting_player(history)
    key = (player, cards[player], history)
    strategy = policy.get(key, (0.5, 0.5))
    return sum(
        strategy[action_index] * _history_value(cards, history + action, policy)
        for action_index, action in enumerate(ACTIONS)
    )


def _information_sets(player: int) -> tuple[InfoSetKey, ...]:
    histories = ("", "pb") if player == 0 else ("p", "b")
    return tuple((player, card, history) for card in CARDS for history in histories)


def best_response_value_player_zero(policy: Policy, player: int) -> float:
    """Return player-zero utility when ``player`` plays an exact best response.

    Enumerating 2^6 deterministic policies is exact for Kuhn poker and, unlike a
    per-deal maximum, respects that a player cannot observe the opponent's card.
    """
    if player not in {0, 1}:
        raise ValueError("player must be zero or one")
    info_sets = _information_sets(player)
    values = []
    for choices in product(range(2), repeat=len(info_sets)):
        candidate = dict(policy)
        for key, action_index in zip(info_sets, choices, strict=True):
            candidate[key] = (1.0, 0.0) if action_index == 0 else (0.0, 1.0)
        values.append(expected_value(candidate))
    return max(values) if player == 0 else min(values)


def exploitability(policy: Policy) -> ExploitabilityReport:
    """Measure distance from equilibrium using exact best responses."""
    profile_value = expected_value(policy)
    best_zero = best_response_value_player_zero(policy, player=0)
    best_one_as_zero = best_response_value_player_zero(policy, player=1)
    best_one = -best_one_as_zero
    nash_conv = best_zero - best_one_as_zero
    return ExploitabilityReport(
        profile_value_player_zero=profile_value,
        best_response_value_player_zero=best_zero,
        best_response_value_player_one=best_one,
        nash_conv=nash_conv,
        exploitability=nash_conv / 2.0,
    )
