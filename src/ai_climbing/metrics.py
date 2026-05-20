from __future__ import annotations

import math
from typing import Iterable


def angle_degrees(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    """Return the angle ABC in degrees."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    norm_ba = math.hypot(*ba)
    norm_bc = math.hypot(*bc)
    if norm_ba == 0.0 or norm_bc == 0.0:
        return 0.0
    cosine = max(-1.0, min(1.0, dot / (norm_ba * norm_bc)))
    return math.degrees(math.acos(cosine))


def midpoint(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def average(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)
