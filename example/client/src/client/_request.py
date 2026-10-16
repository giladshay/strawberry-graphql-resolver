from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from urllib.request import Request, urlopen

from strawberry_graphql_resolver import Queryable, QueryExpression


def submit_query[ModelT: Queryable](
    model_type: type[ModelT], query: QueryExpression
) -> Sequence[ModelT]:
    query._query_input_name = f"{model_type.__name__}Input"
    query.schema_name = f"{model_type.__name__.lower()}s"
    graphql_query, variables = query.to_graphql()
    request = Request(
        "http://127.0.0.1:8000/graphql",
        data=json.dumps({"query": graphql_query, "variables": variables}).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urlopen(request) as response:
        result: dict[str, Any] = json.load(response)

    if result.get("errors"):
        raise RuntimeError(f"GraphQL request failed: {result['errors']}")
    return [
        model_type.model_validate(item) for item in result["data"][query.schema_name]
    ]
