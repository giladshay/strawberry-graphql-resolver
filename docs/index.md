# Typed GraphQL queries for Pydantic models

**Strawberry GraphQL Resolver** turns a Pydantic model into a fluent query
builder and a generated Strawberry GraphQL resolver.

!!! tip "The short version"
    Define a `Queryable` model, compose filters with normal Python operators,
    and submit it. On the server, decorate a handler with `resolve_query`.

=== "Client"

    ```python
    users = User.where(User.age >= 18).sort(-User.age).submit()
    ```

=== "Server"

    ```python
    @resolve_query(db=DBType.SQL)
    def users(self, query: SQLQuery) -> list[User]:
        return repository.fetch(query)
    ```

## Why this project?

- **Typed**: query fields are derived from Pydantic models.
- **Composable**: filters and sort expressions can be combined fluently.
- **GraphQL-native**: query expressions serialize to GraphQL documents and
  variables.
- **Backend-aware**: the same expression can compile to SQL Server or MongoDB.
- **Testable**: unit and Testcontainers-backed system tests are included.

Get started with the [installation guide](guide/installation.md), then explore
the [quick start](guide/quickstart.md).

## Project links

- [Developer guide](developers.md)
- [API reference](api/index.md)
- [GitHub repository](https://github.com/giladshay/strawberry-graphql-resolver)
