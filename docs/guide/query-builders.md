# Query builders

`Queryable` exposes model fields dynamically through `FieldMapper`.

```python
query = User.where(
    User.age >= 18,
    User.name != "blocked",
).sort(-User.age, +User.name)
```

## Comparison operators

| Python expression | Meaning |
| --- | --- |
| `User.age == 18` | Equal |
| `User.age != 18` | Not equal |
| `User.age < 18` | Less than |
| `User.age <= 18` | Less than or equal |
| `User.age > 18` | Greater than |
| `User.age >= 18` | Greater than or equal |

Boolean values passed to `where` are ignored, which makes conditional query
composition convenient:

```python
query = User.where(include_adults and User.age >= 18)
```

Call `.submit()` to create a `QueryExpression` and invoke the model's
submission implementation.

## Selecting fields

Use `only` to include specific model fields, or `exclude` to remove them.
Refer to fields through the class itself, so editors complete field names and
unknown fields are caught at type-check time:

```python
names = User.where(User.age >= 18).only(User.name).submit()
rows = User.where(User.age >= 18).only(User.name, User.mail).submit()
without_age = User.exclude(User.age).submit()
```

Field-name strings such as `only("name")` remain supported, which is useful
when selections are built dynamically:

```python
names = User.where(User.age >= 18).only("name").submit()
```

`only` preserves the selected field's value type: `only(User.age)` produces a
`Sequence[int]`, while selecting several fields produces a sequence of
tuples in the given order.

`QueryBuilder` keeps the selection through `where`, `sort`, `only`, and
`exclude`, so chained calls are checked as well.

### Inherited and defaulted fields

Fields inherited from another `Queryable` model and fields with defaults are
exposed the same way:

```python
class Base(Queryable):
    name: str
    age: int


class Admin(Base):
    role: str = "admin"


Admin.only(Admin.name)  # ok
Admin.only(Admin.role)  # ok, defaults are supported
Admin.only(Admin.missing)  # type error
```

### At runtime

At runtime the names are used as provided. Field handles and strings may be
mixed in the same call. Unknown string names are not silently ignored, and no
`ValueError` is raised; static type checking is responsible for catching them
before the query is submitted.

Selecting one field returns a sequence of values:

```python
["Ada", "Grace"]
```

Selecting multiple fields returns one tuple per result, in the requested order:

```python
users = User.where(User.age >= 18).only("name", "age").submit()
# [
#     ("Ada", 37),
#     ("Grace", 28),
# ]
```

The same rule applies to `exclude`. Excluding all but one field returns
values; excluding fields so that multiple remain returns tuples:

```python
names = User.exclude("age").submit()
```

Field selections can be combined and chained with filters and sorts:

```python
query = User.where(User.age >= 18).only("name", "age").exclude("age").sort(+User.name)
```
