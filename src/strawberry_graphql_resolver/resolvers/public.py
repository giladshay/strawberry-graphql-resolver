from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import cast, get_args, get_type_hints

import strawberry
from pydantic import BaseModel
from strawberry.experimental.pydantic.conversion_types import (
    StrawberryTypeFromPydantic,
)
from strawberry.types.field import StrawberryField

from strawberry_graphql_resolver.compilers import DBType
from strawberry_graphql_resolver.queries import Queryable, QueryExpression
from strawberry_graphql_resolver.resolvers.query_resolver import create_query_resolver


def resolve_query(
    query_handler: Callable[..., Sequence[BaseModel]] | None = None,
    *,
    db: DBType | str | None = None,
) -> StrawberryField | Callable[[Callable[..., Sequence[BaseModel]]], StrawberryField]:
    if query_handler is None:
        return cast(
            Callable[[Callable[..., Sequence[BaseModel]]], StrawberryField],
            lambda handler: resolve_query(handler, db=db),
        )

    database = DBType(db) if db is not None else None
    if isinstance(query_handler, staticmethod):
        query_handler = query_handler.__func__
    annotations = get_type_hints(query_handler)
    return_type = annotations["return"]
    model_type: type[BaseModel]
    owner = getattr(query_handler, "__self__", None)
    if isinstance(owner, type) and issubclass(owner, BaseModel):
        model_type = owner
    else:
        return_args = get_args(return_type)
        model_type = cast(type[BaseModel], return_args[0])
    resolver = create_query_resolver(model_type, query_handler, database)
    field_value = strawberry.field(resolver=resolver, init=False)
    return cast(StrawberryField, cast(object, field_value))


def flattened_pydantic_resolver(
    model_type: type[Queryable],
    query_handler: Callable[[QueryExpression], Sequence[BaseModel]] | None = None,
) -> Callable[..., list[StrawberryTypeFromPydantic[BaseModel]]]:
    handler = query_handler if query_handler is not None else model_type.submit
    return create_query_resolver(model_type, handler)
