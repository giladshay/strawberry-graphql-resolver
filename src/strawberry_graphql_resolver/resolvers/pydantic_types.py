from __future__ import annotations

from collections.abc import Iterator
from typing import Any, get_args, get_type_hints

import strawberry
from pydantic import BaseModel
from strawberry.experimental.pydantic.conversion_types import (
    StrawberryTypeFromPydantic,
)

_input_types: dict[type[Any], type[StrawberryTypeFromPydantic[BaseModel]]] = {}
_output_types: dict[type[Any], type[StrawberryTypeFromPydantic[BaseModel]]] = {}


def _nested_models(model_type: type[BaseModel]) -> Iterator[type[BaseModel]]:
    for annotation in get_type_hints(model_type).values():
        candidates = (
            (annotation, *get_args(annotation))
            if hasattr(annotation, "__origin__")
            else (annotation,)
        )
        yield from (
            candidate
            for candidate in candidates
            if isinstance(candidate, type)
            and issubclass(candidate, BaseModel)
            and hasattr(candidate, "model_fields")
        )


def create_pydantic_types(
    model_type: type[BaseModel],
) -> tuple[
    type[StrawberryTypeFromPydantic[BaseModel]],
    type[StrawberryTypeFromPydantic[BaseModel]],
]:
    if model_type in _input_types:
        return _input_types[model_type], _output_types[model_type]

    for nested_model in _nested_models(model_type):
        create_pydantic_types(nested_model)

    type_name = model_type.__name__.removesuffix("Model")
    output_type = strawberry.experimental.pydantic.type(
        model=model_type, all_fields=True
    )(type(f"{type_name}Type", (), {"__module__": __name__}))
    input_type = strawberry.experimental.pydantic.input(
        model=model_type, all_fields=True
    )(type(f"{type_name}Input", (), {"__module__": __name__}))
    _output_types[model_type] = output_type
    _input_types[model_type] = input_type
    return input_type, output_type
