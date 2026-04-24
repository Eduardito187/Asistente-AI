from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mariadb_user: str
    mariadb_password: str
    mariadb_host: str
    mariadb_port: int
    mariadb_db: str

    origen: str
    intervalo_seg: int
    dismac_csv_path: str
    akeneo_csv_path: str
    csv_path: str
    rest_url: str
    graphql_url: str

    mysql_source_user: str
    mysql_source_password: str
    mysql_source_host: str
    mysql_source_port: int
    mysql_source_db: str

    @staticmethod
    def desde_entorno() -> "Settings":
        return Settings(
            mariadb_user=os.environ["MARIADB_USER"],
            mariadb_password=os.environ["MARIADB_PASSWORD"],
            mariadb_host=os.environ.get("MARIADB_HOST", "db"),
            mariadb_port=int(os.environ.get("MARIADB_PORT", "3306")),
            mariadb_db=os.environ["MARIADB_DB"],
            origen=os.environ.get("INGEST_SOURCE", "dismac_csv"),
            intervalo_seg=int(os.environ.get("INGEST_INTERVAL_SECONDS", "86400")),
            dismac_csv_path=os.environ.get(
                "INGEST_DISMAC_CSV_PATH", "/app/data/feed_meta_scz.csv"
            ),
            akeneo_csv_path=os.environ.get(
                "INGEST_AKENEO_CSV_PATH", "/app/data/process/akeneo_processed.csv"
            ),
            csv_path=os.environ.get("INGEST_CSV_PATH", "/app/data/productos_sample.csv"),
            rest_url=os.environ.get("INGEST_REST_URL", ""),
            graphql_url=os.environ.get("INGEST_GRAPHQL_URL", ""),
            mysql_source_user=os.environ.get("MYSQL_USER", ""),
            mysql_source_password=os.environ.get("MYSQL_PASSWORD", ""),
            mysql_source_host=os.environ.get("MYSQL_HOST", "mysql-source"),
            mysql_source_port=int(os.environ.get("MYSQL_PORT", "3306")),
            mysql_source_db=os.environ.get("MYSQL_DB", ""),
        )

    def mariadb_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mariadb_user}:{self.mariadb_password}"
            f"@{self.mariadb_host}:{self.mariadb_port}/{self.mariadb_db}"
            "?charset=utf8mb4"
        )

    def mysql_source_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_source_user}:{self.mysql_source_password}"
            f"@{self.mysql_source_host}:{self.mysql_source_port}/{self.mysql_source_db}"
            "?charset=utf8mb4"
        )
