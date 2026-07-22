import unittest

from pokeringdumdum.cfr import CFRTrainer
from pokeringdumdum.evaluation import expected_value, exploitability


class SolverTests(unittest.TestCase):
    def test_average_policy_is_normalized(self):
        trainer = CFRTrainer("cfr")
        policy = trainer.train(100)
        self.assertEqual(len(policy), 12)
        self.assertGreater(trainer.terminal_visits, 0)
        for probabilities in policy.values():
            self.assertAlmostEqual(sum(probabilities), 1.0)
            self.assertTrue(all(0.0 <= value <= 1.0 for value in probabilities))

    def test_uniform_policy_has_positive_exploitability(self):
        self.assertGreater(exploitability({}).exploitability, 0.1)

    def test_cfr_plus_converges_near_kuhn_value(self):
        policy = CFRTrainer("cfr_plus").train(25_000)
        report = exploitability(policy)
        self.assertAlmostEqual(expected_value(policy), -1.0 / 18.0, delta=0.01)
        self.assertLess(report.exploitability, 0.01)

    def test_invalid_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            CFRTrainer("not_cfr")
        with self.assertRaises(ValueError):
            CFRTrainer().train(0)


if __name__ == "__main__":
    unittest.main()
