from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from ..ports import UnitOfWork


@dataclass(frozen=True)
class VarianteAsignada:
    name: str
    prompt_extra: str


class AsignadorVarianteAB:
    """Asigna deterministamente una variante A/B/C... a una sesión.

    Determinismo: la misma sesion_id siempre cae en la misma variante (no
    cambia entre turnos). Distribución uniforme via sha256 + módulo.

    Uso típico (estatico): testear variantes del mensaje de derivación a
    ventas para medir cuál funciona mejor.

    Uso runtime (#15 review): variantes de prompt almacenadas en BD para
    A/B testing en produccion. La variante se persiste en metricas_turno
    (`variant_name`) para analisis posterior."""

    DEFAULT = VarianteAsignada(name="control", prompt_extra="")

    def __init__(self, uow_factory: Callable[[], UnitOfWork] | None = None) -> None:
        self._uow_factory = uow_factory

    @classmethod
    def variante(cls, sesion_id: UUID, opciones: tuple[str, ...]) -> str:
        """API estatica legacy: variante segun hash entre opciones tupla."""
        if not opciones:
            return ""
        h = hashlib.sha256(str(sesion_id).encode()).hexdigest()
        idx = int(h[:8], 16) % len(opciones)
        return opciones[idx]

    @classmethod
    def es_variante_a(cls, sesion_id: UUID, opciones: tuple[str, ...]) -> bool:
        return cls.variante(sesion_id, opciones) == opciones[0]

    def asignar_runtime(self, sesion_id: UUID) -> VarianteAsignada:
        """Lee variantes activas de prompt_variants y elige una via ruleta
        ponderada determinista. Si no hay variantes activas devuelve control."""
        if self._uow_factory is None:
            return self.DEFAULT
        try:
            with self._uow_factory() as uow:
                variantes = uow.prompt_variants.listar_activas()
        except Exception:
            return self.DEFAULT
        if not variantes:
            return self.DEFAULT
        total_peso = sum(v.weight for v in variantes if v.weight > 0)
        if total_peso <= 0:
            return self.DEFAULT
        bucket = self._hash_bucket(sesion_id, total_peso)
        acum = 0
        for v in variantes:
            if v.weight <= 0:
                continue
            acum += v.weight
            if bucket < acum:
                return VarianteAsignada(name=v.variant_name, prompt_extra=v.prompt_extra or "")
        return self.DEFAULT

    @staticmethod
    def _hash_bucket(sesion_id: UUID, modulo: int) -> int:
        h = hashlib.sha256(str(sesion_id).encode()).digest()
        return int.from_bytes(h[:4], "big") % modulo
