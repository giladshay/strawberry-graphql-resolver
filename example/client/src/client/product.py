from __future__ import annotations

from collections.abc import Sequence
from typing import Self, override

from client._request import submit_query
from strawberry_graphql_resolver import Queryable, QueryExpression


class Product(Queryable):
    name: str
    price: int

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        return submit_query(cls, query)


if __name__ == "__main__":
    print(Product.where(Product.name == "Keyboard").submit())
