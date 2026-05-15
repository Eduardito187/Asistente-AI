from __future__ import annotations

from typing import Any


class FormateadorDetalleProducto:
    """Arma respuesta de texto determinística con specs completas de un
    producto. Se usa cuando el cliente pide detalles ('características',
    'specs', 'cuéntame más') y queremos respuesta confiable sin LLM.

    El input es el dict de `ProductoSerializer.detalle()` (lo que devuelve
    `ver_producto`)."""

    # Etiquetas humanas para los campos estructurados de `atributos`.
    # Mantenido en orden de relevancia para listar en respuesta.
    _ETIQUETAS = (
        ("pulgadas",            "Pantalla",          "{:g}\""),
        ("tipo_panel",          "Tipo de panel",     "{}"),
        ("resolucion",          "Resolución",        "{}"),
        ("refresh_hz",          "Refresh",           "{} Hz"),
        ("procesador",          "Procesador",        "{}"),
        ("ram_gb",              "RAM",               "{} GB"),
        ("capacidad_gb",        "Almacenamiento",    "{} GB"),
        ("gpu",                 "GPU",               "{}"),
        ("sistema_operativo",   "Sistema operativo", "{}"),
        ("bateria_mah",         "Batería",           "{} mAh"),
        ("camara_mp",           "Cámara principal",  "{} MP"),
        ("camara_frontal_mp",   "Cámara frontal",    "{} MP"),
        ("soporta_5g",          "5G",                "{}"),
        ("capacidad_litros",    "Capacidad",         "{} L"),
        ("capacidad_kg",        "Capacidad",         "{} kg"),
        ("potencia_w",          "Potencia",          "{} W"),
        ("color",               "Color",             "{}"),
    )

    @classmethod
    def formatear(cls, ficha: dict[str, Any]) -> str:
        """Genera respuesta multi-línea con todas las specs disponibles.
        Líneas sin dato no aparecen — preferimos respuesta corta a relleno N/D."""
        nombre = ficha.get("nombre") or "este producto"
        sku = ficha.get("sku") or ""
        marca = ficha.get("marca") or ""
        precio = ficha.get("precio_bob")
        precio_ant = ficha.get("precio_anterior_bob")
        modelo = ficha.get("modelo")
        meses_garantia = ficha.get("meses_garantia")

        # Encabezado: nombre + precio + SKU
        encabezado_partes = [f"**{nombre}**"]
        if marca:
            encabezado_partes.append(f"({marca})")
        encabezado = " ".join(encabezado_partes)
        if precio is not None:
            if precio_ant and precio_ant > precio:
                encabezado += f" — Bs {precio:.0f} (antes Bs {precio_ant:.0f})"
            else:
                encabezado += f" — Bs {precio:.0f}"
        if sku:
            encabezado += f" [{sku}]"

        # Specs estructuradas
        atributos = ficha.get("atributos") or {}
        specs_lineas = cls._formatear_atributos(atributos)

        # Modelo + garantía
        extras = []
        if modelo:
            extras.append(f"Modelo: {modelo}")
        if meses_garantia:
            extras.append(f"Garantía: {meses_garantia} meses")

        # Características Akeneo (bullets) si las hay
        caracteristicas = ficha.get("caracteristicas")
        bullets_extra = cls._formatear_caracteristicas(caracteristicas)

        # Atributos Akeneo extra (los que no están en specs estructuradas)
        akeneo = ficha.get("atributos_akeneo") or {}
        akeneo_lineas = cls._formatear_akeneo(akeneo, atributos)

        # Ensamblado final
        partes = [encabezado]
        if specs_lineas:
            partes.append("\n**Características principales:**\n" + "\n".join(specs_lineas))
        if extras:
            partes.append("\n" + " · ".join(extras))
        if bullets_extra:
            partes.append("\n**Características destacadas:**\n" + bullets_extra)
        if akeneo_lineas:
            partes.append("\n**Otros datos de ficha:**\n" + "\n".join(akeneo_lineas))

        partes.append(
            "\n¿Querés que te lo compare con otra opción o lo agrego al carrito?"
        )
        return "".join(partes)

    @classmethod
    def _formatear_atributos(cls, atributos: dict) -> list[str]:
        lineas = []
        for campo, etiqueta, formato in cls._ETIQUETAS:
            val = atributos.get(campo)
            if val is None or val == "":
                continue
            if isinstance(val, bool):
                val_fmt = "Sí" if val else "No"
            else:
                try:
                    val_fmt = formato.format(val)
                except (ValueError, TypeError):
                    val_fmt = str(val)
            lineas.append(f"- {etiqueta}: {val_fmt}")
        return lineas

    @staticmethod
    def _formatear_caracteristicas(caracteristicas: str | None) -> str:
        if not caracteristicas:
            return ""
        # `caracteristicas` viene del ingestor en formato "C1|C2|C3" — un bullet
        # por separador. Si no tiene "|", lo dejamos como un único bullet.
        items = [c.strip() for c in caracteristicas.split("|") if c.strip()]
        if not items:
            return ""
        return "\n".join(f"- {c}" for c in items[:8])  # tope 8 bullets

    @staticmethod
    def _formatear_akeneo(akeneo: dict, atributos_estructurados: dict) -> list[str]:
        """Atributos Akeneo extra que NO se mostraron en specs estructuradas.
        Filtra logística/operaciones (ya filtrado en ProductoSerializer) y
        toma máximo 6 entradas para no inflar la respuesta."""
        if not akeneo:
            return []
        # Llaves Akeneo que duplicarían specs ya mostradas (caso por caso)
        duplicadas = frozenset({
            "RAM", "Memoria RAM", "Procesador", "Pantalla", "Resolución",
            "Sistema operativo", "Almacenamiento", "GPU", "Batería",
        })
        lineas = []
        for k, v in list(akeneo.items())[:6]:
            if k in duplicadas:
                continue
            if v is None or str(v).strip() == "":
                continue
            lineas.append(f"- {k}: {v}")
        return lineas
