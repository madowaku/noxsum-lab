from __future__ import annotations

import math
from statistics import median
from typing import Any

from .rules import CELL_COUNT, Objects, code, shadow


def _value_bitsets(column: tuple[int, ...]) -> dict[int, int]:
    """Map each value in one cell column to a bitset of the worlds showing it.

    Bit ``i`` is world ``i``. Each bitset is parsed in one linear pass; OR-ing
    one bit at a time into a growing integer is quadratic in the world count.
    """

    values = set(column)
    if not values:
        return {}
    if min(values) < 0 or max(values) > 255:
        result: dict[int, int] = {}
        for world_index, value in enumerate(column):
            result[value] = result.get(value, 0) | (1 << world_index)
        return result

    # Reversed so that world 0 lands on the least significant bit.
    encoded = bytes(column)[::-1]
    result = {}
    for value in values:
        table = bytearray(b"0" * 256)
        table[value] = ord("1")
        result[value] = int(encoded.translate(bytes(table)), 2)
    return result


class ReasoningIndex:
    """Bitset index for clue-survivor analysis within one physical profile."""

    def __init__(self, worlds: list[Objects], targets: list[tuple[int, ...]]):
        if len(worlds) != len(targets):
            raise ValueError("world and target counts differ")
        # worlds / targets are deliberately not retained: only the bitsets are
        # needed afterwards, and the miner keeps one index per profile.
        self.world_count = len(worlds)
        self.all_bits = (1 << self.world_count) - 1
        self.buckets = [
            _value_bitsets(column)
            for column in (zip(*targets) if targets else [()] * CELL_COUNT)
        ]

    def clue_bits(self, cell_index: int, value: int) -> int:
        return self.buckets[cell_index].get(int(value), 0)

    def analyze(self, target: tuple[int, ...]) -> dict[str, Any]:
        bits = [
            self.clue_bits(index, target[index])
            for index in range(CELL_COUNT)
        ]
        single_counts = [item.bit_count() for item in bits]
        best_single = min(single_counts)
        median_single = float(median(single_counts))

        best_pair = self.world_count
        best_pair_cells: tuple[int, int] | None = None
        # Worlds matching every clue survive any pair, so no pair can go below
        # this floor; stop scanning once a pair reaches it.
        full_match = self.all_bits
        for item in bits:
            full_match &= item
        pair_floor = full_match.bit_count()

        for left in range(CELL_COUNT):
            if best_pair_cells is not None and best_pair <= pair_floor:
                break
            left_bits = bits[left]
            for right in range(left + 1, CELL_COUNT):
                count = (left_bits & bits[right]).bit_count()
                if count < best_pair:
                    best_pair = count
                    best_pair_cells = (left, right)

        remaining = self.all_bits
        unrevealed = set(range(CELL_COUNT))
        trace: list[dict[str, Any]] = []

        while remaining.bit_count() > 1 and unrevealed:
            before = remaining.bit_count()
            best_cell = None
            best_bits = None
            best_count = before

            for cell_index in unrevealed:
                candidate_bits = remaining & bits[cell_index]
                count = candidate_bits.bit_count()
                if count < best_count:
                    best_count = count
                    best_cell = cell_index
                    best_bits = candidate_bits

            if best_cell is None or best_bits is None:
                break

            gain = before / max(1, best_count)
            trace.append(
                {
                    "cell": code(best_cell),
                    "value": int(target[best_cell]),
                    "before": before,
                    "after": best_count,
                    "gain": round(gain, 4),
                }
            )
            remaining = best_bits
            unrevealed.remove(best_cell)

        witness_length = len(trace)
        penultimate = trace[-1]["before"] if trace else self.world_count
        first_after = trace[0]["after"] if trace else self.world_count
        max_gain = max((item["gain"] for item in trace), default=1.0)
        late_trace = trace[max(0, len(trace) // 2):]
        late_max_gain = max((item["gain"] for item in late_trace), default=1.0)

        pair_synergy = 0.0
        if best_single > 0 and best_pair > 0:
            pair_synergy = math.log2(best_single / best_pair)

        log_space = max(1.0, math.log2(max(2, self.world_count)))
        witness_density = witness_length / CELL_COUNT
        opening_strength = 1.0 - math.log2(max(1, best_single)) / log_space
        pair_strength = 1.0 - math.log2(max(1, best_pair)) / log_space

        return {
            "best_single_survivors": best_single,
            "median_single_survivors": round(median_single, 3),
            "best_pair_survivors": best_pair,
            "best_pair_cells": (
                [code(best_pair_cells[0]), code(best_pair_cells[1])]
                if best_pair_cells
                else []
            ),
            "witness_length": witness_length,
            "witness_trace": trace,
            "first_greedy_survivors": first_after,
            "penultimate_survivors": penultimate,
            "max_information_gain": round(max_gain, 4),
            "late_max_information_gain": round(late_max_gain, 4),
            "pair_synergy_bits": round(pair_synergy, 4),
            "opening_strength": round(max(0.0, min(1.0, opening_strength)), 4),
            "pair_strength": round(max(0.0, min(1.0, pair_strength)), 4),
            "witness_density": round(witness_density, 4),
        }


def texture_metrics(
    objects: Objects,
    target: tuple[int, ...],
    lights: tuple[str, ...],
) -> dict[str, Any]:
    nonzero = sum(value > 0 for value in target)
    zero = CELL_COUNT - nonzero
    overlap = sum(value > 1 for value in target)
    maximum = max(target, default=0)
    total_ink = sum(target)

    occupied = [index for index, _ in objects]
    if occupied:
        xs = [index % 5 for index in occupied]
        ys = [index // 5 for index in occupied]
        span = (max(xs) - min(xs)) + (max(ys) - min(ys))
        center_distance = sum(
            abs(index % 5 - 2) + abs(index // 5 - 2)
            for index in occupied
        ) / len(occupied)
    else:
        span = 0
        center_distance = 0.0

    counts: dict[int, int] = {}
    for value in target:
        counts[value] = counts.get(value, 0) + 1
    entropy = 0.0
    for count in counts.values():
        probability = count / CELL_COUNT
        entropy -= probability * math.log2(probability)

    return {
        "visible_nonzero_cells": nonzero,
        "zero_cells": zero,
        "overlap_cells": overlap,
        "max_shadow_value": maximum,
        "total_shadow_ink": total_ink,
        "target_entropy": round(entropy, 4),
        "solution_span": span,
        "solution_center_distance": round(center_distance, 4),
        "light_count": len(lights),
    }
