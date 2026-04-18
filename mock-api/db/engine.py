from __future__ import annotations

import os

from sqlalchemy import create_engine

MYSQL_URL = (
    f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
    f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DB']}"
    "?charset=utf8mb4"
)

engine = create_engine(MYSQL_URL, pool_pre_ping=True, pool_recycle=1800)
