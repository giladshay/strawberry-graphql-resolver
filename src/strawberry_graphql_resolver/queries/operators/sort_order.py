from __future__ import annotations

from enum import IntFlag


class SortOrder(IntFlag):
    """Sort directions supported by query expressions."""

    ASCENDING = 1
    DESCENDING = 2
