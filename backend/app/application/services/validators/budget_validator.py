from __future__ import annotations

from .category_consistency_validator import ResultadoValidacion
from ....domain.aprendizaje import ReasonCode


class BudgetValidator:
    """SRP: verifica que productos citados respeten el presupuesto_max
    declarado del perfil. Permite hasta 10% sobre techo (margen de gama)."""

    TOLERANCIA = 0.10

    @classmethod
    def validar(cls, perfil_estado: dict, productos: list[dict]) -> ResultadoValidacion:
        techo = perfil_estado.get("presupuesto_max")
        if not techo or not productos:
            return ResultadoValidacion(True, ReasonCode.OK, "no aplica")
        techo_flexible = float(techo) * (1 + cls.TOLERANCIA)
        for p in productos:
            precio = p.get("precio_bob") or p.get("precio") or 0
            try:
                precio_f = float(precio)
            except (TypeError, ValueError):
                continue
            if precio_f > techo_flexible:
                return ResultadoValidacion(
                    False, ReasonCode.LOW_END_FOR_PREMIUM,  # reuso codigo "fuera-rango"
                    f"sku={p.get('sku')} {precio_f}>{techo_flexible:.0f}",
                )
        return ResultadoValidacion(True, ReasonCode.OK, "presupuesto respetado")
