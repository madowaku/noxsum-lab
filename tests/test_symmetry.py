import unittest

from noxsum_lab.symmetry import (
    canonical_puzzle_signature,
    transform_lights,
    transform_values,
)


class SymmetryTests(unittest.TestCase):
    def test_rotated_puzzle_has_same_signature(self) -> None:
        target = tuple((index * 3) % 4 for index in range(25))
        lights = ("TOP", "LEFT")
        inventory = (2, 1, 0)

        original = canonical_puzzle_signature(
            target=target,
            lights=lights,
            inventory=inventory,
        )
        rotated = canonical_puzzle_signature(
            target=transform_values(target, "rot90"),
            lights=transform_lights(lights, "rot90"),
            inventory=inventory,
        )
        self.assertEqual(original, rotated)

    def test_different_inventory_is_not_duplicate(self) -> None:
        target = tuple(index % 3 for index in range(25))
        left = canonical_puzzle_signature(
            target=target,
            lights=("TOP", "LEFT"),
            inventory=(3, 0, 0),
        )
        right = canonical_puzzle_signature(
            target=target,
            lights=("TOP", "LEFT"),
            inventory=(2, 1, 0),
        )
        self.assertNotEqual(left, right)


if __name__ == "__main__":
    unittest.main()
