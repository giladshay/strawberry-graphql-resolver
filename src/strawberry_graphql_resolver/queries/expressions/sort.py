from __future__ import annotations

from strawberry_graphql_resolver.queries.expressions import BaseQueryExpression
from strawberry_graphql_resolver.queries.operators import SortOrder


class QuerySortExpression(BaseQueryExpression):
    name: str
    order: SortOrder
