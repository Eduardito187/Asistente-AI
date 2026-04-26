from __future__ import annotations

from dataclasses import dataclass

from .umbrales_tier import UmbralesTier

_NOMBRE_TIER: dict[str, str] = {
    "flagship": "premium/flagship",
    "alto": "gama alta",
    "medio": "gama media",
    "budget": "económica",
}

_NOMBRE_SUBCAT: dict[str, str] = {
    "smartphones": "celular",
    "notebooks": "laptop",
    "smart tv": "televisor",
    "refrigeradores": "refrigeradora",
    "lavadoras": "lavadora",
    "tablets": "tablet",
    "cocinas": "cocina",
    "audífonos": "auriculares",
    "audifonos": "auriculares",
    "smartwatch": "smartwatch",
}


@dataclass(frozen=True)
class ContradiccionPresupuesto:
    mensaje: str
    tier: str
    presupuesto: float
    piso_tier: float
    subcategoria: str | None


class DetectorContradiccionPresupuesto:
    """SRP: detecta cuando el presupuesto declarado es insuficiente para el
    tier solicitado. Devuelve un objeto con el mensaje explicativo listo para
    incluir en la respuesta, o None si no hay contradicción."""

    @classmethod
    def detectar(
        cls,
        tier: str | None,
        presupuesto_max: float | None,
        subcategoria: str | None,
    ) -> ContradiccionPresupuesto | None:
        if not tier or not presupuesto_max:
            return None
        if tier == "budget":
            return None
        piso, _ = UmbralesTier.rango(tier, subcategoria)
        if piso is None or presupuesto_max >= piso:
            return None
        nombre_cat = _NOMBRE_SUBCAT.get((subcategoria or "").lower(), subcategoria or "producto")
        nombre_tier = _NOMBRE_TIER.get(tier, tier)
        msg = (
            f"Con Bs {presupuesto_max:.0f}, los {nombre_cat}s que vamos a encontrar "
            f"son de gama media o económica. "
            f"Para {nombre_tier} el rango empieza en Bs {piso:.0f}. "
            f"Te muestro la mejor opción dentro de tu presupuesto."
        )
        return ContradiccionPresupuesto(
            mensaje=msg,
            tier=tier,
            presupuesto=presupuesto_max,
            piso_tier=piso,
            subcategoria=subcategoria,
        )
