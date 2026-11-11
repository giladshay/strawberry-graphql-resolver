from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr

from strawberry_graphql_resolver.queries.expressions.base import BaseQueryExpression
from strawberry_graphql_resolver.queries.expressions.filter import QueryFilterExpression
from strawberry_graphql_resolver.queries.expressions.sort import QuerySortExpression


class QueryExpression(BaseQueryExpression):
    """Represent the complete query sent to a GraphQL resolver."""

    _query_input_name: str = PrivateAttr(default="QueryInput")
    schema_name: str
    field_names: list[str] = Field(default_factory=list)
    filters: list[QueryFilterExpression] = Field(default_factory=list)
    sorts: list[QuerySortExpression] = Field(default_factory=list)

    def parse_result[ModelT: BaseModel](
        self, model_type: type[ModelT], result: dict[str, Any]
    ) -> Sequence[ModelT]:
        """Parse a GraphQL JSON *result* into model instances.

        Handles partial selections (``only`` / ``exclude``) automatically.
        The HTTP request itself is the caller's responsibility; this helper
        only interprets the already-received response.
        """
        from strawberry_graphql_resolver.results import parse_graphql_result

        return parse_graphql_result(model_type, self, result)

    def to_graphql(self) -> tuple[str, dict[str, Any]]:
        """Return a GraphQL document and variables payload for this query."""
        filters = self._to_graphql_filters()
        sorts = self._to_graphql_sorts()
        query_input: dict[str, Any] = {}
        if filters:
            query_input["filters"] = filters
        if sorts:
            query_input["sorts"] = sorts
        graphql_query = (
            f"query FetchData($query: {self._query_input_name}!) {{\n"
            f"  {self.schema_name}(query: $query) {{\n"
            + "\n".join(f"    {field_name}" for field_name in self.field_names)
            + "\n  }\n}"
        )

        return graphql_query, {"query": query_input}

    def _to_graphql_filters(self) -> dict[str, dict[str, Any]]:
        filters: dict[str, dict[str, Any]] = {}
        for filter in self.filters:
            filters.setdefault(filter.name, {})[filter.operator.name] = filter.value
        return filters

    def _to_graphql_sorts(self) -> dict[str, str]:
        sorts: dict[str, str] = {sort.name: sort.order.name for sort in self.sorts}
        return sorts
