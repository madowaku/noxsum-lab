from __future__ import annotations

import math
from typing import Any


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _tent(value: float, center: float, radius: float) -> float:
    if radius <= 0:
        return 0.0
    return _clamp(1.0 - abs(value - center) / radius)


def score_candidate(metrics: dict[str, Any]) -> tuple[float, float, list[str]]:
    """Heuristic v0.2 scores.

    FLOW rewards a visible foothold, short/medium reasoning chain and a small
    final ambiguity. AHA rewards interacting constraints, moderate depth, and
    late information gain while penalizing brute-force-shaped traces.
    """

    opening = float(metrics["opening_strength"])
    pair_synergy = float(metrics["pair_synergy_bits"])
    witness = float(metrics["witness_length"])
    penultimate = float(metrics["penultimate_survivors"])
    late_gain = float(metrics["late_max_information_gain"])
    overlap = float(metrics["overlap_cells"])
    entropy = float(metrics["target_entropy"])
    best_single = float(metrics["best_single_survivors"])
    search_space = max(1.0, float(metrics["search_space"]))

    # FLOW: clear entry, enough steps to feel like a puzzle, then a crisp finish.
    flow_open = opening
    flow_witness = _tent(witness, center=5.0, radius=5.0)
    flow_finish = _tent(math.log2(max(1.0, penultimate)), center=1.5, radius=2.5)
    flow_overlap = _tent(overlap, center=2.0, radius=4.0)
    flow_entropy = _tent(entropy, center=1.25, radius=1.25)
    flow_score = 100.0 * (
        0.30 * flow_open
        + 0.25 * flow_witness
        + 0.20 * flow_finish
        + 0.10 * flow_overlap
        + 0.15 * flow_entropy
    )

    # AHA: no single clue solves everything, but combinations create a sharp
    # change of understanding. Extremely opaque traces are not rewarded.
    single_ratio = best_single / search_space
    aha_not_obvious = _tent(single_ratio, center=0.32, radius=0.32)
    aha_depth = _tent(witness, center=8.0, radius=7.0)
    aha_synergy = _clamp(pair_synergy / 5.0)
    aha_late_gain = _clamp(math.log2(max(1.0, late_gain)) / 5.0)
    aha_overlap = _tent(overlap, center=4.0, radius=5.0)
    brute_force_penalty = _clamp((witness - 14.0) / 8.0)

    aha_score = 100.0 * (
        0.22 * aha_not_obvious
        + 0.22 * aha_depth
        + 0.22 * aha_synergy
        + 0.20 * aha_late_gain
        + 0.14 * aha_overlap
    )
    aha_score *= 1.0 - 0.45 * brute_force_penalty

    tags: list[str] = []
    if opening >= 0.65:
        tags.append("clear_foothold")
    if pair_synergy >= 2.0:
        tags.append("constraint_synergy")
    if 2 <= penultimate <= 5:
        tags.append("snap_finish")
    if late_gain >= 4.0:
        tags.append("late_breakthrough")
    if overlap >= 3:
        tags.append("overlap_rich")
    if witness >= 12:
        tags.append("deep_chain")
    if brute_force_penalty >= 0.5:
        tags.append("bruteforce_smell")

    return round(flow_score, 3), round(aha_score, 3), tags
