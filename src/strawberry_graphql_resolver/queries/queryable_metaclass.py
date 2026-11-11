from __future__ import annotations

from typing import Any

from pydantic._internal._model_construction import ModelMetaclass

from strawberry_graphql_resolver.queries.field_mapper import FieldMapper


class QueryableMetaclass(ModelMetaclass):
    """Expose every model field as a query handle at class level.

    A :class:`FieldMapper` is installed as a plain class attribute for each
    model field. Class-level access (``User.name``) therefore returns the
    handle, while instance access still returns the stored value, because an
    instance's ``__dict__`` takes precedence over a non-descriptor class
    attribute. Unknown attributes are not provided, so typos such as
    ``User.mial`` are rejected by type checkers.
    """

    def __new__(
        mcls, name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any]
    ) -> type:
        cls = super().__new__(mcls, name, bases, namespace)
        try:
            fields = type.__getattribute__(cls, "model_fields")
        except Exception:  # noqa: BLE001
            fields = {}
        for field_name in fields or {}:
            setattr(cls, field_name, FieldMapper(name=field_name))
        return cls
