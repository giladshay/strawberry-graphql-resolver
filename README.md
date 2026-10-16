# Strawberry GraphQL Resolver

[![CI](https://img.shields.io/github/actions/workflow/status/giladshay/strawberry-graphql-resolver/docs.yml?label=docs%20%26%20quality)](https://github.com/giladshay/strawberry-graphql-resolver/actions)
[![Coverage](https://codecov.io/gh/giladshay/strawberry-graphql-resolver/branch/mvp/graph/badge.svg)](https://codecov.io/gh/giladshay/strawberry-graphql-resolver)
[![Python](https://img.shields.io/badge/python-%3E%3D3.12-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063)](https://docs.pydantic.dev/)
[![GraphQL](https://img.shields.io/badge/GraphQL-Strawberry-e10098)](https://strawberry.rocks/)
[![Docs](https://img.shields.io/badge/docs-MkDocs%20Material-526cfe?logo=materialformkdocs&logoColor=white)](https://giladshay.github.io/strawberry-graphql-resolver/)

Typed query builders and generated Strawberry GraphQL resolvers for Pydantic
models.

Strawberry GraphQL Resolver lets clients compose filters and sorting with
ordinary Python operators while servers choose whether handlers receive the
original GraphQL expression, parameterized SQL, or a MongoDB query.

## Highlights

- **Pydantic-first** model definitions.
- Fluent, typed query composition with all six comparison operators.
- Automatic Strawberry input and output type generation.
- SQL Server and MongoDB compiler support.
- `DBType.NONE` for custom repositories and additional backends.
- Nested Pydantic output models, constrained types, validators, and serializers.
- Strict Ruff and `ty` checks with unit and real-database system tests.

## Installation

```shell
git clone https://github.com/giladshay/strawberry-graphql-resolver.git
cd strawberry-graphql-resolver
uv sync --all-packages --all-groups
```

The library requires Python 3.12 or newer. See the
[full installation guide](https://giladshay.github.io/strawberry-graphql-resolver/guide/installation/).

## Quick start

Define a queryable model:

```python
from collections.abc import Sequence
from typing import Self, override

from strawberry_graphql_resolver import QueryExpression, Queryable


class User(Queryable):
    name: str
    age: int

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        return repository.fetch(query)


adults = User.where(User.age >= 18).sort(-User.age).submit()
```

Build a GraphQL resolver:

```python
from strawberry_graphql_resolver import DBType, SQLQuery, resolve_query


@resolve_query(db=DBType.SQL)
def users(self, query: SQLQuery) -> list[User]:
    with sql_connection.cursor(as_dict=True) as cursor:
        cursor.execute(query.statement, query.parameters)
        return [User.model_validate(row) for row in cursor.fetchall()]
```

For MongoDB, use `@resolve_query(db=DBType.MONGO_DB)` and
`MongoDBQuery`. For a custom repository, use `DBType.NONE` to receive the
original `QueryExpression`.

## Query operators

```python
User.age == 18  # EQ
User.age != 18  # NEQ
User.age < 18  # LT
User.age <= 18  # LTE
User.age > 18  # GT
User.age >= 18  # GTE

+User.age  # ascending
-User.age  # descending
```

See the [query builder guide](https://giladshay.github.io/strawberry-graphql-resolver/guide/query-builders/)
for composition patterns and edge cases.

## Testing

```shell
uv run pytest tests/unit
uv run pytest
uv run pre-commit run --all-files
```

The complete suite includes Testcontainers-backed tests against real SQL Server
and MongoDB instances, so Docker must be running for `uv run pytest` to execute
the system tests.

## Documentation

- **User documentation:** [strawberry-graphql-resolver docs](https://giladshay.github.io/strawberry-graphql-resolver/)
- **Developer guide:** [docs/developers.md](docs/developers.md)
- **API reference:** [generated API docs](https://giladshay.github.io/strawberry-graphql-resolver/api/)

Build documentation locally:

```shell
uv run mkdocs serve
uv run sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html
```

## Repository layout

```text
src/strawberry_graphql_resolver/  library source
tests/unit/                       fast unit tests
tests/system/                     parameterized database tests
example/client/                   example query client
example/server/                   FastAPI and Strawberry example server
docs/                             MkDocs and Sphinx documentation
compose.yaml                      local MongoDB and SQL Server services
```

## Contributing

Read the [developer guide](docs/developers.md) before making changes. New
public behavior should include typed implementation, parameterized tests,
documentation, and docstrings. Pull requests should pass the repository
pre-commit hooks.

## Releases

Maintainers manually run **Create release tag** in GitHub Actions. The
workflow derives the tag from `pyproject.toml`: a normal `0.2.0` version
becomes `v0.2.0`, while a beta version ending in `b` increments tags as
`v0.2.0b0`, `v0.2.0b1`, and so on.

The `Release` workflow builds the package and documentation for `v*` tags.
PyPI and GitHub Pages publication are protected by GitHub Environment approval
gates and use PyPI Trusted Publishing through OIDC. See the
[developer release guide](docs/developers.md#release-process) for maintainer
setup.

## License

See the repository for licensing information.
