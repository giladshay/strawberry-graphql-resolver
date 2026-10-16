# Installation

The project uses [uv](https://docs.astral.sh/uv/) and requires Python 3.12 or
newer.

```shell
git clone https://github.com/giladshay/strawberry-graphql-resolver.git
cd strawberry-graphql-resolver
uv sync --all-packages --all-groups
```

The command installs the library, examples, lint tools, tests, and docs.

!!! note
    Runtime dependencies are declared in the workspace packages. The `docs`
    dependency group contains MkDocs and Sphinx tooling without adding those
    packages to the runtime library.
