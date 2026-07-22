import unittest

from pokeringdumdum.evaluation import exploitability
from pokeringdumdum.mccfr import ExternalSamplingMCCFR
from pokeringdumdum.mccfr_study import run_external_sampling_study


class ExternalSamplingTests(unittest.TestCase):
    def test_training_is_reproducible(self):
        first = ExternalSamplingMCCFR(seed=11)
        second = ExternalSamplingMCCFR(seed=11)
        self.assertEqual(first.train(500), second.train(500))
        self.assertEqual(first.terminal_visits, second.terminal_visits)

    def test_policy_is_complete_and_normalized(self):
        policy = ExternalSamplingMCCFR(seed=2).train(500)
        self.assertEqual(len(policy), 12)
        for strategy in policy.values():
            self.assertAlmostEqual(sum(strategy), 1.0)
            self.assertTrue(all(0.0 <= probability <= 1.0 for probability in strategy))

    def test_exploitability_improves_over_uniform_policy(self):
        uniform = exploitability({}).exploitability
        learned = exploitability(
            ExternalSamplingMCCFR(seed=4).train(10_000)
        ).exploitability
        self.assertLess(learned, uniform * 0.5)

    def test_study_aggregates_every_seed_and_checkpoint(self):
        rows, summary = run_external_sampling_study(
            checkpoints=(20, 50), seeds=(1, 2, 3)
        )
        self.assertEqual(len(rows), 6)
        self.assertEqual(len(summary), 2)
        self.assertTrue(all(row["runs"] == 3 for row in summary))

    def test_study_rejects_invalid_design(self):
        with self.assertRaises(ValueError):
            run_external_sampling_study((100, 50), (1, 2))
        with self.assertRaises(ValueError):
            run_external_sampling_study((50, 100), (1, 1))


if __name__ == "__main__":
    unittest.main()
