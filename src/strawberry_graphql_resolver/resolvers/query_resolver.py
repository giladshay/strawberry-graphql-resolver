from __future__ import annotations

import inspect
import types
from collections.abc import Callable, Sequence
from dataclasses import field
from typing import Any, cast, get_type_hints

import strawberry
from pydantic import BaseModel
from strawberry.experimental.pydantic.conversion_types import (
    StrawberryTypeFromPydantic,
)

from strawberry_graphql_resolver.compilers import (
    DBType,
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
from strawberry_graphql_resolver.resolvers.input_values import (
    input_values,
    operator_values,
)
from strawberry_graphql_resolver.resolvers.pydantic_types import (
    create_pydantic_types,
)


def create_query_resolver(
    model_type: type[BaseModel],
    query_handler: Callable[[Any], Sequence[BaseModel]],
    db: DBType | None = None,
) -> Callable[..., list[StrawberryTypeFromPydantic[BaseModel]]]:
    _, output_type = create_pydantic_types(model_type)
    field_types = get_type_hints(model_type)
    handler_parameters = tuple(inspect.signature(query_handler).parameters)
    handler = cast(Any, query_handler)

    def create_input_type(name: str, annotations: dict[str, Any]) -> type[Any]:
        namespace = {field_name: field(default=None) for field_name in annotations}
        namespace["__annotations__"] = annotations
        return strawberry.input(type(name, (), namespace))

    filter_types = {
        field_name: create_input_type(
            f"{model_type.__name__}{field_name.title()}Filter",
            {
                operator_name: field_type | None
                for operator_name in Comparison.__members__
            },
        )
        for field_name, field_type in field_types.items()
    }
    filters_type = create_input_type(
        f"{model_type.__name__}Filters",
        {
            field_name: field_type | None
            for field_name, field_type in filter_types.items()
        },
    )
    sorts_type = create_input_type(
        f"{model_type.__name__}Sorts",
        {field_name: SortOrder | None for field_name in field_types},
    )
    query_type = strawberry.input(
        type(
            f"{model_type.__name__}Query",
            (),
            {
                "filters": None,
                "sorts": None,
                "__annotations__": {
                    "filters": filters_type | None,
                    "sorts": sorts_type | None,
                },
            },
        ),
        name=f"{model_type.__name__}Input",
    )

    def resolver(
        self, query: Any = None
    ) -> list[StrawberryTypeFromPydantic[BaseModel]]:
        query_model = QueryExpression(
            schema_name=f"{model_type.__name__.lower()}s",
            field_names=list(field_types),
            filters=[
                QueryFilterExpression(name=field_name, operator=operator, value=value)
                for field_name, field_filter in input_values(query, "filters")
                for operator, value in operator_values(field_filter, Comparison)
            ],
            sorts=[
                QuerySortExpression(name=field_name, order=order)
                for field_name, order in input_values(query, "sorts")
                if order is not None
            ],
        )
        query_model._query_input_name = f"{model_type.__name__}Input"
        compiled_query: Any = query_model
        if db is DBType.MONGO_DB:
            compiled_query = compile_mongo(query_model)
        elif db is DBType.SQL:
            compiled_query = compile_sql(query_model)
        if len(handler_parameters) > 1:
            results = handler(self, compiled_query)
        else:
            results = handler(compiled_query)
        return [output_type.from_pydantic(item) for item in results]

    parameters = [
        inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        inspect.Parameter(
            "query",
            inspect.Parameter.KEYWORD_ONLY,
            annotation=query_type | None,
            default=None,
        ),
    ]
    signature_return_type: Any = types.GenericAlias(list, output_type)
    cast(Any, resolver).__signature__ = inspect.Signature(
        parameters, return_annotation=signature_return_type
    )
    return resolver
