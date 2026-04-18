from __future__ import annotations

from sqlalchemy import Engine, create_engine


class EngineFactory:
    """Fabrica de engines SQLAlchemy contra MariaDB."""

    @staticmethod
    def mariadb(url: str) -> Engine:
        return create_engine(url, pool_pre_ping=True, future=True)
