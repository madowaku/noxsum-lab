import unittest

from noxsum_lab.analysis import ReasoningIndex
from noxsum_lab.miner import _prepare_profile
from noxsum_lab.rules import CELL_COUNT, code


class ReasoningIndexTests(unittest.TestCase):
    def test_bitsets_match_per_world_definition(self) -> None:
        worlds, targets, _ = _prepare_profile((2, 0, 1), ("TOP", "LEFT"))
        index = ReasoningIndex(worlds, targets)

        expected: list[dict[int, int]] = [dict() for _ in range(CELL_COUNT)]
        for world_index, values in enumerate(targets):
            for cell_index, value in enumerate(values):
                by_value = expected[cell_index]
                by_value[value] = by_value.get(value, 0) | (1 << world_index)

        self.assertEqual(index.world_count, len(worlds))
        self.assertEqual(index.buckets, expected)

    def test_best_pair_is_the_first_minimal_pair(self) -> None:
        worlds, targets, unique_indices = _prepare_profile((3, 0, 0), ("TOP", "LEFT"))
        index = ReasoningIndex(worlds, targets)

        for world_index in unique_indices[:50]:
            target = targets[world_index]
            bits = [index.clue_bits(cell, target[cell]) for cell in range(CELL_COUNT)]
            pairs = [
                ((bits[left] & bits[right]).bit_count(), left, right)
                for left in range(CELL_COUNT)
                for right in range(left + 1, CELL_COUNT)
            ]
            best = min(count for count, _, _ in pairs)
            first = next(
                (left, right) for count, left, right in pairs if count == best
            )

            result = index.analyze(target)
            self.assertEqual(result["best_pair_survivors"], best)
            self.assertEqual(
                result["best_pair_cells"], [code(first[0]), code(first[1])]
            )


if __name__ == "__main__":
    unittest.main()
