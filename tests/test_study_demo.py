import json
from pathlib import Path

import jsonschema
import pytest

from pokeringdumdum.cfr import CFRTrainer
from pokeringdumdum.demo import Hand
from pokeringdumdum.evaluation import expected_value
from pokeringdumdum.export import export
from pokeringdumdum.game import legal_actions
from pokeringdumdum.study import run, validate_config


def test_export_contract_and_fixture():
    schema = json.loads(Path("explorer/strategy.schema.json").read_text())
    trainer = CFRTrainer()
    trainer.train(5)
    jsonschema.validate(json.loads(json.dumps(export(trainer))), schema)
    fixture = json.loads(Path("explorer/strategy.json").read_text())
    jsonschema.validate(fixture, schema)
    keys = {(n["player"], n["card"], n["history"]) for n in fixture["information_sets"]}
    assert len(keys) == 12
    for h, state in fixture["states"].items():
        assert tuple(state.get("actions", [])) == legal_actions(h)
    fixture["information_sets"][0]["probabilities"][0] = -1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(fixture, schema)


def test_no_hidden_card_and_policy_key():
    class Spy(dict):
        def __getitem__(self, key):
            assert key[0] == 1 and key[1] == hand.cards[1]
            assert len(key) == 3
            return (1, 0)

    hand = Hand(Spy(), 7)
    assert "opponent_card" not in hand.view()
    assert hand.act("p")["terminal"]
    assert "opponent_card" in hand.view()
    with pytest.raises(ValueError):
        hand.act("b")
    with pytest.raises(ValueError):
        Hand({}, 1).act("invalid")


def test_seeded_hands():
    assert Hand({}, 9).cards == Hand({}, 9).cards


def test_runner(tmp_path):
    config = {
        "algorithms": ["cfr", "cfr_plus"],
        "iterations": [2, 4],
        "seconds": [0.001],
    }
    rows = run(config, tmp_path)
    assert len(rows) == 6
    assert [r["iterations"] for r in rows if r["experiment"] == "iterations"] == [
        2,
        4,
        2,
        4,
    ]
    assert all(
        r["training_seconds"] >= r["budget"]
        for r in rows
        if r["experiment"] == "seconds"
    )
    assert len(list(tmp_path.glob("*.json"))) == 7
    for bad in (0, -1, float("nan"), True):
        with pytest.raises(ValueError):
            validate_config(config | {"seconds": [bad]})


@pytest.mark.parametrize(
    "policy",
    [
        {(0, 0, ""): (-1, 2)},
        {(0, 0, ""): (0.2, 0.2)},
        {(0, 0, ""): (float("nan"), 1)},
        {(1, 0, ""): (0.5, 0.5)},
    ],
)
def test_invalid_policies(policy):
    with pytest.raises(ValueError):
        expected_value(policy)


def test_illegal_histories():
    with pytest.raises(ValueError):
        legal_actions("bbb")
    assert legal_actions("pp") == ()
