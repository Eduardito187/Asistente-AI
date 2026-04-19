from __future__ import annotations


class CalculadorPercentiles:
    """SRP: calcular percentiles sobre una lista ordenada de enteros."""

    @classmethod
    def p(cls, ordenados: list[int], percentil: float) -> int:
        if not ordenados:
            return 0
        if percentil <= 0:
            return int(ordenados[0])
        if percentil >= 100:
            return int(ordenados[-1])
        idx = max(0, min(len(ordenados) - 1, int(len(ordenados) * percentil / 100)))
        return int(ordenados[idx])
