from __future__ import annotations

from abc import ABC, abstractmethod

from .synonym_candidato import SynonymCandidato


class SynonymsCandidatosRepository(ABC):
    """Puerto de salida del agregado SynonymCandidato."""

    @abstractmethod
    def upsert_incrementando(self, termino: str, categoria_inferida: str | None) -> int:
        """Registra termino y devuelve el contador acumulado."""

    @abstractmethod
    def listar_top(self, limite: int = 50, solo_no_promovidos: bool = True) -> list[SynonymCandidato]: ...

    @abstractmethod
    def marcar_promovido(self, id_: int) -> None: ...
