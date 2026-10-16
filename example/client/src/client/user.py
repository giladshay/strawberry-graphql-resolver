from __future__ import annotations

from collections.abc import Sequence
from typing import Self, override

from client._request import submit_query
from strawberry_graphql_resolver import Queryable, QueryExpression


class User(Queryable):
    name: str
    age: int

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        return submit_query(cls, query)


if __name__ == "__main__":
    print(User.where(User.name == "John").submit())
    print(User.sort(+User.age).submit())
