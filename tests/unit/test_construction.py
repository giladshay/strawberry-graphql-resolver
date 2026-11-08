from __future__ import annotations

import json

from pydantic import BaseModel

from strawberry_graphql_resolver import construct_model, construct_models


class Location(BaseModel):
    city: str
    website: str


class Customer(BaseModel):
    id: int
    name: str
    age: int
    location: Location


def test_construct_model_full_row_validates() -> None:
    data = {
        "id": 1,
        "name": "Ada",
        "age": 37,
        "location": {"city": "London", "website": "https://ada.example"},
    }
    result = construct_model(Customer, data)
    assert isinstance(result, Customer)
    assert result.name == "Ada"
    assert result.location.city == "London"


def test_construct_model_partial_row_constructs() -> None:
    data = {"name": "Ada", "age": 37}
    result = construct_model(Customer, data)
    assert isinstance(result, Customer)
    assert result.name == "Ada"
    assert result.age == 37


def test_construct_model_coerces_nested_json_string() -> None:
    data = {
        "id": 1,
        "name": "Ada",
        "age": 37,
        "location": json.dumps({"city": "London", "website": "https://ada.example"}),
    }
    result = construct_model(Customer, data)
    assert isinstance(result, Customer)
    assert result.location.city == "London"


def test_construct_model_does_not_coerce_non_model_strings() -> None:
    class Tagged(BaseModel):
        name: str
        tag: str

    result = construct_model(Tagged, {"name": "Ada", "tag": '{"not": "json"}'})
    assert result.tag == '{"not": "json"}'


def test_construct_models_returns_list() -> None:
    rows = [
        {
            "id": 1,
            "name": "Ada",
            "age": 37,
            "location": {"city": "London", "website": "https://ada.example"},
        },
        {"id": 2, "name": "Grace", "age": 28},
    ]
    results = construct_models(Customer, rows)
    assert len(results) == 2
    assert isinstance(results[0], Customer)
    assert isinstance(results[1], Customer)
    assert results[1].name == "Grace"


def test_construct_model_optional_nested() -> None:
    class WithOptional(BaseModel):
        name: str
        location: Location | None = None

    result = construct_model(WithOptional, {"name": "Ada"})
    assert result.name == "Ada"
    assert result.location is None
