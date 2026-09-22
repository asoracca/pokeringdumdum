"""Versioned explorer data, generated only from the Python game and trainer."""

import json
from dataclasses import asdict
from pathlib import Path

from pokeringdumdum.cfr import CFRTrainer
from pokeringdumdum.evaluation import exploitability
from pokeringdumdum.game import (
    ACTIONS,
    CARD_NAMES,
    DEALS,
    acting_player,
    is_terminal,
    legal_actions,
    terminal_utility_player_zero,
)


def export(trainer):
    states = {}

    def visit(history):
        if is_terminal(history):
            states[history] = {
                "terminal": True,
                "payoffs": {
                    f"{a},{b}": terminal_utility_player_zero((a, b), history)
                    for a, b in DEALS
                },
            }
            return
        states[history] = {
            "terminal": False,
            "player": acting_player(history),
            "actions": list(legal_actions(history)),
            "labels": ["Fold", "Call"] if history.endswith("b") else ["Check", "Bet"],
        }
        for action in ACTIONS:
            visit(history + action)

    visit("")
    policy = trainer.average_policy()
    aggressive = {key: (0.0, 1.0) for key in policy}
    return {
        "version": 1,
        "game": "kuhn",
        "input_kind": "synthetic",
        "algorithm": trainer.algorithm,
        "iterations": trainer.iterations,
        "cards": CARD_NAMES,
        "deals": DEALS,
        "states": states,
        "report": asdict(exploitability(policy)),
        "always_bet_call_report": asdict(exploitability(aggressive)),
        "information_sets": [
            {
                "player": p,
                "card": c,
                "history": h,
                "probabilities": policy[p, c, h],
                "regrets": node.regret_sum,
            }
            for (p, c, h), node in sorted(trainer.info_sets.items())
        ],
    }


def main():
    trainer = CFRTrainer("cfr_plus")
    trainer.train(10000)
    Path("explorer/strategy.json").write_text(json.dumps(export(trainer), indent=2))


if __name__ == "__main__":
    main()
