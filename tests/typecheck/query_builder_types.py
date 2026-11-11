"""Static typing checks for model field-name completion.

This module is checked by ``ty`` but is not collected by pytest.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, Self, assert_type, override

from strawberry_graphql_resolver import Queryable, QueryExpression


class User(Queryable):
    name: str
    age: int
    mail: str

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        raise NotImplementedError


class Admin(User):
    role: str

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        raise NotImplementedError


class Wide(Queryable):
    a: int
    b: str
    c: float
    d: bool
    e: int

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        raise NotImplementedError


# Unconfigured models still accept any string and any field handle.
class Unconfigured(Queryable):
    name: str

    @override
    @classmethod
    def submit(cls, query: QueryExpression) -> Sequence[Self]:
        raise NotImplementedError


# Single-field selections preserve the field's value type.
assert_type(User.only(User.name).submit(), Sequence[str])
assert_type(User.only(User.age).submit(), Sequence[int])
assert_type(User.only(User.mail).submit(), Sequence[str])
assert_type(User.only("name").submit(), Sequence[Literal["name"]])

# Two-field selections produce tuples.
assert_type(
    User.only(User.name, User.age).submit(),
    Sequence[tuple[str, int]],
)

# Chaining preserves the selected value type.
assert_type(
    User.where(User.age >= 18).only(User.mail).submit(),
    Sequence[str],
)

# No selection and empty selections return models.
assert_type(User.where(User.age >= 18).submit(), Sequence[User])
assert_type(User.exclude().submit(), Sequence[User])

# exclude() cannot know the number of remaining fields statically.
assert_type(User.exclude(User.age).submit(), Sequence[Any])

# Inherited fields are usable as handles.
assert_type(Admin.only(Admin.role).submit(), Sequence[str])
assert_type(Admin.only(Admin.name, Admin.mail).submit(), Sequence[tuple[str, str]])

# Variadic generics support any number of fields, not just two or three.
assert_type(
    Wide.only(Wide.a, Wide.b, Wide.c, Wide.d, Wide.e).submit(),
    Sequence[tuple[int, str, float, bool, int]],
)

# Unconfigured models accept strings and handles.
Unconfigured.only("anything")
Unconfigured.only(Unconfigured.name)

# Typos in field handles are rejected.
User.only(User.nope)  # ty: ignore[unresolved-attribute]
