import unittest

from noxsum_lab.miner import mine_candidates


class MinerTests(unittest.TestCase):
    def test_small_mine_is_reproducible_and_ranked(self) -> None:
        kwargs = {
            "seed": 20260925,
            "count": 16,
            "inventories": [(3, 0, 0)],
            "light_sets": [("TOP", "LEFT", "RIGHT")],
        }
        left = mine_candidates(**kwargs)
        right = mine_candidates(**kwargs)

        self.assertEqual(left, right)
        self.assertEqual(left["raw_candidates"], 16)
        self.assertLessEqual(left["after_symmetry_dedupe"], 16)
        self.assertGreater(left["after_symmetry_dedupe"], 0)

        levels = left["levels"]
        flow_ranks = sorted(level["metrics"]["flow_rank"] for level in levels)
        aha_ranks = sorted(level["metrics"]["aha_rank"] for level in levels)
        expected = list(range(1, len(levels) + 1))
        self.assertEqual(flow_ranks, expected)
        self.assertEqual(aha_ranks, expected)

        for level in levels:
            self.assertIn("flow_score", level["metrics"])
            self.assertIn("aha_score", level["metrics"])
            self.assertIn("witness_trace", level["annotations"])
            self.assertEqual(level["metrics"]["exact_survivors"], 1)


if __name__ == "__main__":
    unittest.main()
