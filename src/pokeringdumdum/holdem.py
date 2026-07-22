"""Small, auditable Texas Hold'em card and showdown evaluator."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_VALUE = {rank: value for value, rank in enumerate(RANKS, start=2)}
DECK = tuple(f"{rank}{suit}" for rank in RANKS for suit in SUITS)
CATEGORY_NAMES = (
    "high card",
    "pair",
    "two pair",
    "three of a kind",
    "straight",
    "flush",
    "full house",
    "four of a kind",
    "straight flush",
)


def validate_cards(
    cards: Iterable[str], expected: int | None = None
) -> tuple[str, ...]:
    """Normalize and validate two-character cards such as ``As`` and ``Td``."""
    normalized = tuple(card.strip() for card in cards)
    if expected is not None and len(normalized) != expected:
        raise ValueError(f"expected {expected} cards, received {len(normalized)}")
    for card in normalized:
        if (
            len(card) != 2
            or card[0].upper() not in RANKS
            or card[1].lower() not in SUITS
        ):
            raise ValueError(f"invalid card: {card!r}")
    normalized = tuple(card[0].upper() + card[1].lower() for card in normalized)
    if len(set(normalized)) != len(normalized):
        raise ValueError("cards must be unique")
    return normalized


def _straight_high(values: Iterable[int]) -> int | None:
    unique = set(values)
    if 14 in unique:
        unique.add(1)
    ordered = sorted(unique)
    for high_index in range(len(ordered) - 1, 3, -1):
        window = ordered[high_index - 4 : high_index + 1]
        if window[-1] - window[0] == 4:
            return window[-1]
    return None


def rank_five(cards: Iterable[str]) -> tuple[int, ...]:
    """Return a lexicographically comparable rank for exactly five cards."""
    hand = validate_cards(cards, expected=5)
    return _rank_five_unchecked(hand)


def _rank_five_unchecked(hand: tuple[str, ...]) -> tuple[int, ...]:
    values = [RANK_VALUE[card[0]] for card in hand]
    counts = Counter(values)
    groups = sorted(((count, value) for value, count in counts.items()), reverse=True)
    flush = len({card[1] for card in hand}) == 1
    straight_high = _straight_high(values)

    if flush and straight_high is not None:
        return (8, straight_high)
    if groups[0][0] == 4:
        quad = groups[0][1]
        kicker = max(value for value in values if value != quad)
        return (7, quad, kicker)
    if sorted(counts.values()) == [2, 3]:
        triple = max(value for value, count in counts.items() if count == 3)
        pair = max(value for value, count in counts.items() if count == 2)
        return (6, triple, pair)
    if flush:
        return (5, *sorted(values, reverse=True))
    if straight_high is not None:
        return (4, straight_high)
    if groups[0][0] == 3:
        triple = groups[0][1]
        kickers = sorted((value for value in values if value != triple), reverse=True)
        return (3, triple, *kickers)
    pairs = sorted(
        (value for value, count in counts.items() if count == 2), reverse=True
    )
    if len(pairs) == 2:
        kicker = max(value for value in values if value not in pairs)
        return (2, pairs[0], pairs[1], kicker)
    if len(pairs) == 1:
        pair = pairs[0]
        kickers = sorted((value for value in values if value != pair), reverse=True)
        return (1, pair, *kickers)
    return (0, *sorted(values, reverse=True))


def best_rank(cards: Iterable[str]) -> tuple[int, ...]:
    """Return the best five-card rank available from five to seven cards."""
    available = validate_cards(cards)
    if not 5 <= len(available) <= 7:
        raise ValueError("best_rank requires five to seven cards")
    return max(_rank_five_unchecked(combo) for combo in combinations(available, 5))


def category_name(rank: tuple[int, ...]) -> str:
    return CATEGORY_NAMES[rank[0]]
