from __future__ import annotations

from typing import Optional


class UmbralesTier:
    """SRP: mapea (subcategoría, tier) → (piso_precio, techo_precio).

    Los umbrales reflejan rangos reales del catálogo Dismac por subcategoría.
    Son estáticos por simplicidad — si el catálogo crece o se diversifica,
    el ingestor podría calcularlos dinámicamente con percentiles y persistir
    en una tabla auxiliar."""

    # subcategoria_norm → tier → (piso, techo); None = sin límite
    _TABLA: dict[str, dict[str, tuple[Optional[float], Optional[float]]]] = {
        "smartphones": {
            "flagship": (8000.0, None),
            "alto":     (3500.0, 8000.0),
            "medio":    (1500.0, 3500.0),
            "budget":   (None,   1500.0),
        },
        "smart tv": {
            "flagship": (6000.0, None),
            "alto":     (3000.0, 6000.0),
            "medio":    (1500.0, 3000.0),
            "budget":   (None,   1500.0),
        },
        "notebooks": {
            "flagship": (8000.0, None),
            "alto":     (4500.0, 8000.0),
            "medio":    (2500.0, 4500.0),
            "budget":   (None,   2500.0),
        },
        "smartwatch": {
            "flagship": (2500.0, None),
            "alto":     (1000.0, 2500.0),
            "medio":    (400.0,  1000.0),
            "budget":   (None,   400.0),
        },
        "tablets": {
            "flagship": (3500.0, None),
            "alto":     (1800.0, 3500.0),
            "medio":    (800.0,  1800.0),
            "budget":   (None,   800.0),
        },
    }

    # Fallback genérico cuando no conocemos la subcategoría: ratio sobre un
    # ancla (precio_foco u otro).
    _FALLBACK_RATIO_PISO: dict[str, float] = {
        "flagship": 0.60,
        "alto":     0.35,
        "medio":    0.15,
        "budget":   0.00,
    }

    @classmethod
    def tier_de(
        cls, precio: float, subcategoria: Optional[str]
    ) -> Optional[str]:
        """Inverso de `rango`: dado un precio y una subcategoría, devuelve
        el tier que ese precio ocuparía. Usado para inferir el tier del
        cliente cuando ya mencionó un producto foco (ej. si eligió un
        producto Bs 18.699 en Smartphones, su tier intencional es 'flagship').

        Devuelve None si no conocemos la subcategoría — no queremos forzar
        una inferencia en categorías donde los umbrales no aplican."""
        subcat_norm = (subcategoria or "").strip().lower()
        tabla_sub = cls._TABLA.get(subcat_norm)
        if not tabla_sub:
            return None
        # Orden descendente: flagship primero; el primero cuyo piso sea <= precio gana.
        for tier in ("flagship", "alto", "medio", "budget"):
            piso, techo = tabla_sub.get(tier, (None, None))
            piso_ok = piso is None or precio >= piso
            techo_ok = techo is None or precio < techo
            if piso_ok and techo_ok:
                return tier
        return None

    @classmethod
    def rango(
        cls,
        tier: Optional[str],
        subcategoria: Optional[str],
        precio_ancla: Optional[float] = None,
    ) -> tuple[Optional[float], Optional[float]]:
        """Devuelve (piso, techo) en Bs para el tier pedido.

        - Si la subcategoría tiene tabla, usa esos umbrales absolutos.
        - Si no, y hay `precio_ancla` (ej. precio del producto foco), calcula
          el piso como `precio_ancla * ratio` según el tier.
        - Si no hay nada, devuelve (None, None) — caller debe ignorar el filtro.
        """
        if not tier:
            return (None, None)
        subcat_norm = (subcategoria or "").strip().lower()
        tabla_sub = cls._TABLA.get(subcat_norm)
        if tabla_sub and tier in tabla_sub:
            return tabla_sub[tier]
        if precio_ancla is not None and tier in cls._FALLBACK_RATIO_PISO:
            return (precio_ancla * cls._FALLBACK_RATIO_PISO[tier], None)
        return (None, None)
