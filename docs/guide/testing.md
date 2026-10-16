# Testing

Run fast unit tests:

```shell
uv run pytest tests/unit
```

Run the complete suite:

```shell
uv run pytest
```

System tests use Testcontainers with real SQL Server and MongoDB instances, so
Docker must be running. The same parameterized backend tests run against both
databases.

```shell
uv run pytest tests/system
```

Before opening a pull request, run:

```shell
uv run pre-commit run --all-files
```

!!! example "Adding a backend"
    Add one typed backend specification to `tests/system/conftest.py`. Shared
    tests should remain backend-independent.
