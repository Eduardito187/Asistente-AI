from __future__ import annotations

from .resultado_caso import ResultadoCaso


class ReporteConsola:
    """SRP: imprimir un resumen humano de los resultados al stdout."""

    @classmethod
    def imprimir(cls, resultados: list[ResultadoCaso]) -> int:
        total = len(resultados)
        pasados = sum(1 for r in resultados if r.paso())
        print("")
        print(f"=== Evaluacion offline — {pasados}/{total} casos OK ===")
        for r in resultados:
            cls._imprimir_caso(r)
        print("")
        return 0 if pasados == total else 1

    @staticmethod
    def _imprimir_caso(r: ResultadoCaso) -> None:
        marca = "OK" if r.paso() else "FAIL"
        print(f"[{marca}] {r.nombre}")
        for a in r.fallidos():
            print(f"    - {a.nombre}: {a.detalle}")
