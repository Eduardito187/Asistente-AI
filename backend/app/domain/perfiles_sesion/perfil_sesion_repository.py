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

    @abstractmethod
    def limpiar(self, sesion_id: UUID) -> None: ...

    @abstractmethod
    def limpiar_dominio(self, sesion_id: UUID, dominio: str) -> None:
        """Limpia solo los atributos del dominio indicado al cambiar de macro-dominio.
        dominio: 'digital' | 'linea_blanca' | 'tv'"""
        ...

    @abstractmethod
    def limpiar_presupuesto_y_marca(self, sesion_id: UUID) -> None:
        """Limpia presupuesto y marca huérfanos cuando el dominio anterior es
        desconocido pero hay contaminación potencial."""
        ...

    @abstractmethod
    def obtener_contexto_dominio(self, sesion_id: UUID) -> dict:
        """Devuelve el JSON almacenado de snapshots de contexto por dominio.
        Clave: 'digital' | 'linea_blanca' | 'tv'. Valor: dict de attrs."""
        ...

    @abstractmethod
    def guardar_contexto_dominio(self, sesion_id: UUID, contexto: dict) -> None:
        """Persiste el JSON de snapshots de contexto por dominio."""
        ...
