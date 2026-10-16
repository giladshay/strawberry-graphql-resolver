from __future__ import annotations

import contextlib

from pydantic._internal._model_construction import ModelMetaclass

from strawberry_graphql_resolver.queries.field_mapper import FieldMapper


class QueryableMetaclass(ModelMetaclass):
    def __getattr__(self, name: str) -> FieldMapper:
        if name.startswith("_"):
            raise AttributeError(f"'{self.__name__}' object has no attribute '{name}'")

        with contextlib.suppress(AttributeError):
            fields = object.__getattribute__(self, "__annotations__")
            if name in fields:
                return FieldMapper(name=name)
        raise AttributeError(f"'{self.__name__}' object has no attribute '{name}'")
