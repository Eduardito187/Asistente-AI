from __future__ import annotations

from abc import ABC, abstractmethod

from .golden_conversation import GoldenConversation


class GoldenConversationsRepository(ABC):
    @abstractmethod
    def upsert(self, golden: GoldenConversation) -> int: ...

    @abstractmethod
    def listar_activas(self, limite: int = 50) -> list[GoldenConversation]: ...

    @abstractmethod
    def buscar_por_categoria(
        self, categoria: str, intencion: str | None = None, limite: int = 5
    ) -> list[GoldenConversation]: ...

    @abstractmethod
    def desactivar(self, caso_que_cubre: str) -> None: ...
