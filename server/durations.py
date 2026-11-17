"""MuseScore duration units.

A quarter note is 480 ticks. Whole note = 1920 ticks.
Plugin code must use the same fractions: cursor.setDuration takes
numerator/denominator, not ticks.
"""

from typing import Dict, Tuple

TICKS_PER_WHOLE = 1920

# ticks -> (numerator, denominator) of a whole note
FRACTION_BY_TICKS: Dict[int, Tuple[int, int]] = {
    1920: (1, 1),
    1440: (3, 4),
    960: (1, 2),
    720: (3, 8),
    640: (1, 3),
    480: (1, 4),
    360: (3, 16),
    320: (1, 6),
    240: (1, 8),
    180: (3, 32),
    160: (1, 12),
    120: (1, 16),
    80: (1, 24),
    60: (1, 32),
}

NAME_BY_TICKS: Dict[int, str] = {
    1920: "whole",
    1440: "dotted half",
    960: "half",
    720: "dotted quarter",
    640: "half triplet",
    480: "quarter",
    360: "dotted eighth",
    320: "quarter triplet",
    240: "eighth",
    180: "dotted 16th",
    160: "eighth triplet",
    120: "16th",
    80: "16th triplet",
    60: "32nd",
}


def ticks_per_beat(denominator: int) -> int:
    """Ticks in one beat for a time-signature denominator (4 = quarter)."""
    if denominator <= 0 or TICKS_PER_WHOLE % denominator != 0:
        return 480
    return TICKS_PER_WHOLE // denominator


def measure_length(numerator: int, denominator: int) -> int:
    return ticks_per_beat(denominator) * max(numerator, 1)


def ticks_to_fraction(ticks: int) -> Tuple[int, int]:
    known = FRACTION_BY_TICKS.get(int(ticks))
    if known:
        return known
    value = abs(int(ticks)) or 480
    factor = _gcd(value, TICKS_PER_WHOLE)
    return value // factor, TICKS_PER_WHOLE // factor


def nearest_duration(ticks: int) -> int:
    return min(FRACTION_BY_TICKS, key=lambda candidate: (abs(candidate - int(ticks)), -candidate))


def format_beat(tick: int, ticks_for_beat: int = 480) -> str:
    if ticks_for_beat <= 0:
        ticks_for_beat = 480
    beat = 1 + (tick / ticks_for_beat)
    if abs(beat - round(beat)) < 1e-6:
        return str(int(round(beat)))
    text = f"{beat:.2f}".rstrip("0").rstrip(".")
    return text


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a or 1
