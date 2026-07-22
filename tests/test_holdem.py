import unittest

from pokeringdumdum.holdem import best_rank, category_name, rank_five, validate_cards


class HoldemTests(unittest.TestCase):
    def test_rejects_duplicate_and_invalid_cards(self):
        with self.assertRaises(ValueError):
            validate_cards(("As", "As"))
        with self.assertRaises(ValueError):
            validate_cards(("1s", "Kh"))

    def test_hand_categories_are_ordered(self):
        straight = rank_five(("As", "2d", "3c", "4h", "5s"))
        flush = rank_five(("As", "Js", "8s", "4s", "2s"))
        full_house = rank_five(("Kh", "Kd", "Ks", "2c", "2d"))
        self.assertLess(straight, flush)
        self.assertLess(flush, full_house)
        self.assertEqual(category_name(straight), "straight")
        self.assertEqual(straight[1], 5)

    def test_best_of_seven_uses_best_five(self):
        rank = best_rank(("As", "Ks", "Qs", "Js", "Ts", "2d", "3c"))
        self.assertEqual(category_name(rank), "straight flush")
        self.assertEqual(rank[1], 14)


if __name__ == "__main__":
    unittest.main()
