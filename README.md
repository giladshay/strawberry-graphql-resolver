# strawberry-graphql-resolver

## Testing

Run the unit and database-backed system tests with:

```shell
uv run pytest
```

The system tests use a parameterized pytest backend fixture and run the same
GraphQL assertions against SQL Server and MongoDB in Testcontainers. Docker
must be running for those tests. Unit tests can be run without Docker:

```shell
uv run pytest tests/unit
```

The test-only GraphQL schema and HTTP client live under `tests/system`; they do
not import the example client or server schemas. To add another database
backend, add one typed backend specification to
`tests/system/conftest.py`; the shared system tests will run for it
automatically.
