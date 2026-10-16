# GraphQL resolvers

`resolve_query` creates a Strawberry field with a model-specific GraphQL input
type. The generated resolver parses filters and sorts before calling your
handler.

=== "SQL"

    ```python
    @resolve_query(db=DBType.SQL)
    def users(self, query: SQLQuery) -> list[User]:
        return sql_connection.execute(query.statement, query.parameters)
    ```

=== "MongoDB"

    ```python
    @resolve_query(db=DBType.MONGO_DB)
    def users(self, query: MongoDBQuery) -> list[User]:
        cursor = collection.find(query.filters)
        return list(cursor.sort(query.sorts)) if query.sorts else list(cursor)
    ```

=== "Original expression"

    ```python
    @resolve_query(db=DBType.NONE)
    def users(self, query: QueryExpression) -> list[User]:
        return repository.fetch(query)
    ```

Nested Pydantic models are generated as nested Strawberry output types. They
are returned as fields, but nested objects are not exposed as scalar filter
inputs.
