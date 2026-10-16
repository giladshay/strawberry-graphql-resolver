from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Self, cast, override

import pytest
from pydantic import BaseModel

from strawberry_graphql_resolver.queries import (
    Comparison,
    Queryable,
    QueryExpression,
    SortOrder,
)
from strawberry_graphql_resolver.queries.expressions import (
    QueryFilterExpression,
    QuerySortExpression,
)


class User(BaseModel):
    name: str
    age: int


class UserQuery(Queryable):
    name: str
    age: int

    @classmethod
    @override
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        return [cls(name=query.filters[0].value, age=30)]


def test_query_expression_serializes_filters_sorts_and_fields() -> None:
    expression = QueryExpression(
        schema_name="users",
        field_names=["name", "age"],
        filters=[
            cast(QueryFilterExpression, cast(Any, UserQuery.name == "John")),
            cast(QueryFilterExpression, cast(Any, UserQuery.age >= 18)),
        ],
        sorts=[cast(QuerySortExpression, cast(Any, -UserQuery.age))],
    )
    expression._query_input_name = "UserInput"

    graphql, variables = expression.to_graphql()

    assert "query FetchData($query: UserInput!)" in graphql
    assert "users(query: $query)" in graphql
    assert variables == {
        "query": {
            "filters": {"name": {"EQ": "John"}, "age": {"GTE": 18}},
            "sorts": {"age": "DESCENDING"},
        }
    }


def test_query_builder_ignores_non_query_expressions_and_submits() -> None:
    result = (
        UserQuery.where(UserQuery.name == "John", False)
        .sort(-UserQuery.age, "invalid")
        .submit()
    )

    assert result == [UserQuery(name="John", age=30)]


def test_queryable_fields_create_expected_comparison_expressions() -> None:
    expression = cast(QueryFilterExpression, cast(Any, UserQuery.name != "Jane"))

    assert expression.operator is Comparison.NEQ
    assert expression.name == "name"
    assert expression.value == "Jane"
    assert (
        cast(QuerySortExpression, cast(Any, -UserQuery.age)).order
        is SortOrder.DESCENDING
    )


@pytest.mark.parametrize(
    ("expression", "operator", "value"),
    [
        (lambda: UserQuery.age == 7, Comparison.EQ, 7),
        (lambda: UserQuery.age != 7, Comparison.NEQ, 7),
        (lambda: UserQuery.age < 7, Comparison.LT, 7),
        (lambda: UserQuery.age <= 7, Comparison.LTE, 7),
        (lambda: UserQuery.age > 7, Comparison.GT, 7),
        (lambda: UserQuery.age >= 7, Comparison.GTE, 7),
    ],
)
def test_every_field_comparison_operator(
    expression: Any, operator: Comparison, value: int
) -> None:
    result = cast(QueryFilterExpression, expression())

    assert result.name == "age"
    assert result.operator is operator
    assert result.value == value


def test_query_builder_preserves_filter_and_sort_order() -> None:
    result = UserQuery.where(
        cast(Any, UserQuery.age >= 18),
        cast(Any, UserQuery.name != "blocked"),
    ).sort(+UserQuery.age, -cast(Any, UserQuery.name))

    assert result._filters[0].name == "age"
    assert result._filters[1].name == "name"
    assert [sort.order for sort in result._sorts] == [
        SortOrder.ASCENDING,
        SortOrder.DESCENDING,
    ]
