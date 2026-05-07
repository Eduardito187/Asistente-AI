from __future__ import annotations

from abc import ABC, abstractmethod

from .perfil_historico import PerfilHistorico


class PerfilesHistoricosRepository(ABC):
    """Puerto del agregado PerfilHistorico."""

    @abstractmethod
    def upsert(self, perfil: PerfilHistorico) -> None: ...

    @abstractmethod
    def obtener_por_contacto_hash(self, contacto_hash: str) -> PerfilHistorico | None: ...
