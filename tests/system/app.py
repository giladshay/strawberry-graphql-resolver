from __future__ import annotations

from typing import Any, cast

import strawberry
from fastapi import FastAPI
from pydantic import AnyUrl, BaseModel, PositiveInt, field_serializer, field_validator
from strawberry.fastapi import GraphQLRouter

from strawberry_graphql_resolver import DBType, MongoDBQuery, SQLQuery, resolve_query
from strawberry_graphql_resolver.resolvers.pydantic_types import create_pydantic_types


class Location(BaseModel):
    city: str
    website: AnyUrl


class Customer(BaseModel):
    id: int
    name: str
    age: PositiveInt
    location: Location

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @field_serializer("name")
    def serialize_name(self, value: str) -> str:
        return value.upper()


def create_app(backend: Any) -> FastAPI:
    _, location_type = create_pydantic_types(Location)
    if backend.db_type is DBType.SQL:

        @strawberry.type
        class Query:
            @resolve_query(db=DBType.SQL)
            def customers(self, query: SQLQuery) -> list[Customer]:
                return cast(list[Customer], backend.query(query))

    else:

        @strawberry.type
        class Query:
            @resolve_query(db=DBType.MONGO_DB)
            def customers(self, query: MongoDBQuery) -> list[Customer]:
                return cast(list[Customer], backend.query(query))

    app = FastAPI()
    app.include_router(
        GraphQLRouter(strawberry.Schema(query=Query, types=[location_type])),
        prefix="/graphql",
    )
    return app
