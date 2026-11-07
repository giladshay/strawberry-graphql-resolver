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


class PeopleQuery(Queryable):
    name: str
    age: int

    @classmethod
    @override
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        name = query.filters[0].value if query.filters else "John"
        return [
            cls(name=name, age=30),
            cls(name="Jane", age=18),
        ]


def test_only_one_field_returns_field_values() -> None:
    queries: list[QueryExpression] = []

    class RecordingQuery(Queryable):
        name: str
        age: int

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            queries.append(query)
            return [
                cls(name="John", age=30),
                cls(name="Jane", age=18),
            ]

    result = (
        RecordingQuery.where(cast(Any, RecordingQuery.name == "John"))
        .only("name")
        .submit()
    )

    assert result == ["John", "Jane"]
    assert queries[0].field_names == ["name"]


def test_only_multiple_fields_returns_tuples() -> None:
    result = (
        PeopleQuery.where(cast(Any, PeopleQuery.name == "John"))
        .only("name", "age")
        .submit()
    )

    assert result == [
        ("John", 30),
        ("Jane", 18),
    ]


def test_only_all_fields_returns_tuples() -> None:
    result = (
        PeopleQuery.where(cast(Any, PeopleQuery.name == "John"))
        .only("age", "name")
        .submit()
    )

    assert result == [
        (30, "John"),
        (18, "Jane"),
    ]


def test_exclude_returns_values_for_one_remaining_field() -> None:
    result = (
        PeopleQuery.where(cast(Any, PeopleQuery.name == "John")).exclude("age").submit()
    )

    assert result == ["John", "Jane"]


def test_exclude_returns_dictionaries_for_multiple_remaining_fields() -> None:
    class PersonQuery(Queryable):
        name: str
        age: int
        active: bool

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            return [cls(name="John", age=30, active=True)]

    result = PersonQuery.exclude("active").submit()

    assert result == [("John", 30)]


def test_only_and_exclude_combine() -> None:
    class PersonQuery(Queryable):
        name: str
        age: int
        active: bool

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            return [cls(name="John", age=30, active=True)]

    result = PersonQuery.only("name", "age", "active").exclude("active").submit()

    assert result == [("John", 30)]


def test_submit_without_field_selection_returns_models() -> None:
    result = PeopleQuery.where(cast(Any, PeopleQuery.name == "John")).submit()

    assert result == [
        PeopleQuery(name="John", age=30),
        PeopleQuery(name="Jane", age=18),
    ]


def test_only_accepts_plain_mapping_results() -> None:
    class MappingQuery(Queryable):
        name: str
        age: int

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            return cast(
                Sequence[Self],
                [
                    {"name": "John", "age": 30},
                    {"name": "Jane", "age": 18},
                ],
            )

    assert MappingQuery.only("name").submit() == ["John", "Jane"]
    assert MappingQuery.only("name", "age").submit() == [
        ("John", 30),
        ("Jane", 18),
    ]


def test_only_keeps_unknown_fields_in_the_selection() -> None:
    builder = PeopleQuery.only("missing")

    assert builder._selected_fields == ["missing"]


def test_only_does_not_ignore_known_and_unknown_fields() -> None:
    builder = PeopleQuery.only(
        "name",
        "missing",
    )

    assert builder._selected_fields == ["name", "missing"]


def test_exclude_unknown_field_keeps_every_model_field() -> None:
    result = PeopleQuery.exclude("missing").submit()

    assert result == [
        ("John", 30),
        ("Jane", 18),
    ]


def test_custom_field_selection_methods_are_preserved() -> None:
    class CustomQuery(Queryable):
        name: str

        @override
        @classmethod
        def only(cls, *field_names: object) -> Any:
            return ("custom", field_names)

    assert CustomQuery.only("name") == ("custom", ("name",))


def test_only_accepts_field_handles() -> None:
    result = (
        PeopleQuery.where(cast(Any, PeopleQuery.name == "John"))
        .only(PeopleQuery.name)
        .submit()
    )

    assert result == ["John", "Jane"]


def test_only_multiple_field_handles_returns_tuples() -> None:
    result = (
        PeopleQuery.where(cast(Any, PeopleQuery.name == "John"))
        .only(PeopleQuery.name, PeopleQuery.age)
        .submit()
    )

    assert result == [
        ("John", 30),
        ("Jane", 18),
    ]


def test_exclude_field_handle_keeps_every_other_field() -> None:
    result = PeopleQuery.exclude(PeopleQuery.age).submit()

    assert result == ["John", "Jane"]


def test_field_handles_with_defaults() -> None:
    class QueryWithDefault(Queryable):
        name: str
        role: str = "admin"

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            return [cls(name="John", role="admin")]

    assert QueryWithDefault.only(QueryWithDefault.role).submit() == ["admin"]
    assert QueryWithDefault.only(
        QueryWithDefault.name, QueryWithDefault.role
    ).submit() == [("John", "admin")]


def test_field_handles_inherited() -> None:
    class BaseQuery(Queryable):
        name: str
        age: int

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            return [cls(name="John", age=30)]

    class ExtendedQuery(BaseQuery):
        mail: str = "x@example.com"

        @classmethod
        @override
        def submit(cls, query: QueryExpression) -> Sequence[Self]:
            return [cls(name="John", age=30, mail="x@example.com")]

    assert ExtendedQuery.only(ExtendedQuery.name).submit() == ["John"]
    assert ExtendedQuery.only(ExtendedQuery.mail).submit() == ["x@example.com"]
    assert ExtendedQuery.only(ExtendedQuery.name, ExtendedQuery.mail).submit() == [
        ("John", "x@example.com")
    ]


def test_mixed_field_handles_and_strings() -> None:
    result = PeopleQuery.only(PeopleQuery.name, "age").submit()
    assert result == [
        ("John", 30),
        ("Jane", 18),
    ]
