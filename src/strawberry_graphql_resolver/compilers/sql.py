from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from strawberry_graphql_resolver.queries import Comparison, QueryExpression

SqlComparison = Literal["=", "<>", "<", "<=", ">", ">="]
_COMPARISON_TO_SQL: dict[Comparison, SqlComparison] = {
    Comparison.EQ: "=",
    Comparison.NEQ: "<>",
    Comparison.LT: "<",
    Comparison.LTE: "<=",
    Comparison.GT: ">",
    Comparison.GTE: ">=",
}


@dataclass(frozen=True)
class SQLQuery:
    """Parameterized SQL Server query produced from a query expression."""

    statement: str
    parameters: tuple[Any, ...]
    filters: tuple[tuple[str, str, Any], ...]
    sorts: tuple[tuple[str, str], ...]


def compile_sql(query: QueryExpression) -> SQLQuery:
    """Compile a query expression into SQL text and bound parameters."""
    filters = tuple(
        (
            filter_expression.name,
            _COMPARISON_TO_SQL[filter_expression.operator],
            filter_expression.value,
        )
        for filter_expression in query.filters
    )
    sorts = tuple(
        (
            sort.name,
            "ASC" if sort.order.name == "ASCENDING" else "DESC",
        )
        for sort in query.sorts
    )
    fields = (
        ", ".join(
            field_name for field_name in query.field_names if "{" not in field_name
        )
        or "*"
    )
    statement = f"SELECT {fields} FROM {query.schema_name}"
    if where := " AND ".join(f"{name} {operator} %s" for name, operator, _ in filters):
        statement += f" WHERE {where}"
    if order_by := ", ".join(f"{name} {direction}" for name, direction in sorts):
        statement += f" ORDER BY {order_by}"
    return SQLQuery(
        statement=statement,
        parameters=tuple(value for _, _, value in filters),
        filters=filters,
        sorts=sorts,
    )
