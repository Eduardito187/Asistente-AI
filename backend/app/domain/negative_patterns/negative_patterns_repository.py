from __future__ import annotations

from abc import ABC, abstractmethod

from .negative_pattern import NegativePattern


class NegativePatternsRepository(ABC):
    @abstractmethod
    def upsert(self, np: NegativePattern) -> None: ...

    @abstractmethod
    def listar_activos(self) -> list[NegativePattern]: ...

    @abstractmethod
    def incrementar_ocurrencia(self, patron: str) -> None: ...
