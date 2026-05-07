from __future__ import annotations

from abc import ABC, abstractmethod

from .prompt_variant import PromptVariant


class PromptVariantsRepository(ABC):
    @abstractmethod
    def listar_activas(self) -> list[PromptVariant]: ...

    @abstractmethod
    def upsert(self, variant: PromptVariant) -> None: ...

    @abstractmethod
    def desactivar(self, variant_name: str) -> None: ...
