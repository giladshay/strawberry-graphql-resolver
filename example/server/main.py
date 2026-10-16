from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import strawberry
from client.product import Product
from client.user import User
from fastapi import FastAPI
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from pymssql import connect
from strawberry.fastapi import GraphQLRouter

from strawberry_graphql_resolver import DBType, MongoDBQuery, SQLQuery, resolve_query


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    sql_database = connect(
        server=os.environ.get("SQLSERVER_HOST", "localhost"),
        port=os.environ.get("SQLSERVER_PORT", "1433"),
        user=os.environ.get("SQLSERVER_USER", "sa"),
        password=os.environ.get("SQLSERVER_PASSWORD", "Strawberry!SqlServer2026"),
        database=os.environ.get("SQLSERVER_DATABASE", "master"),
        login_timeout=5,
        timeout=5,
    )
    sql_database.autocommit(True)
    with sql_database.cursor() as cursor:
        cursor.execute(
            """
            IF DB_ID(N'strawberry_resolver') IS NULL
                CREATE DATABASE strawberry_resolver
            """
        )
    sql_database.close()
    sql_database = connect(
        server=os.environ.get("SQLSERVER_HOST", "localhost"),
        port=os.environ.get("SQLSERVER_PORT", "1433"),
        user=os.environ.get("SQLSERVER_USER", "sa"),
        password=os.environ.get("SQLSERVER_PASSWORD", "Strawberry!SqlServer2026"),
        database=os.environ.get("SQLSERVER_DATABASE", "strawberry_resolver"),
        login_timeout=5,
        timeout=5,
    )
    sql_database.autocommit(True)
    with sql_database.cursor() as cursor:
        cursor.execute(
            """
            IF OBJECT_ID(N'users', N'U') IS NULL
                CREATE TABLE users (name NVARCHAR(255) NOT NULL, age INT NOT NULL);
            IF OBJECT_ID(N'products', N'U') IS NULL
                CREATE TABLE products (name NVARCHAR(255) NOT NULL, price INT NOT NULL);
            IF NOT EXISTS (SELECT 1 FROM users)
                INSERT INTO users VALUES (N'John', 30), (N'Jane', 20);
            IF NOT EXISTS (SELECT 1 FROM products)
                INSERT INTO products VALUES (N'Keyboard', 80), (N'Monitor', 240);
            """
        )

    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    try:
        mongo_client.admin.command("ping")
    except ServerSelectionTimeoutError as error:
        mongo_client.close()
        raise RuntimeError(
            f"MongoDB is unavailable at {mongo_uri}. Start MongoDB with "
            "`docker compose up -d mongo` or set MONGODB_URI to a reachable server."
        ) from error

    mongo_database = mongo_client["strawberry_resolver"]
    users = mongo_database["users"]
    products = mongo_database["products"]
    if users.count_documents({}) == 0:
        users.insert_many([{"name": "John", "age": 30}, {"name": "Jane", "age": 20}])
    if products.count_documents({}) == 0:
        products.insert_many(
            [{"name": "Keyboard", "price": 80}, {"name": "Monitor", "price": 240}]
        )

    application.state.sql_database = sql_database
    application.state.mongo_database = mongo_database
    try:
        yield
    finally:
        sql_database.close()
        mongo_client.close()


@strawberry.type
class Query:
    @resolve_query(db=DBType.SQL)
    def users(self, query: SQLQuery) -> list[User]:
        with app.state.sql_database.cursor(as_dict=True) as cursor:
            cursor.execute(query.statement, query.parameters)
            rows = cursor.fetchall()
        return [User.model_validate(dict(row)) for row in rows]

    @resolve_query(db=DBType.MONGO_DB)
    def products(self, query: MongoDBQuery) -> list[Product]:
        documents = app.state.mongo_database["products"].find(query.filters)
        if query.sorts:
            documents = documents.sort(query.sorts)
        return [Product.model_validate(document) for document in documents]


schema = strawberry.Schema(query=Query)
app = FastAPI(lifespan=lifespan)
app.include_router(GraphQLRouter(schema), prefix="/graphql")
