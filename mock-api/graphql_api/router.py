from __future__ import annotations

import strawberry
from strawberry.fastapi import GraphQLRouter

from .query import Query

schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema)
