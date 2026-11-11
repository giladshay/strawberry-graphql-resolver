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
from strawberry_graphql_resolver.resolvers.input_values import (
    input_values,
    operator_values,
)
from strawberry_graphql_resolver.resolvers.public import flattened_pydantic_resolver
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


class Person(BaseModel):
    children: list[Person]
    age: int


class TreeNode(BaseModel):
    children: list[TreeNode]
    parent: TreeNode | None = None
    labels: list[str] = []
    lookup: dict[str, TreeNode] = {}


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


def test_recursive_pydantic_types_support_nested_conversion() -> None:
    input_type, output_type = create_pydantic_types(Person)
    person = Person(children=[Person(children=[], age=2)], age=1)

    converted_input = cast(Any, input_type.from_pydantic(person))
    converted_output = cast(Any, output_type.from_pydantic(person))

    assert converted_input.children[0].age == 2
    assert converted_output.children[0].age == 2


def test_recursive_pydantic_types_support_unions_and_container_fields() -> None:
    input_type, output_type = create_pydantic_types(TreeNode)
    node = TreeNode(
        children=[TreeNode(children=[], labels=["child"])],
        parent=TreeNode(children=[], labels=["parent"]),
        labels=["root"],
        lookup={"first": TreeNode(children=[], labels=["lookup"])},
    )

    converted_input = cast(Any, input_type.from_pydantic(node))
    converted_output = cast(Any, output_type.from_pydantic(node))

    assert converted_input.children[0].labels == ["child"]
    assert converted_input.parent.labels == ["parent"]
    assert converted_input.lookup["first"].labels == ["lookup"]
    assert converted_output.children[0].labels == ["child"]
    assert converted_output.parent.labels == ["parent"]
    assert converted_output.lookup["first"].labels == ["lookup"]


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


def test_resolver_uses_selected_fields_from_info() -> None:
    from types import SimpleNamespace

    received: list[Any] = []

    def handler(query: SQLQuery) -> Sequence[Customer]:
        received.append(query)
        return cast(Sequence[Customer], [])

    resolver = cast(Any, resolve_query(handler, db=DBType.SQL))
    fake_info = SimpleNamespace(
        selected_fields=[
            SimpleNamespace(name="customers", selections=[SimpleNamespace(name="name")])
        ]
    )
    resolver.base_resolver(None, query=None, info=fake_info)
    assert "name" in received[0].statement

    # selected_fields without sub-selections uses their names directly
    fake_info2 = SimpleNamespace(
        selected_fields=[SimpleNamespace(name="age", selections=[])]
    )
    received2: list[Any] = []

    def handler2(query: SQLQuery) -> Sequence[Customer]:
        received2.append(query)
        return cast(Sequence[Customer], [])

    resolver2 = cast(Any, resolve_query(handler2, db=DBType.SQL))
    resolver2.base_resolver(None, query=None, info=fake_info2)
    assert "age" in received2[0].statement


def test_resolver_handler_with_self_parameter() -> None:
    received: list[Any] = []

    def handler(self: Any, query: SQLQuery) -> Sequence[Customer]:
        received.append(query)
        return cast(Sequence[Customer], [])

    resolver = cast(Any, resolve_query(handler, db=DBType.SQL))
    resolver.base_resolver(None, query=None)
    assert isinstance(received[0], SQLQuery)


def test_input_values_handles_none_and_populated() -> None:
    assert input_values(None, "filters") == []

    class Filters:
        name: str = "Ada"
        age: int | None = None

    class Container:
        filters: Filters = Filters()

    assert input_values(Container, "filters") == [("name", "Ada")]


def test_operator_values_filters_none_operators() -> None:
    from enum import Enum

    class Op(Enum):
        EQ = "eq"
        NEQ = "neq"

    class Value:
        EQ = 5
        NEQ = None

    result = operator_values(
        Value, type("Ops", (), {"__members__": {"EQ": Op.EQ, "NEQ": Op.NEQ}})
    )
    assert result == [(Op.EQ, 5)]


def test_resolve_query_decorator_form() -> None:
    @resolve_query(db=DBType.NONE)
    def handler(query: QueryExpression) -> Sequence[Customer]:
        return cast(Sequence[Customer], [])

    field = cast(Any, handler)
    result = field.base_resolver(None, query=None)
    assert result == []


def test_resolve_query_staticmethod_form() -> None:
    def handler(query: QueryExpression) -> Sequence[Customer]:
        return cast(Sequence[Customer], [])

    field = cast(Any, resolve_query(staticmethod(handler), db=DBType.NONE))
    result = field.base_resolver(None, query=None)
    assert result == []


def test_resolve_query_owner_based_model_type() -> None:
    class OwnerModel(Customer):
        @classmethod
        def handler(cls, query: QueryExpression) -> Sequence[Customer]:
            return cast(Sequence[Customer], [])

    field = cast(Any, resolve_query(OwnerModel.handler, db=DBType.NONE))
    result = field.base_resolver(None, query=None)
    assert result == []


def test_flattened_pydantic_resolver() -> None:
    def handler(query: QueryExpression) -> Sequence[Customer]:
        return cast(Sequence[Customer], [])

    resolver = flattened_pydantic_resolver(cast(Any, Customer), handler)
    result = resolver(None, query=None)
    assert result == []
