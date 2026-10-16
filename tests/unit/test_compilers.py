from __future__ import annotations

import pytest

from strawberry_graphql_resolver.compilers import (
    MongoDBQuery,
    compile_mongo,
    compile_sql,
)
from strawberry_graphql_resolver.queries import (
    Comparison,
    QueryExpression,
    QueryFilterExpression,
    QuerySortExpression,
    SortOrder,
)


@pytest.fixture
def query() -> QueryExpression:
    return QueryExpression(
        schema_name="users",
        field_names=["name", "age"],
        filters=[
            QueryFilterExpression(name="age", operator=Comparison.GTE, value=18),
            QueryFilterExpression(
                name="name", operator=Comparison.NEQ, value="blocked"
            ),
        ],
        sorts=[
            QuerySortExpression(name="age", order=SortOrder.DESCENDING),
            QuerySortExpression(name="name", order=SortOrder.ASCENDING),
        ],
    )


def test_compile_sql_returns_parameterized_statement(query: QueryExpression) -> None:
    compiled = compile_sql(query)

    assert compiled.statement == (
        "SELECT name, age FROM users WHERE age >= %s AND name <> %s "
        "ORDER BY age DESC, name ASC"
    )
    assert compiled.parameters == (18, "blocked")
    assert compiled.filters == (("age", ">=", 18), ("name", "<>", "blocked"))
    assert compiled.sorts == (("age", "DESC"), ("name", "ASC"))


def test_compile_mongo_returns_pymongo_filter_and_sort(
    query: QueryExpression,
) -> None:
    compiled = compile_mongo(query)

    assert isinstance(compiled, MongoDBQuery)
    assert compiled.filters == {
        "age": {"$gte": 18},
        "name": {"$ne": "blocked"},
    }
    assert compiled.sorts == [("age", -1), ("name", 1)]


def test_compilers_handle_an_empty_query() -> None:
    query = QueryExpression(schema_name="items", field_names=[])

    sql = compile_sql(query)
    mongo = compile_mongo(query)

    assert sql.statement == "SELECT * FROM items"
    assert sql.parameters == ()
    assert sql.filters == ()
    assert sql.sorts == ()
    assert mongo.filters == {}
    assert mongo.sorts == []


@pytest.mark.parametrize(
    ("operator", "sql", "mongo"),
    [
        (Comparison.EQ, "=", "$eq"),
        (Comparison.NEQ, "<>", "$ne"),
        (Comparison.LT, "<", "$lt"),
        (Comparison.LTE, "<=", "$lte"),
        (Comparison.GT, ">", "$gt"),
        (Comparison.GTE, ">=", "$gte"),
    ],
)
def test_compile_comparison_operators(
    operator: Comparison, sql: str, mongo: str
) -> None:
    query = QueryExpression(
        schema_name="items",
        field_names=[],
        filters=[QueryFilterExpression(name="value", operator=operator, value=7)],
    )

    assert compile_sql(query).filters == (("value", sql, 7),)
    assert compile_mongo(query).filters == {"value": {mongo: 7}}
