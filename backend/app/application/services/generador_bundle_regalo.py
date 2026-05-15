from __future__ import annotations

from typing import Optional


class GeneradorBundleRegalo:
    """Genera sugerencias de bundle (combo regalo) cuando el cliente busca
    un producto como regalo. Devuelve texto listo para inyectar en el
    system prompt como contexto."""

    # Combos por categoría: producto principal → accesorios complementarios
    _BUNDLES: dict[str, list[str]] = {
        "Celulares": ["funda protectora", "vidrio templado", "cargador inalámbrico"],
        "Laptops": ["mouse inalámbrico", "mochila para laptop", "antivirus 1 año"],
        "Tablets": ["funda con teclado", "stylus", "vidrio templado"],
        "Televisores": ["soporte de pared", "soundbar o barra de sonido"],
        "Audio": ["estuche de transporte", "cable auxiliar de repuesto"],
        "Cocina Menor": ["set de utensilios", "recetario"],
        "Relojes": ["correa extra", "cargador de repuesto"],
    }

    @classmethod
    def sugerir(cls, categoria: Optional[str], destinatario: Optional[str] = None) -> str | None:
        """Devuelve texto de sugerencia de bundle o None si no aplica."""
        if not categoria:
            return None
        accesorios = cls._BUNDLES.get(categoria)
        if not accesorios:
            return None
        dest_txt = f" para {destinatario}" if destinatario else ""
        acc_str = ", ".join(accesorios[:-1]) + f" o {accesorios[-1]}"
        return (
            f"BUNDLE REGALO{dest_txt}: al ser un regalo, sugerí complementar con "
            f"{acc_str}. Mencionálo como opción al final de tu respuesta — "
            "no lo agregues al carrito sin confirmación."
        )
