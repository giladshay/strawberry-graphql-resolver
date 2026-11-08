from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Self, override
from urllib.request import Request, urlopen

from strawberry_graphql_resolver import Queryable, QueryExpression


class User(Queryable):
    name: str
    age: int

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        query._query_input_name = f"{cls.__name__}Input"
        query.schema_name = f"{cls.__name__.lower()}s"
        graphql_query, variables = query.to_graphql()
        request = Request(
            "http://127.0.0.1:8000/graphql",
            data=json.dumps({"query": graphql_query, "variables": variables}).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            result = json.load(response)
        return query.parse_result(cls, result)  # type: ignore[return-value]


if __name__ == "__main__":
    print(User.where(User.name == "John").submit())
    print(User.sort(+User.age).submit())
    print(User.where(User.name == "John").only(User.name).submit())
    print(User.where(User.name == "John").only(User.name, User.age).submit())
