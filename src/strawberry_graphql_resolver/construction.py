from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any, get_args, get_origin

from pydantic import BaseModel


def _target_type(annotation: Any) -> type | None:
    """Return the (possibly nested) BaseModel target of *annotation*, if any."""
    origin = get_origin(annotation)
    if origin is None:
        return annotation if isinstance(annotation, type) else None
    args = get_args(annotation)
    if origin in (list, tuple, set, frozenset):
        if args:
            return _target_type(args[0])
        return None
    non_none = [arg for arg in args if arg is not type(None)]
    if len(non_none) == 1:
        return _target_type(non_none[0])
    return None


def _coerce_value(model_type: type[BaseModel], field_name: str, value: Any) -> Any:
    """Parse JSON strings into objects for nested ``BaseModel`` fields."""
    if not isinstance(value, str):
        return value
    field_info = model_type.model_fields.get(field_name)
    if field_info is None:
        return value
    target = _target_type(field_info.annotation)
    if not (isinstance(target, type) and issubclass(target, BaseModel)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return value


def construct_model[TModel: BaseModel](
    model_type: type[TModel], data: Mapping[str, Any]
) -> TModel:  # type: ignore[misc]
    """Build a *model_type* instance from a (possibly partial) result row.

    Nested JSON strings are coerced into objects for ``BaseModel`` fields, so
    SQL rows storing a nested model as JSON are handled automatically. When all
    required fields are present the row is validated with ``model_validate``;
    otherwise ``model_construct`` is used so partial selections (``only`` /
    ``exclude``) do not fail validation.
    """
    coerced: dict[str, Any] = {
        key: _coerce_value(model_type, key, value) for key, value in data.items()
    }
    required = {
        name
        for name, field_info in model_type.model_fields.items()
        if field_info.is_required()
    }
    if required.issubset(coerced):
        return model_type.model_validate(coerced)  # type: ignore[return-value]
    return model_type.model_construct(**coerced)  # type: ignore[return-value]


def construct_models[TModel: BaseModel](
    model_type: type[TModel], rows: Iterable[Mapping[str, Any]]
) -> list[TModel]:  # type: ignore[misc]
    """Build a list of *model_type* instances from (possibly partial) rows."""
    return [construct_model(model_type, row) for row in rows]
