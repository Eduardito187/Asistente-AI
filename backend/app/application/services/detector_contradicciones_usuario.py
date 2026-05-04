from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Contradiccion:
    tipo: str
    explicacion: str
    sugerencia: str


class DetectorContradiccionesUsuario:
    """SRP: detectar contradicciones entre lo declarado y lo factible.

    Casos clasicos:
      - 'laptop gamer' + presupuesto 1500 Bs (no alcanza para gamer real)
      - 'TV 85\"' + presupuesto < 5000 Bs
      - 'iPhone' + 'no me importa la marca' (incompatible)
      - 'GPU dedicada' + presupuesto que no la cubre

    Devuelve una contradiccion por turno para que el agente la explique
    antes de mostrar productos."""

    _UMBRALES_GAMA: dict[str, dict[str, float]] = {
        "laptops_gamer": {"min": 8000, "ideal": 12000},
        "laptops_workstation": {"min": 12000, "ideal": 20000},
        "tv_85_pulgadas": {"min": 7000, "ideal": 12000},
        "tv_oled": {"min": 6500, "ideal": 10000},
        "smartphone_flagship": {"min": 6000, "ideal": 10000},
        "refrigerador_french_door": {"min": 8000, "ideal": 14000},
    }

    @classmethod
    def detectar(cls, perfil) -> Contradiccion | None:
        cat = (getattr(perfil, "categoria_foco", None) or "").lower()
        uso = (getattr(perfil, "uso_declarado", None) or "").lower()
        tier = (getattr(perfil, "desired_tier", None) or "").lower()
        gpu = getattr(perfil, "gpu_dedicada", None)
        ram = getattr(perfil, "ram_gb_min", None)
        techo = getattr(perfil, "presupuesto_max", None) or getattr(perfil, "presupuesto_ideal", None)
        pulg = getattr(perfil, "pulgadas", None)

        if not techo:
            return None

        if "laptop" in cat or "computador" in cat:
            if (gpu or "gamer" in uso or "render" in uso) and techo < 8000:
                return Contradiccion(
                    tipo="presupuesto_insuficiente_gpu",
                    explicacion=(
                        f"Pediste GPU dedicada / uso pesado pero el presupuesto Bs {int(techo)} "
                        "no alcanza — laptops con GPU dedicada confirmada parten de Bs 8.000."
                    ),
                    sugerencia="Subir presupuesto a Bs 8.500-11.000 o relajar GPU dedicada como 'preferible'.",
                )
            if uso in ("ingenieria", "render", "diseno") and techo < 6500:
                return Contradiccion(
                    tipo="presupuesto_insuficiente_uso_profesional",
                    explicacion=(
                        f"Para {uso} se necesita 16GB RAM, SSD 512GB y CPU i5/Ryzen 5+. "
                        f"Con Bs {int(techo)} solo entran modelos basicos."
                    ),
                    sugerencia=f"Considera Bs 7.500+ para {uso} con buen rendimiento.",
                )
            if (ram or 0) >= 16 and techo < 5500:
                return Contradiccion(
                    tipo="ram_minima_excede_presupuesto",
                    explicacion=f"Pediste 16GB RAM pero Bs {int(techo)} suele alcanzar para 8GB en laptops.",
                    sugerencia="Subir presupuesto a Bs 6.000+ o aceptar 8GB con upgrade futuro.",
                )

        if ("tv" in cat or "televisor" in cat) and pulg and pulg >= 75 and techo < 6000:
            return Contradiccion(
                tipo="presupuesto_insuficiente_tv_grande",
                explicacion=f"TV de {int(pulg)}\" parten desde Bs 6.000+, presupuesto Bs {int(techo)} es bajo.",
                sugerencia="Considera 55-65 pulgadas o subir presupuesto a Bs 6.500+.",
            )

        if tier in ("flagship", "premium", "alto") and techo < 4000:
            return Contradiccion(
                tipo="tier_premium_presupuesto_bajo",
                explicacion=f"Pediste tope de gama pero Bs {int(techo)} corresponde a gama media-baja.",
                sugerencia="Para flagship considera al menos Bs 6.000+. Si no, mejor relacion calidad/precio.",
            )

        return None
