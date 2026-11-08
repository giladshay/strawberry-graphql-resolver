from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from strawberry_graphql_resolver.compilers.field_names import selected_top_level_fields
from strawberry_graphql_resolver.queries import Comparison, QueryExpression

MongoComparison = Literal["$eq", "$ne", "$lt", "$lte", "$gt", "$gte"]

_COMPARISON_TO_MONGO: dict[Comparison, MongoComparison] = {
    Comparison.EQ: "$eq",
    Comparison.NEQ: "$ne",
    Comparison.LT: "$lt",
    Comparison.LTE: "$lte",
    Comparison.GT: "$gt",
    Comparison.GTE: "$gte",
}


class MongoDBQuery(BaseModel):
    """MongoDB filter, sort and projection values accepted by PyMongo."""

    filters: dict[str, dict[MongoComparison, Any]]
    sorts: list[tuple[str, int]]
    projection: list[str] = Field(default_factory=list)


def compile_mongo(query: QueryExpression) -> MongoDBQuery:
    """Compile a query expression into a PyMongo-compatible query model."""
    filters: dict[str, Any] = {}
    for filter_expression in query.filters:
        operator = _COMPARISON_TO_MONGO[filter_expression.operator]
        value = filter_expression.value
        filters.setdefault(filter_expression.name, {})[operator] = value

    sorts = [
        (sort.name, 1 if sort.order.name == "ASCENDING" else -1) for sort in query.sorts
    ]
    projection = selected_top_level_fields(query.field_names)
    return MongoDBQuery(filters=filters, sorts=sorts, projection=projection)
