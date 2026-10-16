# Database compilers

The compiler layer converts one `QueryExpression` into a backend-specific
value object.

```python
from strawberry_graphql_resolver import compile_mongo, compile_sql

sql_query = compile_sql(expression)
mongo_query = compile_mongo(expression)
```

`SQLQuery` contains:

- `statement`: SQL text with `%s` placeholders.
- `parameters`: values supplied separately to the DB driver.
- `filters` and `sorts`: structured representations useful to repositories.

`MongoDBQuery` contains a PyMongo-compatible `filters` dictionary and `sorts`
list. Empty sort lists should not be passed to `Cursor.sort()`.

!!! warning
    SQL identifiers come from the query expression and are interpolated into
    the statement. Only use model-derived, controlled field and table names;
    values remain parameterized.
