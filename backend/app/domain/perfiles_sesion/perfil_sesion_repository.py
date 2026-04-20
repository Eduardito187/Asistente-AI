from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .perfil_sesion import PerfilSesion


class PerfilSesionRepository(ABC):
    """Puerto de persistencia del agregado PerfilSesion."""

    @abstractmethod
    def obtener(self, sesion_id: UUID) -> Optional[PerfilSesion]: ...

    @abstractmethod
    def guardar(self, perfil: PerfilSesion) -> None: ...

    @abstractmethod
    def registrar_turno(
        self,
        sesion_id: UUID,
        skus_mostrados: Optional[str],
        precio_min: Optional[float],
        precio_max: Optional[float],
    ) -> None: ...

    @abstractmethod
    def registrar_alternativa_ofrecida(
        self, sesion_id: UUID, alternativa: str
    ) -> None: ...
