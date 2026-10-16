from __future__ import annotations

from typing import override

from strawberry_graphql_resolver.queries.expressions import (
    QueryFilterExpression,
    QuerySortExpression,
)
from strawberry_graphql_resolver.queries.operators import Comparison, SortOrder


class FieldMapper:
    def __init__(self, name: str) -> None:
        self._name = name

    @override
    def __eq__(self, other: object) -> QueryFilterExpression:  # ty: ignore[invalid-method-override]
        return QueryFilterExpression(
            name=self._name, operator=Comparison.EQ, value=other
        )

    def __lt__(self, other: object) -> QueryFilterExpression:
        return QueryFilterExpression(
            name=self._name, operator=Comparison.LT, value=other
        )

    def __gt__(self, other: object) -> QueryFilterExpression:
        return QueryFilterExpression(
            name=self._name, operator=Comparison.GT, value=other
        )

    def __le__(self, other: object) -> QueryFilterExpression:
        return QueryFilterExpression(
            name=self._name, operator=Comparison.LTE, value=other
        )

    def __ge__(self, other: object) -> QueryFilterExpression:
        return QueryFilterExpression(
            name=self._name, operator=Comparison.GTE, value=other
        )

    @override
    def __ne__(self, other: object) -> QueryFilterExpression:  # ty: ignore[invalid-method-override]
        return QueryFilterExpression(
            name=self._name, operator=Comparison.NEQ, value=other
        )

    def __pos__(self) -> QuerySortExpression:
        return QuerySortExpression(name=self._name, order=SortOrder.ASCENDING)

    def __neg__(self) -> QuerySortExpression:
        return QuerySortExpression(name=self._name, order=SortOrder.DESCENDING)
