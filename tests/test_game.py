import unittest

from pokeringdumdum.game import acting_player, terminal_utility_player_zero


class GameTests(unittest.TestCase):
    def test_showdown_utilities(self):
        self.assertEqual(terminal_utility_player_zero((2, 0), "pp"), 1.0)
        self.assertEqual(terminal_utility_player_zero((0, 2), "bb"), -2.0)
        self.assertEqual(terminal_utility_player_zero((2, 1), "pbb"), 2.0)

    def test_fold_utilities(self):
        self.assertEqual(terminal_utility_player_zero((0, 2), "bp"), 1.0)
        self.assertEqual(terminal_utility_player_zero((2, 0), "pbp"), -1.0)

    def test_acting_player(self):
        self.assertEqual(acting_player(""), 0)
        self.assertEqual(acting_player("p"), 1)
        self.assertEqual(acting_player("b"), 1)
        self.assertEqual(acting_player("pb"), 0)


if __name__ == "__main__":
    unittest.main()
