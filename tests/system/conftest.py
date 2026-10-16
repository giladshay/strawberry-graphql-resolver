from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, Protocol, cast

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.collection import Collection
from pymssql import Connection, connect

# sourcery skip: dont-import-test-modules
from testcontainers.community.mongodb import MongoDbContainer
from testcontainers.community.mssql import SqlServerContainer

from strawberry_graphql_resolver import DBType, MongoDBQuery, SQLQuery

from .app import Customer, create_app


class Backend(Protocol):
    name: str
    db_type: DBType

    def query(self, query: SQLQuery | MongoDBQuery) -> list[Customer]: ...

    def close(self) -> None: ...


@dataclass
class SqlBackend:
    connection: Connection
    name: str = "sql"
    db_type: DBType = DBType.SQL

    def query(self, query: SQLQuery | MongoDBQuery) -> list[Customer]:
        assert isinstance(query, SQLQuery)
        with self.connection.cursor(as_dict=True) as cursor:
            cursor.execute(query.statement, query.parameters)
            rows = cursor.fetchall()
        return [
            Customer.model_validate(
                {**row, "location": json.loads(str(row["location"]))}
            )
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()


@dataclass
class MongoBackend:
    client: MongoClient[dict[str, Any]]
    collection: Collection[dict[str, Any]]
    name: str = "mongo"
    db_type: DBType = DBType.MONGO_DB

    def query(self, query: SQLQuery | MongoDBQuery) -> list[Customer]:
        assert isinstance(query, MongoDBQuery)
        documents = self.collection.find(query.filters)
        if query.sorts:
            documents = documents.sort(query.sorts)
        return [Customer.model_validate(document) for document in documents]

    def close(self) -> None:
        self.client.close()


@dataclass(frozen=True)
class BackendSpec:
    name: str
    db_type: DBType
    create: Callable[[], tuple[Any, Backend]]


def _docker_available() -> bool:
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=5)
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        return False
    return True


def _seed_sql(container: SqlServerContainer) -> SqlBackend:
    connection = connect(
        server=container.get_container_host_ip(),
        port=str(container.get_exposed_port(1433)),
        user="sa",
        password="Strawberry!SqlServer2026",
        database="master",
        login_timeout=10,
        timeout=10,
    )
    connection.autocommit(True)
    with connection.cursor() as cursor:
        cursor.execute(
            "IF OBJECT_ID(N'customers', N'U') IS NOT NULL DROP TABLE customers"
        )
        cursor.execute(
            """
            CREATE TABLE customers (
                id INT NOT NULL PRIMARY KEY,
                name NVARCHAR(255) NOT NULL,
                age INT NOT NULL,
                location NVARCHAR(MAX) NOT NULL
            )
            """
        )
        for customer in _customers():
            cursor.execute(
                "INSERT INTO customers (id, name, age, location) VALUES (%s, %s, %s, %s)",
                (
                    customer.id,
                    customer.model_dump(mode="json")["name"],
                    customer.age,
                    json.dumps(customer.location.model_dump(mode="json")),
                ),
            )
    return SqlBackend(connection)


def _seed_mongo(container: MongoDbContainer) -> MongoBackend:
    client = MongoClient(container.get_connection_url())
    collection = client["resolver_tests"]["customers"]
    collection.drop()
    collection.insert_many(
        [customer.model_dump(mode="json") for customer in _customers()]
    )
    return MongoBackend(client, collection)


def _customers() -> list[Customer]:
    return [
        Customer(
            id=1,
            name=" Ada ",
            age=37,
            location={"city": "London", "website": "https://ada.example"},
        ),
        Customer(
            id=2,
            name="Grace",
            age=28,
            location={"city": "New York", "website": "https://grace.example"},
        ),
        Customer(
            id=3,
            name="Linus",
            age=18,
            location={"city": "Helsinki", "website": "https://linus.example"},
        ),
    ]


def _create_sql() -> tuple[SqlServerContainer, Backend]:
    container = SqlServerContainer(
        "mcr.microsoft.com/mssql/server:2022-latest",
        password="Strawberry!SqlServer2026",
    )
    container.start()
    return container, _seed_sql(container)


def _create_mongo() -> tuple[MongoDbContainer, Backend]:
    container = MongoDbContainer("mongo:8.0")
    container.start()
    return container, _seed_mongo(container)


BACKENDS = [
    BackendSpec("sql", DBType.SQL, _create_sql),
    BackendSpec("mongo", DBType.MONGO_DB, _create_mongo),
]


@pytest.fixture(scope="module", params=BACKENDS, ids=lambda spec: spec.name)
def backend(request: pytest.FixtureRequest) -> Iterator[Backend]:
    if not _docker_available():
        pytest.xfail()
    spec = cast(BackendSpec, request.param)
    container, backend = spec.create()
    try:
        yield backend
    finally:
        backend.close()
        container.stop()


@pytest.fixture
def graphql_client(backend: Backend) -> Iterator[Any]:
    with TestClient(create_app(backend)) as client:
        yield client
