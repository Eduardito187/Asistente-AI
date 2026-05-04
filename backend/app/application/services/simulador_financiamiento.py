from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanCuotas:
    cuotas: int
    monto_cuota: float
    interes_total: float
    descripcion: str


class SimuladorFinanciamiento:
    """SRP: a partir del precio del producto, sugerir planes de cuotas
    populares en Bolivia (3, 6, 12, 18 cuotas). Permite que Dismi diga:
    'O en 12 cuotas de Bs X' sin que el LLM lo invente.

    Las tasas son aproximadas y publicas — banco/fintech reales pueden
    variar. Aqui usamos curva conservadora de e-commerce boliviano."""

    _TASAS_ANUALES: dict[int, float] = {
        3: 0.00,    # promo sin intereses 3 cuotas
        6: 0.06,    # 6% anual aprox
        12: 0.12,   # 12% anual
        18: 0.16,   # 18% anual
    }

    _UMBRAL_MIN_FINANCIABLE = 1500  # productos < 1500 Bs no se financian a 12 meses

    @classmethod
    def sugerir(cls, precio: float) -> list[PlanCuotas]:
        if precio < cls._UMBRAL_MIN_FINANCIABLE:
            return []
        planes: list[PlanCuotas] = []
        for cuotas, tasa in cls._TASAS_ANUALES.items():
            if precio < 4000 and cuotas >= 18:
                continue
            tasa_mensual = tasa / 12
            if tasa_mensual == 0:
                cuota = precio / cuotas
                interes = 0.0
            else:
                cuota = (precio * tasa_mensual) / (1 - (1 + tasa_mensual) ** -cuotas)
                interes = (cuota * cuotas) - precio
            descripcion = (
                f"{cuotas} cuotas de Bs {cuota:,.0f}"
                + (" (sin intereses)" if tasa == 0 else f" (interes Bs {interes:,.0f})")
            )
            planes.append(PlanCuotas(
                cuotas=cuotas,
                monto_cuota=round(cuota, 2),
                interes_total=round(interes, 2),
                descripcion=descripcion,
            ))
        return planes

    @classmethod
    def mejor_plan(cls, precio: float) -> PlanCuotas | None:
        planes = cls.sugerir(precio)
        if not planes:
            return None
        sin_interes = [p for p in planes if p.interes_total == 0]
        if sin_interes:
            return sin_interes[0]
        return min(planes, key=lambda p: p.interes_total)
