"""Rules for two-player Kuhn poker.

Cards are J=0, Q=1, K=2. Actions use ``p`` for pass (check or fold) and ``b``
for bet (bet or call). Utilities are net chips for player zero after both players
ante one chip.
"""

from __future__ import annotations

from itertools import permutations

CARDS = (0, 1, 2)
CARD_NAMES = {0: "J", 1: "Q", 2: "K"}
ACTIONS = ("p", "b")
DEALS = tuple(permutations(CARDS, 2))
TERMINAL_HISTORIES = {"pp", "bp", "bb", "pbp", "pbb"}


def is_terminal(history: str) -> bool:
    return history in TERMINAL_HISTORIES


def acting_player(history: str) -> int:
    if is_terminal(history):
        raise ValueError("terminal histories have no acting player")
    if history not in {"", "p", "b", "pb"}:
        raise ValueError(f"invalid history: {history!r}")
    return len(history) % 2


def terminal_utility_player_zero(cards: tuple[int, int], history: str) -> float:
    """Return player zero's net payoff for a terminal history."""
    if history not in TERMINAL_HISTORIES:
        raise ValueError(f"history is not terminal: {history!r}")
    if cards[0] == cards[1] or any(card not in CARDS for card in cards):
        raise ValueError(f"invalid private cards: {cards!r}")

    if history == "bp":
        return 1.0
    if history == "pbp":
        return -1.0

    stake = 1.0 if history == "pp" else 2.0
    return stake if cards[0] > cards[1] else -stake
