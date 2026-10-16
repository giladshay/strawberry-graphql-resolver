# Developer guide

## Set up the workspace

```shell
uv sync --all-packages --all-groups
pre-commit install
```

The repository contains the library plus the standalone example client and
server under `example/`.

## Quality gates

Run the complete local checks:

```shell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pre-commit run --all-files
```

Keep changes typed. The project treats strict `ty` diagnostics as errors and
uses Ruff for linting and formatting.

## Adding query behavior

1. Add or update the typed expression/compiler implementation under `src/`.
2. Add parameterized unit tests for every operator and edge case.
3. Add backend-independent system coverage when behavior crosses GraphQL and a
   real database.
4. Keep compiler-specific setup in the parameterized backend fixture.

## Adding a database compiler

Implement a compiler value object and compiler function under
`src/strawberry_graphql_resolver/compilers/`, export it from the package, and
add a `DBType` member. Update `resolve_query` dispatch and add unit tests for
all comparison/sort combinations. Then add one backend specification to the
system-test fixture so shared tests exercise the new backend.

## Documentation workflow

Build the published site locally:

```shell
uv run mkdocs build --strict
uv run mkdocs serve
```

Build the Sphinx API documentation:

```shell
uv run sphinx-build -W -b html docs/sphinx docs/sphinx/_build/html
```

Public classes and functions should have Google-style docstrings with useful
parameters, return values, and behavior notes. API pages are generated from
those docstrings; do not duplicate signatures manually.

## Pull requests

- Use a clear, capitalized commit subject.
- Include focused tests and documentation for public behavior.
- Run pre-commit locally.
- Mention Docker requirements when changing system tests.
- Keep generated documentation output out of the repository.

## Release process

Release automation is split into four workflows:

1. **Code quality** and **Tests** run on every push and pull request.
2. **Create release tag** is manually dispatched from the Actions tab. It
   reads the version from the root `pyproject.toml`.
3. **Release** runs automatically for `v*` tags and validates the tag before
   building the package and both documentation sites.
4. PyPI and GitHub Pages publication pause at environment approval gates.

For a normal version such as `0.2.0`, the tag workflow creates `v0.2.0`.
For a beta version ending in `b`, such as `0.2.0b`, it scans existing tags and
creates `v0.2.0b0`, then `v0.2.0b1`, and so on.

Repository administrators must configure:

- A `pypi` GitHub Environment with required reviewers.
- A PyPI Trusted Publisher with owner `giladshay`, repository
   `strawberry-graphql-resolver`, workflow `release.yml`, and environment
   `pypi`.
- A `github-pages` Environment with required reviewers.
- GitHub Pages enabled under **Settings > Pages**, with **GitHub Actions**
   selected as the build and deployment source.

The release workflow never stores a PyPI token. Its `id-token: write`
permission is used by PyPI's OIDC Trusted Publishing. If a build fails, fix
the source and create a new version/tag; if publication is paused, approve or
rerun the individual environment job after checking the artifacts.
