import unittest

from noxsum_lab.generator import generate_levels


class GeneratorTests(unittest.TestCase):
    def test_same_seed_is_reproducible(self) -> None:
        left = generate_levels(seed=20260925, count=8, normal=3)
        right = generate_levels(seed=20260925, count=8, normal=3)
        self.assertEqual(left, right)

    def test_different_seed_changes_selection(self) -> None:
        left = generate_levels(seed=20260925, count=8, normal=3)
        right = generate_levels(seed=20260926, count=8, normal=3)
        self.assertNotEqual(
            [item["solution"] for item in left],
            [item["solution"] for item in right],
        )

    def test_typed_profile_is_supported(self) -> None:
        levels = generate_levels(
            seed=7,
            count=2,
            normal=1,
            tall=1,
            plate=1,
            lights=("TOP", "LEFT", "RIGHT", "BOTTOM"),
        )
        self.assertEqual(len(levels), 2)
        for level in levels:
            self.assertEqual(level["inventory"], {"POST": 1, "TALL": 1, "PLATE": 1})
            self.assertEqual(level["metrics"]["exact_survivors"], 1)


if __name__ == "__main__":
    unittest.main()
