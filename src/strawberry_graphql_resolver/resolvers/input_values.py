from __future__ import annotations

from typing import Any

from strawberry_graphql_resolver.queries import Comparison


def input_values(value: Any, name: str) -> list[tuple[str, Any]]:
    selected = getattr(value, name, None) if value is not None else None
    if selected is None:
        return []
    return [
        (field_name, getattr(selected, field_name))
        for field_name in selected.__annotations__
        if getattr(selected, field_name) is not None
    ]


def operator_values(value: Any, operators: Any) -> list[tuple[Comparison, Any]]:
    return [
        (operator, getattr(value, operator_name))
        for operator_name, operator in operators.__members__.items()
        if getattr(value, operator_name) is not None
    ]
