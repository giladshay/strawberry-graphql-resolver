from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel

from strawberry_graphql_resolver.construction import construct_model
from strawberry_graphql_resolver.queries import QueryExpression


def parse_graphql_result[ModelT: BaseModel](
    model_type: type[ModelT],
    query: QueryExpression,
    result: dict[str, Any],
) -> Sequence[ModelT]:
    """Parse a GraphQL response into model instances.

    Handles partial selections (``only`` / ``exclude``) automatically via
    :func:`construct_model`. The HTTP request itself is the caller's
    responsibility; this helper only interprets the JSON response.
    """
    if result.get("errors"):
        raise RuntimeError(f"GraphQL request failed: {result['errors']}")
    items = result["data"][query.schema_name]
    return [construct_model(model_type, item) for item in items]  # type: ignore[return-value]


def parse_result[ModelT: BaseModel](
    model_type: type[ModelT],
    query: QueryExpression,
    result: dict[str, Any],
) -> Sequence[ModelT]:
    """Alias for :func:`parse_graphql_result`."""
    return parse_graphql_result(model_type, query, result)
