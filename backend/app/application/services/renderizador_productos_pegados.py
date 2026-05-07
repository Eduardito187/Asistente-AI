from __future__ import annotations

from .parser_productos_pegados import ListadoPegado, ProductoPegado


class RenderizadorProductosPegados:
    """SRP: convierte un `ListadoPegado` en un texto comparativo
    deterministico cuando el cliente pego varios productos en el chat.

    No inventa datos: si la GPU no esta en el texto, dice 'No tengo ese
    dato en la ficha tecnica'. Si el cliente pidio un criterio (ej. 'cual
    para autocad?'), el ranking se hace por:
      1. RAM mayor primero (peso pesado para uso pro)
      2. Storage mayor
      3. CPU tier (i7/Ryzen 7 > i5/Ryzen 5 > i3)
      4. Precio menor (desempate)"""

    @classmethod
    def renderizar(cls, listado: ListadoPegado) -> str:
        if listado.vacio():
            return ""
        ordenados = sorted(listado.productos, key=cls._score, reverse=True)
        principal = ordenados[0]
        lineas: list[str] = [
            "Comparando las opciones que pegaste:",
            "",
        ]
        for p in ordenados:
            lineas.append(f"- {cls._linea(p)}")
        lineas.append("")
        lineas.append(f"Mejor opcion: **{cls._titulo(principal)}** — {cls._razon(principal)}")
        return "\n".join(lineas)

    @classmethod
    def _score(cls, p: ProductoPegado) -> tuple:
        """Tuple ordenable: RAM > Storage > tier CPU > -precio."""
        return (
            p.ram_gb or 0,
            p.storage_gb or 0,
            cls._tier_cpu(p.cpu),
            -(p.precio_bob or 1e9),
        )

    @staticmethod
    def _tier_cpu(cpu: str | None) -> int:
        if not cpu:
            return 0
        c = cpu.lower()
        if "i9" in c or "ryzen 9" in c or "m3 max" in c or "m4" in c:
            return 5
        if "i7" in c or "ryzen 7" in c or "m3 pro" in c:
            return 4
        if "i5" in c or "ryzen 5" in c or "m3" in c or "m2" in c:
            return 3
        if "i3" in c or "ryzen 3" in c or "m1" in c:
            return 2
        if "celeron" in c or "pentium" in c or "atom" in c:
            return 1
        return 2

    @classmethod
    def _linea(cls, p: ProductoPegado) -> str:
        partes: list[str] = []
        partes.append(cls._titulo(p))
        if p.cpu:
            partes.append(p.cpu.upper())
        if p.ram_gb:
            partes.append(f"{p.ram_gb}GB RAM")
        if p.storage_gb:
            tb = p.storage_gb // 1024
            partes.append(f"{tb}TB" if tb >= 1 and p.storage_gb % 1024 == 0 else f"{p.storage_gb}GB")
        if p.precio_bob:
            partes.append(f"Bs {int(p.precio_bob)}")
        if p.gpu:
            partes.append(f"GPU: {p.gpu}")
        else:
            partes.append("GPU: No tengo ese dato en la ficha tecnica")
        if p.sistema_operativo:
            so = p.sistema_operativo.lower()
            if "freedos" in so.replace(" ", "") or "free dos" in so:
                partes.append("OS: FreeDOS (sin Windows preinstalado)")
            else:
                partes.append(f"OS: {p.sistema_operativo}")
        return " | ".join(partes)

    @staticmethod
    def _titulo(p: ProductoPegado) -> str:
        if p.marca and p.modelo:
            return f"{p.marca} {p.modelo}"
        if p.marca:
            return p.marca
        if p.modelo:
            return p.modelo
        return p.raw[:40]

    @classmethod
    def _razon(cls, p: ProductoPegado) -> str:
        partes: list[str] = []
        if p.ram_gb and p.ram_gb >= 16:
            partes.append(f"{p.ram_gb}GB de RAM")
        if p.storage_gb and p.storage_gb >= 512:
            partes.append(f"{p.storage_gb}GB de storage")
        if cls._tier_cpu(p.cpu) >= 4:
            partes.append("CPU de gama alta")
        if not partes:
            partes.append("mejor balance de specs/precio entre las opciones pegadas")
        if not p.gpu:
            partes.append("recordando que no confirmo GPU en el texto")
        return ", ".join(partes) + "."
