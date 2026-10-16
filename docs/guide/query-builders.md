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
