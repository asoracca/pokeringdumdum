"""Vanilla CFR and regret-matching-plus for Kuhn poker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pokeringdumdum.game import ACTIONS, DEALS, acting_player, is_terminal
from pokeringdumdum.game import terminal_utility_player_zero as terminal_utility

InfoSetKey = tuple[int, int, str]
Policy = dict[InfoSetKey, tuple[float, float]]


@dataclass
class InfoSet:
    regret_sum: list[float] = field(default_factory=lambda: [0.0, 0.0])
    strategy_sum: list[float] = field(default_factory=lambda: [0.0, 0.0])

    def current_strategy(self) -> tuple[float, float]:
        positive = [max(regret, 0.0) for regret in self.regret_sum]
        normalizer = sum(positive)
        if normalizer == 0.0:
            return (0.5, 0.5)
        return (positive[0] / normalizer, positive[1] / normalizer)

    def average_strategy(self) -> tuple[float, float]:
        normalizer = sum(self.strategy_sum)
        if normalizer == 0.0:
            return (0.5, 0.5)
        return (
            self.strategy_sum[0] / normalizer,
            self.strategy_sum[1] / normalizer,
        )


class CFRTrainer:
    """Train an average strategy using full-tree counterfactual regret."""

    def __init__(
        self,
        algorithm: Literal["cfr", "cfr_plus"] = "cfr_plus",
        averaging_delay: int = 0,
    ) -> None:
        if algorithm not in {"cfr", "cfr_plus"}:
            raise ValueError("algorithm must be 'cfr' or 'cfr_plus'")
        if averaging_delay < 0:
            raise ValueError("averaging_delay cannot be negative")
        self.algorithm = algorithm
        self.averaging_delay = averaging_delay
        self.info_sets: dict[InfoSetKey, InfoSet] = {}
        self.iterations = 0
        self.terminal_visits = 0

    def train(self, iterations: int) -> Policy:
        if iterations < 1:
            raise ValueError("iterations must be positive")

        for _ in range(iterations):
            self.iterations += 1
            regret_deltas: dict[InfoSetKey, list[float]] = {}
            average_weight = (
                float(max(self.iterations - self.averaging_delay, 0))
                if self.algorithm == "cfr_plus"
                else 1.0
            )
            for cards in DEALS:
                self._traverse(
                    cards=cards,
                    history="",
                    reach_zero=1.0,
                    reach_one=1.0,
                    chance_reach=1.0 / len(DEALS),
                    average_weight=average_weight,
                    regret_deltas=regret_deltas,
                )
            self._apply_regrets(regret_deltas)
        return self.average_policy()

    def average_policy(self) -> Policy:
        return {key: node.average_strategy() for key, node in self.info_sets.items()}

    def _apply_regrets(self, regret_deltas: dict[InfoSetKey, list[float]]) -> None:
        for key, deltas in regret_deltas.items():
            node = self.info_sets[key]
            for action_index, delta in enumerate(deltas):
                updated = node.regret_sum[action_index] + delta
                node.regret_sum[action_index] = (
                    max(updated, 0.0) if self.algorithm == "cfr_plus" else updated
                )

    def _traverse(
        self,
        cards: tuple[int, int],
        history: str,
        reach_zero: float,
        reach_one: float,
        chance_reach: float,
        average_weight: float,
        regret_deltas: dict[InfoSetKey, list[float]],
    ) -> float:
        if is_terminal(history):
            self.terminal_visits += 1
            return terminal_utility(cards, history)

        player = acting_player(history)
        key = (player, cards[player], history)
        node = self.info_sets.setdefault(key, InfoSet())
        strategy = node.current_strategy()
        own_reach = reach_zero if player == 0 else reach_one
        for action_index in range(2):
            node.strategy_sum[action_index] += (
                chance_reach * own_reach * average_weight * strategy[action_index]
            )

        action_utilities = []
        for action_index, action in enumerate(ACTIONS):
            next_history = history + action
            if player == 0:
                utility = self._traverse(
                    cards,
                    next_history,
                    reach_zero * strategy[action_index],
                    reach_one,
                    chance_reach,
                    average_weight,
                    regret_deltas,
                )
            else:
                utility = self._traverse(
                    cards,
                    next_history,
                    reach_zero,
                    reach_one * strategy[action_index],
                    chance_reach,
                    average_weight,
                    regret_deltas,
                )
            action_utilities.append(utility)

        node_utility = sum(
            probability * utility
            for probability, utility in zip(strategy, action_utilities, strict=True)
        )
        opponent_reach = reach_one if player == 0 else reach_zero
        deltas = regret_deltas.setdefault(key, [0.0, 0.0])
        for action_index, action_utility in enumerate(action_utilities):
            player_regret = (
                action_utility - node_utility
                if player == 0
                else node_utility - action_utility
            )
            deltas[action_index] += chance_reach * opponent_reach * player_regret
        return node_utility
