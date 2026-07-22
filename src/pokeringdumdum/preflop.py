"""Beginner preflop charts, equity simulation, and decision mathematics."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from itertools import combinations

from pokeringdumdum.holdem import DECK, RANK_VALUE, best_rank, validate_cards

DISPLAY_RANKS = "AKQJT98765432"
POSITIONS = ("UTG", "HJ", "CO", "BTN", "SB", "BB")


def starting_hand_label(first: str, second: str) -> str:
    """Convert two cards to canonical notation such as AA, AKs, or AKo."""
    card_a, card_b = validate_cards((first, second), expected=2)
    rank_a, rank_b = card_a[0], card_b[0]
    if rank_a == rank_b:
        return rank_a * 2
    high, low = sorted(
        (rank_a, rank_b), key=lambda rank: RANK_VALUE[rank], reverse=True
    )
    suited = card_a[1] == card_b[1]
    return f"{high}{low}{'s' if suited else 'o'}"


def all_starting_hand_labels() -> tuple[str, ...]:
    labels: list[str] = []
    for row, first in enumerate(DISPLAY_RANKS):
        for column, second in enumerate(DISPLAY_RANKS):
            if row == column:
                labels.append(first * 2)
            elif row < column:
                labels.append(f"{first}{second}s")
            else:
                labels.append(f"{second}{first}o")
    return tuple(labels)


def _expand(specification: str) -> frozenset[str]:
    return frozenset(specification.split())


_BALANCED_OPEN = {
    "UTG": _expand(
        "AA KK QQ JJ TT 99 88 77 AKs AQs AJs ATs KQs KJs QJs JTs T9s 98s AKo AQo"
    ),
    "HJ": _expand(
        "AA KK QQ JJ TT 99 88 77 66 AKs AQs AJs ATs A9s KQs KJs KTs "
        "QJs QTs JTs T9s 98s 87s AKo AQo AJo KQo"
    ),
    "CO": _expand(
        "AA KK QQ JJ TT 99 88 77 66 55 44 33 22 AKs AQs AJs ATs A9s "
        "A8s A7s A6s A5s A4s A3s A2s KQs KJs KTs K9s QJs QTs Q9s JTs "
        "J9s T9s T8s 98s 97s 87s 76s 65s 54s AKo AQo AJo ATo KQo KJo QJo"
    ),
    "BTN": _expand(
        "AA KK QQ JJ TT 99 88 77 66 55 44 33 22 AKs AQs AJs ATs A9s "
        "A8s A7s A6s A5s A4s A3s A2s KQs KJs KTs K9s K8s K7s K6s K5s "
        "K4s K3s K2s QJs QTs Q9s Q8s Q7s JTs J9s J8s T9s T8s T7s 98s "
        "97s 96s 87s 86s 76s 75s 65s 64s 54s 53s 43s AKo AQo AJo ATo "
        "A9o KQo KJo KTo QJo QTo JTo T9o 98o 87o"
    ),
    "SB": _expand(
        "AA KK QQ JJ TT 99 88 77 66 55 44 33 22 AKs AQs AJs ATs A9s "
        "A8s A7s A6s A5s A4s A3s A2s KQs KJs KTs K9s K8s K7s K6s QJs "
        "QTs Q9s Q8s JTs J9s J8s T9s T8s 98s 97s 87s 76s 65s 54s AKo "
        "AQo AJo ATo A9o KQo KJo KTo QJo QTo JTo"
    ),
    "BB": frozenset(),
}


def open_range(position: str, style: str = "balanced") -> frozenset[str]:
    """Return an educational six-max first-in opening range.

    These ranges are simplified defaults, not solver outputs. The BB has no
    first-in open range because it already closes the action when all others fold.
    """
    position = position.upper()
    style = style.lower()
    if position not in POSITIONS:
        raise ValueError(f"position must be one of {POSITIONS}")
    if style not in {"tight", "balanced", "loose"}:
        raise ValueError("style must be tight, balanced, or loose")
    base = set(_BALANCED_OPEN[position])
    ordered = list(all_starting_hand_labels())
    strength_order = sorted(ordered, key=_simple_preflop_score, reverse=True)
    if style == "tight":
        keep = max(0, round(len(base) * 0.72))
        return frozenset(
            label for label in strength_order if label in base
        ) & frozenset(strength_order[:keep])
    if style == "loose":
        target = min(169, round(len(base) * 1.28))
        base.update(strength_order[:target])
    return frozenset(base)


def _simple_preflop_score(label: str) -> float:
    high = RANK_VALUE[label[0]]
    low = RANK_VALUE[label[1]]
    if len(label) == 2:
        return 45 + 3 * high
    score = 2.2 * high + low
    if label.endswith("s"):
        score += 3
    gap = high - low
    score -= max(0, gap - 1) * 1.5
    return score


def chart_matrix(position: str, style: str = "balanced") -> list[list[str]]:
    selected = open_range(position, style)
    labels = all_starting_hand_labels()
    return [
        [
            f"{label} {'OPEN' if label in selected else 'FOLD'}"
            for label in labels[i : i + 13]
        ]
        for i in range(0, 169, 13)
    ]


@dataclass(frozen=True)
class EquityResult:
    equity: float
    win_rate: float
    tie_rate: float
    ci95_low: float
    ci95_high: float
    trials: int
    opponents: int


def simulate_preflop_equity(
    hero_cards: tuple[str, str],
    trials: int = 10_000,
    opponents: int = 1,
    opponent_labels: frozenset[str] | None = None,
    seed: int = 7,
) -> EquityResult:
    """Estimate showdown equity against sampled opponent ranges.

    Equity credits a tied pot fractionally. The interval is a normal
    approximation for the mean per-trial pot share.
    """
    hero = validate_cards(hero_cards, expected=2)
    if trials < 100:
        raise ValueError("trials must be at least 100")
    if not 1 <= opponents <= 5:
        raise ValueError("opponents must be between one and five")
    rng = random.Random(seed)
    shares: list[float] = []
    wins = 0
    ties = 0
    range_combinations = (
        tuple(
            combo
            for combo in combinations(DECK, 2)
            if starting_hand_label(combo[0], combo[1]) in opponent_labels
        )
        if opponent_labels is not None
        else ()
    )

    for _ in range(trials):
        available = [card for card in DECK if card not in hero]
        villain_hands: list[tuple[str, str]] = []
        for _opponent in range(opponents):
            if opponent_labels is None:
                sampled = rng.sample(available, 2)
                hand = (sampled[0], sampled[1])
            else:
                available_set = set(available)
                candidates = [
                    combo
                    for combo in range_combinations
                    if combo[0] in available_set and combo[1] in available_set
                ]
                if not candidates:
                    raise ValueError(
                        "opponent range has no available card combinations"
                    )
                hand = rng.choice(candidates)
            villain_hands.append(hand)
            available.remove(hand[0])
            available.remove(hand[1])

        board = tuple(rng.sample(available, 5))
        hero_rank = best_rank((*hero, *board))
        villain_ranks = [best_rank((*hand, *board)) for hand in villain_hands]
        best = max([hero_rank, *villain_ranks])
        winners = int(hero_rank == best) + sum(rank == best for rank in villain_ranks)
        share = 1.0 / winners if hero_rank == best else 0.0
        shares.append(share)
        wins += int(share == 1.0)
        ties += int(0.0 < share < 1.0)

    mean = sum(shares) / trials
    variance = sum((share - mean) ** 2 for share in shares) / (trials - 1)
    margin = 1.96 * math.sqrt(variance / trials)
    return EquityResult(
        equity=mean,
        win_rate=wins / trials,
        tie_rate=ties / trials,
        ci95_low=max(0.0, mean - margin),
        ci95_high=min(1.0, mean + margin),
        trials=trials,
        opponents=opponents,
    )


def pot_odds(pot_before_call: float, call_amount: float) -> float:
    if pot_before_call < 0 or call_amount < 0:
        raise ValueError("pot and call amount cannot be negative")
    if call_amount == 0:
        return 0.0
    return call_amount / (pot_before_call + call_amount)


def call_decision(
    equity: float,
    pot_before_call: float,
    call_amount: float,
    tolerance: float = 0.0,
) -> tuple[str, float]:
    """Return a simple equity-vs-pot-odds decision and required equity.

    ``tolerance`` is an extra safety margin, such as 0.03 for three percentage
    points. It can represent uncertainty or a beginner's preference for avoiding
    marginal calls; it is not a universal poker constant.
    """
    if not 0 <= equity <= 1 or not 0 <= tolerance <= 0.25:
        raise ValueError("equity and tolerance are outside their valid ranges")
    if call_amount == 0:
        return "CHECK", 0.0
    required = min(1.0, pot_odds(pot_before_call, call_amount) + tolerance)
    return ("CALL" if equity >= required else "FOLD"), required


def raise_expected_value(
    pot: float,
    risk: float,
    equity_when_called: float,
    opponent_fold_probability: float,
) -> float:
    """Return stylized raise EV when one opponent either folds or calls.

    ``risk`` is the additional amount hero invests. If called, the opponent adds
    the same amount. This omits reraises and future-street decisions.
    """
    if pot < 0 or risk <= 0:
        raise ValueError("pot must be nonnegative and risk must be positive")
    if not 0 <= equity_when_called <= 1 or not 0 <= opponent_fold_probability <= 1:
        raise ValueError("probabilities must be between zero and one")
    called_ev = equity_when_called * (pot + 2 * risk) - risk
    fold = opponent_fold_probability
    return fold * pot + (1 - fold) * called_ev


def break_even_fold_probability(
    pot: float, risk: float, equity_when_called: float
) -> float:
    called_ev = raise_expected_value(pot, risk, equity_when_called, 0.0)
    denominator = pot - called_ev
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, -called_ev / denominator))
