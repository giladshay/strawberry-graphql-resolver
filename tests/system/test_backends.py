from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from strawberry_graphql_resolver.queries import (
    Comparison,
    QueryExpression,
    QueryFilterExpression,
    QuerySortExpression,
    SortOrder,
)

from .app import Customer


def submit(
    client: TestClient,
    *,
    filters: list[QueryFilterExpression] | None = None,
    sorts: list[QuerySortExpression] | None = None,
) -> list[Customer]:
    query = QueryExpression(
        schema_name="customers",
        field_names=["id", "name", "age", "location { city website }"],
        filters=filters or [],
        sorts=sorts or [],
    )
    query._query_input_name = "CustomerInput"
    graphql, variables = query.to_graphql()
    response = client.post(
        "/graphql",
        json={"query": graphql, "variables": variables},
    )
    response.raise_for_status()
    payload = response.json()
    assert "errors" not in payload, payload.get("errors")
    return [Customer.model_validate(item) for item in payload["data"]["customers"]]


def _filter(name: str, operator: Comparison, value: Any) -> QueryFilterExpression:
    return QueryFilterExpression(name=name, operator=operator, value=value)


@pytest.mark.parametrize(
    ("operator", "value", "expected_ids"),
    [
        (Comparison.EQ, 28, [2]),
        (Comparison.NEQ, 28, [1, 3]),
        (Comparison.LT, 28, [3]),
        (Comparison.LTE, 28, [2, 3]),
        (Comparison.GT, 28, [1]),
        (Comparison.GTE, 28, [1, 2]),
    ],
)
def test_all_comparison_operators_across_backends(
    graphql_client: TestClient,
    operator: Comparison,
    value: int,
    expected_ids: list[int],
) -> None:
    customers = submit(
        graphql_client,
        filters=[_filter("age", operator, value)],
        sorts=[QuerySortExpression(name="id", order=SortOrder.ASCENDING)],
    )

    assert [customer.id for customer in customers] == expected_ids


def test_nested_models_and_pydantic_serialization(
    graphql_client: TestClient,
) -> None:
    customers = submit(
        graphql_client,
        filters=[_filter("id", Comparison.EQ, 1)],
    )

    assert len(customers) == 1
    customer = customers[0]
    assert customer.name == "ADA"
    assert customer.model_dump(mode="json")["name"] == "ADA"
    assert customer.age == 37
    assert customer.location.city == "London"
    assert str(customer.location.website) == "https://ada.example/"


def test_multiple_filters_and_both_sort_directions(
    graphql_client: TestClient,
) -> None:
    descending = submit(
        graphql_client,
        filters=[
            _filter("age", Comparison.GTE, 18),
            _filter("age", Comparison.LTE, 37),
        ],
        sorts=[QuerySortExpression(name="age", order=SortOrder.DESCENDING)],
    )
    ascending = submit(
        graphql_client,
        sorts=[QuerySortExpression(name="age", order=SortOrder.ASCENDING)],
    )

    assert [customer.id for customer in descending] == [1, 2, 3]
    assert [customer.id for customer in ascending] == [3, 2, 1]


def test_empty_query_returns_all_records(
    graphql_client: TestClient,
) -> None:
    customers = submit(graphql_client)

    assert {customer.id for customer in customers} == {1, 2, 3}
