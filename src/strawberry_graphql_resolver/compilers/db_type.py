from __future__ import annotations

from enum import StrEnum


class DBType(StrEnum):
    NONE = "none"
    MONGO_DB = "mongo"
    SQL = "sql"
