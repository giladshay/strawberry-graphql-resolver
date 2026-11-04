from __future__ import annotations

import operator
from collections.abc import Iterator
from functools import reduce
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

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


def _replace_recursive_model(
    annotation: Any,
    model_type: type[BaseModel],
    replacement: type[Any],
) -> Any:
    if annotation is model_type:
        return replacement

    origin = get_origin(annotation)
    arguments = get_args(annotation)
    if not origin or not arguments:
        return annotation

    replaced_arguments = tuple(
        _replace_recursive_model(argument, model_type, replacement)
        for argument in arguments
    )
    if replaced_arguments == arguments:
        return annotation
    if origin in (Union, UnionType):
        return reduce(operator.or_, replaced_arguments)
    return origin[
        replaced_arguments[0] if len(replaced_arguments) == 1 else replaced_arguments
    ]


def _recursive_annotations(
    model_type: type[BaseModel], replacement: type[Any]
) -> dict[str, Any]:
    annotations = {}
    for field_name, annotation in get_type_hints(model_type).items():
        replaced = _replace_recursive_model(annotation, model_type, replacement)
        if replaced is not annotation:
            annotations[field_name] = replaced
    return annotations


def create_pydantic_types(
    model_type: type[BaseModel],
) -> tuple[
    type[StrawberryTypeFromPydantic[BaseModel]],
    type[StrawberryTypeFromPydantic[BaseModel]],
]:
    """Generate recursive Strawberry input/output types for a Pydantic model."""
    if model_type in _input_types:
        return _input_types[model_type], _output_types[model_type]

    for nested_model in _nested_models(model_type):
        if nested_model is model_type:
            continue
        create_pydantic_types(nested_model)

    type_name = model_type.__name__.removesuffix("Model")
    output_placeholder = type(f"{type_name}Type", (), {"__module__": __name__})
    output_placeholder.__annotations__ = _recursive_annotations(
        model_type, output_placeholder
    )
    input_placeholder = type(f"{type_name}Input", (), {"__module__": __name__})
    input_placeholder.__annotations__ = _recursive_annotations(
        model_type, input_placeholder
    )
    output_type = strawberry.experimental.pydantic.type(
        model=model_type, all_fields=True
    )(output_placeholder)
    input_type = strawberry.experimental.pydantic.input(
        model=model_type, all_fields=True
    )(input_placeholder)
    _output_types[model_type] = output_type
    _input_types[model_type] = input_type
    return input_type, output_type
