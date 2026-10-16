# Quick start

## Build a query

```python
from collections.abc import Sequence
from typing import Self, override

from strawberry_graphql_resolver import Queryable, QueryExpression


class User(Queryable):
    name: str
    age: int

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        return repository.fetch(query)


adults = User.where(User.age >= 18).sort(+User.name).submit()
```

The unary `+` operator means ascending order; unary `-` means descending.

## Generate a resolver

```python
from strawberry_graphql_resolver import DBType, SQLQuery, resolve_query


@resolve_query(db=DBType.SQL)
def users(self, query: SQLQuery) -> list[User]:
    return repository.fetch(query)
```

Use `DBType.MONGO_DB` for a `MongoDBQuery`, or `DBType.NONE` to receive the
original `QueryExpression`.
