"""Alembic environment — conecta con PyMySQL (sync) para correr migraciones.

La URL se construye desde variables de entorno para que el mismo contenedor
sirva local (docker-compose) y cloud (RDS, PlanetScale, Cloud SQL).

Variables requeridas:
  DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

o bien una URL completa:
  DATABASE_URL=mysql+pymysql://user:pass@host:3306/db
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _db_url() -> str:
    """Construye la URL desde env vars. DATABASE_URL tiene prioridad."""
    url = os.getenv("DATABASE_URL")
    if url:
        # Asegurar que usa el driver pymysql (no aiomysql) para migraciones.
        return url.replace("mysql+aiomysql://", "mysql+pymysql://")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "asistente")
    password = os.getenv("DB_PASS", "asistente_pass")
    name = os.getenv("DB_NAME", "asistente_db")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


def run_migrations_offline() -> None:
    url = _db_url()
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        _db_url(),
        poolclass=pool.NullPool,
        connect_args={"connect_timeout": 10},
    )
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
