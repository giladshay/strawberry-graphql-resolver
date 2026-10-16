from __future__ import annotations

from enum import StrEnum


class DBType(StrEnum):
    """Select how a resolver receives a parsed GraphQL query."""

    NONE = "none"
    MONGO_DB = "mongo"
    SQL = "sql"
