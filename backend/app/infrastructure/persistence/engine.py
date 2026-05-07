from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import settings

# Pool tuneado para concurrencia:
# - pool_size=20: 20 conexiones permanentes (default era 5).
# - max_overflow=20: hasta 20 conexiones extra durante picos.
# - pool_recycle=3600: recicla conexiones cada hora (evita timeouts MySQL).
# - pool_pre_ping=True: chequea conexión antes de usar (evita "MySQL gone away").
# Con estos valores soportamos ~40 requests concurrentes sin esperar pool.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_recycle=3600,
    pool_timeout=10,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
