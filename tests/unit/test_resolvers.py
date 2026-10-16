from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    PositiveInt,
    field_serializer,
    field_validator,
)

from strawberry_graphql_resolver import DBType, MongoDBQuery, SQLQuery, resolve_query
from strawberry_graphql_resolver.queries import QueryExpression
from strawberry_graphql_resolver.resolvers.pydantic_types import create_pydantic_types


class Address(BaseModel):
    city: str
    website: AnyUrl


class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    age: PositiveInt
    address: Address

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be empty")
        return value.strip()

    @field_serializer("name")
    def serialize_name(self, value: str) -> str:
        return value.upper()


def test_nested_pydantic_types_support_constrained_and_url_fields() -> None:
    input_type, output_type = create_pydantic_types(Customer)
    customer = Customer(
        name="Ada",
        age=37,
        address=Address(city="London", website="https://example.com"),
    )

    converted_input = cast(Any, input_type.from_pydantic(customer))
    converted_output = cast(Any, output_type.from_pydantic(customer))
    assert converted_input.name == "Ada"
    assert converted_output.address.city == "London"
    assert str(converted_output.address.website) == ("https://example.com/")


def test_none_database_mode_passes_original_query_expression() -> None:
    received: list[QueryExpression] = []

    def handler(query: QueryExpression) -> Sequence[Customer]:
        received.append(query)
        return cast(Sequence[Customer], [])

    field = cast(Any, resolve_query(handler, db=DBType.NONE))
    result = field.base_resolver(None, query=None)

    assert result == []
    assert len(received) == 1
    assert isinstance(received[0], QueryExpression)


def test_sql_and_mongo_modes_pass_compiled_models() -> None:
    received: list[Any] = []

    def sql_handler(query: SQLQuery) -> Sequence[Customer]:
        received.append(query)
        return cast(Sequence[Customer], [])

    def mongo_handler(query: MongoDBQuery) -> Sequence[Customer]:
        received.append(query)
        return cast(Sequence[Customer], [])

    sql_resolver = cast(Any, resolve_query(sql_handler, db=DBType.SQL))
    mongo_resolver = cast(Any, resolve_query(mongo_handler, db=DBType.MONGO_DB))

    sql_resolver.base_resolver(None, query=None)
    mongo_resolver.base_resolver(None, query=None)

    assert isinstance(received[0], SQLQuery)
    assert isinstance(received[1], MongoDBQuery)
