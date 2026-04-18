from __future__ import annotations

from ...application.ports import SourceAdapter
from ...domain.clasificacion import Clasificador
from ..config import Settings
from .csv_adapter import CsvAdapter
from .dismac_csv_adapter import DismacCsvAdapter
from .graphql_adapter import GraphqlAdapter
from .mysql_source_adapter import MysqlSourceAdapter
from .rest_adapter import RestAdapter


class AdapterFactory:
    """Resuelve el SourceAdapter adecuado segun la configuracion del ingestor."""

    @staticmethod
    def construir(settings: Settings) -> SourceAdapter:
        origen = settings.origen.lower().strip()
        if origen in ("dismac", "dismac_csv", "dismac-csv"):
            return DismacCsvAdapter(path=settings.dismac_csv_path, clasificador=Clasificador())
        if origen == "csv":
            return CsvAdapter(path=settings.csv_path)
        if origen == "mysql":
            return MysqlSourceAdapter(url=settings.mysql_source_url())
        if origen == "rest":
            if not settings.rest_url:
                raise ValueError("INGEST_REST_URL no configurado")
            return RestAdapter(url=settings.rest_url)
        if origen == "graphql":
            if not settings.graphql_url:
                raise ValueError("INGEST_GRAPHQL_URL no configurado")
            return GraphqlAdapter(url=settings.graphql_url)
        raise ValueError(f"INGEST_SOURCE desconocido: {origen}")
