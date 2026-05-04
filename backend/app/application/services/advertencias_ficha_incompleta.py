from __future__ import annotations


class AdvertenciasFichaIncompleta:
    """SRP: detectar atributos N/D criticos para el uso declarado y emitir
    advertencias. El system_prompt obliga a decir 'No tengo ese dato en la
    ficha' — esta clase prepara la lista para que el render sea automatico."""

    _CRITICOS_POR_USO: dict[str, tuple[str, ...]] = {
        "ingenieria": ("gpu", "ram_gb", "capacidad_gb", "procesador"),
        "diseno": ("gpu", "ram_gb", "capacidad_gb"),
        "render": ("gpu", "ram_gb"),
        "gaming": ("gpu", "refresh_hz", "ram_gb"),
        "programacion": ("ram_gb", "capacidad_gb", "procesador"),
        "estudio": ("ram_gb", "capacidad_gb"),
        "oficina": ("ram_gb",),
    }

    _LABELS = {
        "gpu": "GPU dedicada",
        "ram_gb": "RAM",
        "capacidad_gb": "almacenamiento SSD",
        "procesador": "modelo de procesador",
        "refresh_hz": "Hz de pantalla",
        "tipo_panel": "tipo de panel",
        "capacidad_litros": "capacidad en litros",
        "capacidad_kg": "capacidad en kg",
    }

    @classmethod
    def advertencias(cls, producto, uso: str | None) -> list[str]:
        if not uso:
            return []
        criticos = cls._CRITICOS_POR_USO.get(uso.lower(), ())
        warnings: list[str] = []
        for atributo in criticos:
            if getattr(producto, atributo, None) in (None, "", 0):
                etiqueta = cls._LABELS.get(atributo, atributo)
                warnings.append(f"No tengo ese dato en la ficha tecnica: {etiqueta}.")
        return warnings
