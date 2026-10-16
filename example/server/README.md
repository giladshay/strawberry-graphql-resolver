Start MongoDB and SQL Server before running the server:

```sh
docker compose up -d mongo sqlserver
```

The server uses `mongodb://localhost:27017` by default. Set `MONGODB_URI` to
override the connection string:

```sh
MONGODB_URI="mongodb://localhost:27017" uv run uvicorn main:app
```

The SQL Server defaults are `sa` / `Strawberry!SqlServer2026` on
`localhost:1433`. Override them with `SQLSERVER_HOST`, `SQLSERVER_PORT`,
`SQLSERVER_USER`, `SQLSERVER_PASSWORD`, and `SQLSERVER_DATABASE`.
