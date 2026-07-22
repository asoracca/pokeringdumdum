"""External-sampling Monte Carlo CFR for Kuhn poker."""

from __future__ import annotations

import random

from pokeringdumdum.cfr import InfoSet, InfoSetKey, Policy
from pokeringdumdum.game import ACTIONS, CARDS, DEALS, acting_player, is_terminal
from pokeringdumdum.game import terminal_utility_player_zero as terminal_utility

PLAYER_HISTORIES = {0: ("", "pb"), 1: ("p", "b")}


class ExternalSamplingMCCFR:
    """Train a Kuhn strategy with external-sampling MCCFR.

    Each iteration performs one sampled traversal for each player. At the
    traverser's information sets every action is evaluated; chance and opponent
    actions are sampled. The random generator is owned by the trainer so a seed
    makes the full learning trajectory reproducible.
    """

    def __init__(self, seed: int = 7) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.info_sets: dict[InfoSetKey, InfoSet] = {}
        self.iterations = 0
        self.terminal_visits = 0

    def train(self, iterations: int) -> Policy:
        if iterations < 1:
            raise ValueError("iterations must be positive")
        for _ in range(iterations):
            self.iterations += 1
            for traverser in (0, 1):
                cards = self.rng.choice(DEALS)
                self._traverse(
                    cards=cards,
                    history="",
                    traverser=traverser,
                    reach_zero=1.0,
                    reach_one=1.0,
                )
        return self.average_policy()

    def average_policy(self) -> Policy:
        policy: Policy = {}
        for player in (0, 1):
            for card in CARDS:
                for history in PLAYER_HISTORIES[player]:
                    key = (player, card, history)
                    node = self.info_sets.get(key)
                    policy[key] = (
                        node.average_strategy() if node is not None else (0.5, 0.5)
                    )
        return policy

    def _traverse(
        self,
        cards: tuple[int, int],
        history: str,
        traverser: int,
        reach_zero: float,
        reach_one: float,
    ) -> float:
        if is_terminal(history):
            self.terminal_visits += 1
            return terminal_utility(cards, history)

        player = acting_player(history)
        key = (player, cards[player], history)
        node = self.info_sets.setdefault(key, InfoSet())
        strategy = node.current_strategy()

        if player == traverser:
            action_utilities: list[float] = []
            for action_index, action in enumerate(ACTIONS):
                if player == 0:
                    utility = self._traverse(
                        cards,
                        history + action,
                        traverser,
                        reach_zero * strategy[action_index],
                        reach_one,
                    )
                else:
                    utility = self._traverse(
                        cards,
                        history + action,
                        traverser,
                        reach_zero,
                        reach_one * strategy[action_index],
                    )
                action_utilities.append(utility)

            node_utility = sum(
                probability * utility
                for probability, utility in zip(strategy, action_utilities, strict=True)
            )
            for action_index, action_utility in enumerate(action_utilities):
                regret = (
                    action_utility - node_utility
                    if player == 0
                    else node_utility - action_utility
                )
                node.regret_sum[action_index] += regret
            return node_utility

        own_reach = reach_zero if player == 0 else reach_one
        for action_index, probability in enumerate(strategy):
            node.strategy_sum[action_index] += own_reach * probability

        sampled_action = self._sample_action(strategy)
        action = ACTIONS[sampled_action]
        if player == 0:
            return self._traverse(
                cards,
                history + action,
                traverser,
                reach_zero * strategy[sampled_action],
                reach_one,
            )
        return self._traverse(
            cards,
            history + action,
            traverser,
            reach_zero,
            reach_one * strategy[sampled_action],
        )

    def _sample_action(self, strategy: tuple[float, float]) -> int:
        return 0 if self.rng.random() < strategy[0] else 1
