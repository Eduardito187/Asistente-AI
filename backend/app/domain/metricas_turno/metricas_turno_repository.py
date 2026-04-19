from __future__ import annotations

from abc import ABC, abstractmethod

from .metrica_turno import MetricaTurno


class MetricasTurnoRepository(ABC):
    """Puerto de persistencia del agregado MetricaTurno."""

    @abstractmethod
    def registrar(self, metrica: MetricaTurno) -> int: ...
