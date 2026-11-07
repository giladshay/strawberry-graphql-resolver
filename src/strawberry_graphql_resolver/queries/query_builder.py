from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, Self, TypeVar, TypeVarTuple, cast, overload

from pydantic import BaseModel

from strawberry_graphql_resolver.queries.expressions import (
    QueryExpression,
    QueryFilterExpression,
    QuerySortExpression,
)
from strawberry_graphql_resolver.queries.field_mapper import FieldMapper
from strawberry_graphql_resolver.queries.queryable_metaclass import QueryableMetaclass


def _field_name(field: object) -> str:
    if isinstance(field, FieldMapper):
        return field.name
    if isinstance(field, str):
        return field
    raise TypeError(
        "only() and exclude() accept model field handles such as User.name "
        f"or field-name strings; got {type(field).__name__}"
    )


TField = TypeVar("TField")
Ts = TypeVarTuple("Ts")


class Queryable(ABC, BaseModel, metaclass=QueryableMetaclass):
    """Base model that exposes a fluent query-building API.

    Refer to model fields through the class, so ``only`` and ``exclude``
    complete and validate field names through ordinary attribute access::

        class User(Queryable):
            name: str
            age: int


        names = User.where(User.age >= 18).only(User.name).submit()

    The selected field's value type is preserved: ``only(User.age)`` produces a
    ``Sequence[int]``. Field-name strings such as ``only("name")`` remain
    supported for call sites that build selections dynamically.
    """

    @classmethod
    @abstractmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]: ...

    @classmethod
    def where(cls, *filters: QueryFilterExpression | bool) -> QueryBuilder[Self, Self]:
        return QueryBuilder[Self, Self](cls).where(*filters)

    @classmethod
    def sort(cls, *sorts: QuerySortExpression | Any) -> QueryBuilder[Self, Self]:
        return QueryBuilder[Self, Self](cls).sort(*sorts)

    @classmethod
    @overload
    def only(cls, field: TField, /) -> QueryBuilder[Self, TField]: ...

    @classmethod
    @overload
    def only(cls, *fields: *Ts) -> QueryBuilder[Self, tuple[*Ts]]: ...

    @classmethod
    def only(cls, *field_names: object) -> QueryBuilder[Self, Any]:
        return QueryBuilder[Self, Any](cls).only(*field_names)

    @classmethod
    @overload
    def exclude(cls) -> QueryBuilder[Self, Self]: ...

    @classmethod
    @overload
    def exclude(cls, field: object, /, *fields: object) -> QueryBuilder[Self, Any]: ...

    @classmethod
    def exclude(cls, *field_names: object) -> QueryBuilder[Self, Any]:
        return QueryBuilder[Self, Any](cls).exclude(*field_names)


class QueryBuilder[TModel: Queryable, TValue]:
    """Accumulate filters, sorts, and field selections before submitting a query.

    ``TValue`` describes what :meth:`submit` returns for each result. It is the
    model type when no fields are selected, the field's value type for a
    single-field selection, and a dictionary for multi-field selections.
    """

    def __init__(self, schema: type[TModel]) -> None:
        self._submit = schema.submit
        self._schema = schema
        self._filters: list[QueryFilterExpression] = []
        self._sorts: list[QuerySortExpression] = []
        self._selected_fields: list[str] | None = None

    def where(
        self, *filters: QueryFilterExpression | bool
    ) -> QueryBuilder[TModel, TValue]:
        new_filters = [f for f in filters if isinstance(f, QueryFilterExpression)]
        self._filters.extend(new_filters)
        return self

    def sort(self, *sorts: QuerySortExpression | Any) -> QueryBuilder[TModel, TValue]:
        self._sorts.extend([s for s in sorts if isinstance(s, QuerySortExpression)])
        return self

    @overload
    def only(self) -> QueryBuilder[TModel, TModel]: ...

    @overload
    def only(self, field: TField, /) -> QueryBuilder[TModel, TField]: ...

    @overload
    def only(self, *fields: *Ts) -> QueryBuilder[TModel, tuple[*Ts]]: ...

    def only(self, *field_names: object) -> QueryBuilder[TModel, Any]:
        """Restrict the query to the given model fields.

        Selecting a single field makes :meth:`submit` return that field's value
        for every result. Selecting multiple fields makes it return one
        tuple per result, in the given order.

        Args:
            *field_names: Model field handles such as ``User.name``, or
                field-name strings.

        Returns:
            This builder, allowing further chaining.
        """
        if not field_names:
            return cast("QueryBuilder[TModel, Any]", self)
        self._selected_fields = [_field_name(field) for field in field_names]
        return cast("QueryBuilder[TModel, Any]", self)

    @overload
    def exclude(self) -> QueryBuilder[TModel, TModel]: ...

    @overload
    def exclude(
        self, field: object, /, *fields: object
    ) -> QueryBuilder[TModel, Any]: ...

    def exclude(self, *field_names: object) -> QueryBuilder[TModel, Any]:
        """Remove the given model fields from the query.

        The result shape is determined by the number of remaining fields: one
        field produces a sequence of values, while multiple fields produce one
        tuple per result.

        Args:
            *field_names: Model field handles such as ``User.name``, or
                field-name strings.

        Returns:
            This builder, allowing further chaining.
        """
        if not field_names:
            return cast("QueryBuilder[TModel, Any]", self)
        excluded = {_field_name(field) for field in field_names}
        currently_selected = (
            self._selected_fields
            if self._selected_fields is not None
            else list(self._schema.model_fields)
        )
        self._selected_fields = [
            name for name in currently_selected if name not in excluded
        ]
        return cast("QueryBuilder[TModel, Any]", self)

    def submit(self) -> Sequence[TValue]:
        """Submit the query and return the requested fields.

        Without a field selection, the model's submission handler result is
        returned unchanged. With a selection, a single selected field produces
        a sequence of values and multiple selected fields produce a sequence of
        dictionaries.
        """
        field_names = (
            list(self._selected_fields)
            if self._selected_fields is not None
            else list(self._schema.model_fields)
        )
        query = QueryExpression(
            schema_name=f"{self._schema.__name__.lower()}s",
            field_names=field_names,
            filters=self._filters,
            sorts=self._sorts,
        )
        results = self._submit(query)
        if self._selected_fields is None:
            return cast("Sequence[TValue]", results)
        return cast(
            "Sequence[TValue]",
            [self._project(result, field_names) for result in results],
        )

    @classmethod
    def _project(cls, result: Any, field_names: list[str]) -> Any:
        values = [cls._field_value(result, field_name) for field_name in field_names]
        if len(values) == 1:
            return values[0]
        return tuple(values)

    @staticmethod
    def _field_value(result: Any, field_name: str) -> Any:
        if isinstance(result, Mapping):
            return result[field_name]
        return getattr(result, field_name)
