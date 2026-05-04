from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccesorioSugerido:
    keyword_busqueda: str
    razon: str
    prioridad: int  # 1 = imprescindible, 3 = nice-to-have


class AsesorAccesoriosContextual:
    """SRP: dado un producto principal (laptop/TV/celular), sugerir 2-3
    accesorios contextuales con razon comercial concreta.

    La diferencia con SugeridorAccesoriosRelacionados (cross-sell de BD) es
    que aca elegimos QUE keywords buscar segun el USO declarado del cliente,
    no por relacion estatica del catalogo."""

    @classmethod
    def sugerir(cls, producto, perfil) -> list[AccesorioSugerido]:
        cat = (getattr(producto, "categoria", "") or "").lower()
        subcat = (getattr(producto, "subcategoria", "") or "").lower()
        uso = (getattr(perfil, "uso_declarado", None) or "").lower()
        es_laptop = "laptop" in cat or "computador" in cat or "notebook" in subcat
        es_tv = "tv" in cat or "televisor" in cat
        es_cel = "celular" in cat or "smartphone" in subcat or "telefono" in cat

        if es_laptop:
            return cls._para_laptop(uso)
        if es_tv:
            return cls._para_tv()
        if es_cel:
            return cls._para_celular(uso)
        return []

    @staticmethod
    def _para_laptop(uso: str) -> list[AccesorioSugerido]:
        base = [
            AccesorioSugerido("mouse inalambrico", "Trabajar con touchpad cansa el brazo en sesiones largas.", 1),
            AccesorioSugerido("mochila para laptop", "Proteger la laptop al trasladarla.", 2),
        ]
        if uso in ("ingenieria", "diseno", "render", "programacion", "gaming"):
            base.append(AccesorioSugerido(
                "base refrigeradora cooler",
                f"Para {uso} la CPU/GPU se calienta — el cooler extiende vida util.",
                1,
            ))
            base.append(AccesorioSugerido(
                "monitor externo 24 pulgadas",
                "Trabajar en pantalla grande mejora productividad 20-30%.",
                3,
            ))
        if uso in ("estudio", "oficina", "universidad"):
            base.append(AccesorioSugerido(
                "audifonos con microfono",
                "Indispensables para clases/reuniones online.",
                2,
            ))
        return base[:3]

    @staticmethod
    def _para_tv() -> list[AccesorioSugerido]:
        return [
            AccesorioSugerido("soporte de pared para tv", "Si la queres montada, mucho mejor que la base original.", 1),
            AccesorioSugerido("hdmi 2.1 cable", "Para PS5/Xbox a 120Hz necesitas HDMI 2.1 certificado.", 2),
            AccesorioSugerido("barra de sonido soundbar", "El audio integrado de TVs delgadas es flojo.", 2),
        ]

    @staticmethod
    def _para_celular(uso: str) -> list[AccesorioSugerido]:
        base = [
            AccesorioSugerido("funda case protector", "Las pantallas se rompen — un case Bs 50 evita Bs 1.000 de reparacion.", 1),
            AccesorioSugerido("vidrio templado mica", "Protege la pantalla frente a rayones.", 1),
            AccesorioSugerido("cargador rapido tipo c", "Si el equipo soporta carga rapida, vale la pena el original.", 2),
        ]
        if "gaming" in uso or "jugar" in uso:
            base.append(AccesorioSugerido(
                "gamepad bluetooth",
                "Hace de tu celular una mini consola.",
                3,
            ))
        return base[:3]
