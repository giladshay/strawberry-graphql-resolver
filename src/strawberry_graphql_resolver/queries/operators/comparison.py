from __future__ import annotations

from enum import IntFlag


class Comparison(IntFlag):
    """Comparison operators supported by query expressions."""

    EQ = 0b001
    LT = 0b010
    GT = 0b100
    LTE = 0b011
    GTE = 0b101
    NEQ = 0b110
