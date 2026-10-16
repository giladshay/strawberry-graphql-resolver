from __future__ import annotations

from typing import Any

from strawberry_graphql_resolver.queries.expressions.base import BaseQueryExpression
from strawberry_graphql_resolver.queries.operators import Comparison


class QueryFilterExpression(BaseQueryExpression):
    """Represent one field comparison in a query."""

    name: str
    operator: Comparison
    value: Any
