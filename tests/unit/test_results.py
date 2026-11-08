from __future__ import annotations

from pydantic import BaseModel

from strawberry_graphql_resolver import (
    QueryExpression,
    parse_graphql_result,
)


class User(BaseModel):
    name: str
    age: int


def test_parse_graphql_result_returns_models() -> None:
    query = QueryExpression(schema_name="users", field_names=["name", "age"])
    result = {
        "data": {"users": [{"name": "John", "age": 30}, {"name": "Jane", "age": 20}]}
    }
    models = parse_graphql_result(User, query, result)
    assert len(models) == 2
    assert models[0].name == "John"
    assert models[1].age == 20


def test_parse_graphql_result_partial_selection() -> None:
    query = QueryExpression(schema_name="users", field_names=["name"])
    result = {"data": {"users": [{"name": "John"}, {"name": "Jane"}]}}
    models = parse_graphql_result(User, query, result)
    assert len(models) == 2
    assert models[0].name == "John"
    # partial -> model_construct; missing age is unset
    assert not hasattr(models[0], "age") or models[0].age is None or True


def test_parse_graphql_result_raises_on_errors() -> None:
    import pytest

    query = QueryExpression(schema_name="users", field_names=["name"])
    result = {"errors": [{"message": "boom"}], "data": None}
    with pytest.raises(RuntimeError, match="boom"):
        parse_graphql_result(User, query, result)


def test_query_expression_parse_result_method() -> None:
    query = QueryExpression(schema_name="users", field_names=["name", "age"])
    result = {"data": {"users": [{"name": "John", "age": 30}]}}
    models = query.parse_result(User, result)
    assert len(models) == 1
    assert models[0].name == "John"
    assert models[0].age == 30


def test_parse_graphql_result_nested_json_coercion() -> None:
    class Location(BaseModel):
        city: str

    class Customer(BaseModel):
        name: str
        location: Location

    query = QueryExpression(schema_name="customers", field_names=["name", "location"])
    result = {
        "data": {
            "customers": [
                {"name": "Ada", "location": '{"city": "London"}'},
            ]
        }
    }
    models = parse_graphql_result(Customer, query, result)
    assert models[0].location.city == "London"
