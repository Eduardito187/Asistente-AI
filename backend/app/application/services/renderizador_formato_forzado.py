from __future__ import annotations

from .formato_solicitado import FormatoSolicitado


class RenderizadorFormatoForzado:
    """SRP: cuando el cliente pidio una `forma` estructural (comprar_evitar,
    seguro_barato) y el path determinista de `_forzar_busqueda` esta a cargo
    de renderizar (no el LLM), produce las lineas con la estructura pedida.

    Para 'comprar_evitar': 3 lineas usando el mejor producto y un texto
    generico de "que evitar" segun categoria. Es honesto: si no podemos
    generar 'evitar' con datos reales, lo omitimos."""

    @classmethod
    def renderizar(
        cls, fmt: FormatoSolicitado, productos: list, perfil
    ) -> str | None:
        if fmt.vacio() or not productos:
            return None
        if fmt.forma == "comprar_evitar":
            return cls._render_comprar_evitar(productos, perfil)
        if fmt.forma == "seguro_barato":
            return cls._render_seguro_barato(productos)
        return None

    @classmethod
    def _render_comprar_evitar(cls, productos: list, perfil) -> str:
        principal = productos[0]
        cat = (getattr(perfil, "categoria_efectiva", lambda: None)() or "").lower()
        evitar = cls._texto_evitar_categoria(cat, perfil)
        por_que = cls._texto_por_que(perfil, cat)
        lineas = [
            f"Comprar: {cls._linea_producto(principal)} — la apuesta segura para tu uso.",
        ]
        if evitar:
            lineas.append(f"Evitar: {evitar}")
        lineas.append(f"Por que: {por_que}")
        return "\n".join(lineas)

    @classmethod
    def _render_seguro_barato(cls, productos: list) -> str:
        if len(productos) < 2:
            principal = productos[0]
            return f"Segura: {cls._linea_producto(principal)} — la mejor opcion en tu rango."
        principal = productos[0]
        # "Barata" = la mas economica disponible.
        barata = min(productos, key=lambda p: float(p.precio.monto))
        if barata is principal and len(productos) > 1:
            barata = sorted(productos, key=lambda p: float(p.precio.monto))[1]
        return "\n".join([
            f"Segura: {cls._linea_producto(principal)} — la apuesta mas confiable.",
            f"Barata: {cls._linea_producto(barata)} — la opcion mas accesible.",
        ])

    @staticmethod
    def _linea_producto(p) -> str:
        return f"{p.nombre} — Bs {p.precio.monto:.0f} [{p.sku}]"

    @staticmethod
    def _texto_evitar_categoria(cat: str, perfil) -> str | None:
        """Texto generico de 'evitar' por categoria. Solo categorias donde
        tenemos pattern claro de tier-bajo a evitar para uso profesional."""
        if "laptop" in cat:
            uso = (getattr(perfil, "uso_declarado", None) or "").lower()
            if any(k in uso for k in ("autocad", "render", "ingenieria", "diseno", "edicion", "gaming")):
                return (
                    "Vivobook Go / Chromebook / equipos con Celeron o Pentium "
                    "y 8GB RAM — se quedan cortos para uso profesional."
                )
            return "equipos con Celeron/Pentium o 8GB RAM si planeas usarlo varios anios."
        return None

    @staticmethod
    def _texto_por_que(perfil, cat: str) -> str:
        """Una frase sintetica explicando la decision desde el perfil."""
        partes: list[str] = []
        uso = getattr(perfil, "uso_declarado", None)
        if uso:
            partes.append(f"para {uso}")
        if getattr(perfil, "ram_gb_min", None):
            partes.append(f"pesa la RAM ({perfil.ram_gb_min}GB minimo)")
        if getattr(perfil, "gpu_dedicada", None):
            partes.append("y la GPU dedicada")
        if not partes:
            return "balance entre características y precio según tu rango."
        return ", ".join(partes) + " mas que un precio bajo."
