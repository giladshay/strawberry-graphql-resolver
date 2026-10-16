from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Self

from pydantic import BaseModel

from strawberry_graphql_resolver.queries.expressions import (
    QueryExpression,
    QueryFilterExpression,
    QuerySortExpression,
)
from strawberry_graphql_resolver.queries.queryable_metaclass import QueryableMetaclass


class Queryable(ABC, BaseModel, metaclass=QueryableMetaclass):
    @classmethod
    @abstractmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]: ...
    @classmethod
    def where(cls, *filters: QueryFilterExpression | bool) -> QueryBuilder[Self]:
        return QueryBuilder[Self](cls).where(*filters)

    @classmethod
    def sort(cls, *sorts: QuerySortExpression | Any) -> QueryBuilder[Self]:
        return QueryBuilder[Self](cls).sort(*sorts)


class QueryBuilder[T: Queryable]:
    def __init__(self, schema: type[T]) -> None:
        self._submit = schema.submit
        self._schema = schema
        self._filters: list[QueryFilterExpression] = []
        self._sorts: list[QuerySortExpression] = []

    def where(self, *filters: QueryFilterExpression | bool) -> QueryBuilder[T]:
        new_filters = [f for f in filters if isinstance(f, QueryFilterExpression)]
        self._filters.extend(new_filters)
        return self

    def sort(self, *sorts: QuerySortExpression | Any) -> QueryBuilder[T]:
        self._sorts.extend([s for s in sorts if isinstance(s, QuerySortExpression)])
        return self

    def submit(self) -> Sequence[T]:
        query = QueryExpression(
            schema_name=f"{self._schema.__name__.lower()}s",
            field_names=list(self._schema.model_fields),
            filters=self._filters,
            sorts=self._sorts,
        )
        return self._submit(query)
