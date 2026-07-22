import unittest

from pokeringdumdum.preflop import (
    all_starting_hand_labels,
    break_even_fold_probability,
    call_decision,
    open_range,
    pot_odds,
    raise_expected_value,
    simulate_preflop_equity,
    starting_hand_label,
)


class PreflopTests(unittest.TestCase):
    def test_starting_hand_labels(self):
        self.assertEqual(starting_hand_label("As", "Ks"), "AKs")
        self.assertEqual(starting_hand_label("Kh", "Ac"), "AKo")
        self.assertEqual(starting_hand_label("Qh", "Qc"), "QQ")
        self.assertEqual(len(set(all_starting_hand_labels())), 169)

    def test_range_styles_are_nested(self):
        tight = open_range("CO", "tight")
        balanced = open_range("CO", "balanced")
        loose = open_range("CO", "loose")
        self.assertLess(len(tight), len(balanced))
        self.assertLess(len(balanced), len(loose))
        self.assertTrue(tight <= balanced <= loose)

    def test_simulation_is_seeded_and_aces_are_strong(self):
        first = simulate_preflop_equity(("As", "Ah"), trials=1_000, seed=4)
        second = simulate_preflop_equity(("As", "Ah"), trials=1_000, seed=4)
        self.assertEqual(first, second)
        self.assertGreater(first.equity, 0.75)
        self.assertLessEqual(first.ci95_low, first.equity)
        self.assertGreaterEqual(first.ci95_high, first.equity)

    def test_call_math(self):
        self.assertAlmostEqual(pot_odds(100, 25), 0.2)
        self.assertEqual(call_decision(0.24, 100, 25, 0.03)[0], "CALL")
        self.assertEqual(call_decision(0.22, 100, 25, 0.03)[0], "FOLD")
        self.assertEqual(call_decision(0.10, 100, 0)[0], "CHECK")

    def test_raise_math(self):
        self.assertAlmostEqual(raise_expected_value(100, 50, 0.0, 0.5), 25.0)
        self.assertAlmostEqual(break_even_fold_probability(100, 50, 0.0), 1 / 3)


if __name__ == "__main__":
    unittest.main()
