from __future__ import annotations

from typing import Any

# Atributos de PerfilSesion que pertenecen a cada dominio.
# Se usan para guardar/restaurar el contexto al cambiar de dominio.
ATTRS_DOMINIO: dict[str, frozenset[str]] = {
    "digital": frozenset({
        "marca_preferida", "presupuesto_max", "presupuesto_ideal",
        "presupuesto_min_buscado", "desired_tier", "uso_declarado",
        "pulgadas", "tipo_panel", "resolucion",
        "ram_gb_min", "ssd_gb_min", "gpu_dedicada",
        "refresh_hz_min", "bateria_mah_min", "camara_mp_min",
        "soporta_5g", "sistema_operativo", "nfc", "usb_c",
        "bluetooth_incluido", "hdmi_2_1",
    }),
    "linea_blanca": frozenset({
        "marca_preferida", "presupuesto_max", "presupuesto_ideal",
        "presupuesto_min_buscado", "desired_tier", "uso_declarado",
        "capacidad_litros_min", "capacidad_kg_min", "potencia_w_min",
        "inverter", "no_frost",
    }),
    "tv": frozenset({
        "marca_preferida", "presupuesto_max", "presupuesto_ideal",
        "presupuesto_min_buscado", "desired_tier", "uso_declarado",
        "pulgadas", "tipo_panel", "resolucion",
        "smart_tv", "hdmi_2_1", "bluetooth_incluido",
    }),
}

_DOMINIOS: dict[str, set[str]] = {
    "digital": {
        # términos naturales
        "celulares", "smartphones", "tablets", "laptops", "notebooks",
        "computadoras", "computadores", "pcs", "gaming", "monitores",
        "smartwatch", "relojes", "audífonos", "audifonos", "auriculares",
        "parlantes", "impresoras", "cámaras", "camaras",
        # nombres canónicos de BD (categoria_foco)
        "computación", "computacion", "fotografía", "fotografia",
        "impresión", "impresion", "audio", "relojería", "relojeria",
    },
    "linea_blanca": {
        # términos naturales
        "refrigeradoras", "refrigeradores", "heladeras", "neveras",
        "congeladores", "lavadoras", "secadoras", "microondas", "hornos",
        "cocinas", "freidoras", "cafeteras", "licuadoras", "aspiradoras",
        "ventiladores", "aires acondicionados",
        # nombres canónicos de BD (categoria_foco)
        "refrigeración", "refrigeracion", "lavado", "climatización",
        "climatizacion", "cocina", "cocina menor",
        "pequeños electrodomésticos", "pequenos electrodomesticos",
    },
    "tv": {
        # términos naturales
        "televisores", "smart tv", "smart tvs", "tvs",
        # nombres canónicos de BD
        "accesorios tv",
    },
}

# Mapeo de nombre canónico → dominio
_CAT_DOMINIO: dict[str, str] = {
    cat: dominio
    for dominio, cats in _DOMINIOS.items()
    for cat in cats
}


class DetectorCambioDominio:
    """SRP: determina si dos categorías pertenecen a macro-dominios distintos.

    Usado para limpiar atributos incompatibles del perfil cuando el cliente
    cambia de, por ejemplo, celulares (digital) a refrigeradoras (linea_blanca).
    Sin esto el perfil acumula ssd_gb_min, marca, presupuesto de una sesión de
    teléfonos y los aplica incorrectamente a la búsqueda de electrodomésticos."""

    @staticmethod
    def dominio(categoria: str | None) -> str | None:
        if not categoria:
            return None
        return _CAT_DOMINIO.get(categoria.strip().lower())

    @classmethod
    def dominios_distintos(
        cls, cat_vieja: str | None, cat_nueva: str | None
    ) -> bool:
        """True si ambas categorías están en dominios distintos y no nulos."""
        d_viejo = cls.dominio(cat_vieja)
        d_nuevo = cls.dominio(cat_nueva)
        if d_viejo is None or d_nuevo is None:
            return False
        return d_viejo != d_nuevo

    @classmethod
    def categoria_mensaje(cls, mensaje: str) -> str | None:
        """Extrae la primera categoría reconocida del mensaje por keyword matching.
        Usado como fallback cuando el extractor LLM no detecta categoria_foco."""
        if not mensaje:
            return None
        msg = mensaje.strip().lower()
        for _dominio, cats in _DOMINIOS.items():
            for cat in cats:
                if cat in msg:
                    return cat
        return None

    @staticmethod
    def snapshot_perfil(dominio: str, perfil: Any) -> dict:
        """Extrae del perfil solo los attrs que pertenecen al dominio dado.
        Ignora los None para no guardar ruido en el snapshot."""
        attrs = ATTRS_DOMINIO.get(dominio, frozenset())
        snap: dict = {}
        for attr in attrs:
            val = getattr(perfil, attr, None)
            if val is not None:
                snap[attr] = val
        return snap
