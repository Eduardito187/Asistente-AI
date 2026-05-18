from __future__ import annotations

from .definicion_atributo import DefinicionAtributo


class CatalogoAtributosProducto:
    """Fuente única de verdad de los atributos filtrables de productos.

    Cada entrada define el ciclo completo: mensaje → perfil → query → SQL.
    Para agregar un atributo nuevo: añadir una DefinicionAtributo aquí y el
    resto del sistema lo propaga automáticamente (tests de contrato lo verifican).
    """

    _ATRIBUTOS: tuple[DefinicionAtributo, ...] = (
        # ── Numéricos con columna SQL dedicada ──────────────────────────────
        DefinicionAtributo(
            nombre="ram_gb_min", tipo="int", sticky=True,
            columna_sql="ram_gb", operador_sql=">=",
            descripcion_llm="RAM mínima en GB.",
            ejemplo="16",
        ),
        DefinicionAtributo(
            nombre="capacidad_gb_min", tipo="int", sticky=True,
            columna_sql="capacidad_gb", operador_sql=">=",
            descripcion_llm="Almacenamiento mínimo en GB (celulares, laptops, tablets).",
            ejemplo="256",
        ),
        DefinicionAtributo(
            nombre="refresh_hz_min", tipo="int", sticky=True,
            columna_sql="refresh_hz", operador_sql=">=",
            descripcion_llm="Frecuencia de refresco mínima en Hz (TVs, monitores, laptops gaming).",
            ejemplo="120",
        ),
        DefinicionAtributo(
            nombre="bateria_mah_min", tipo="int", sticky=True,
            columna_sql="bateria_mah", operador_sql=">=",
            descripcion_llm="Capacidad de batería mínima en mAh (smartphones, power banks).",
            ejemplo="5000",
        ),
        DefinicionAtributo(
            nombre="camara_mp_min", tipo="int", sticky=True,
            columna_sql="camara_mp", operador_sql=">=",
            descripcion_llm="Megapíxeles mínimos de cámara trasera principal (smartphones).",
            ejemplo="50",
        ),
        DefinicionAtributo(
            nombre="capacidad_litros_min", tipo="float", sticky=True,
            columna_sql="capacidad_litros", operador_sql=">=",
            descripcion_llm="Capacidad mínima en litros (heladeras, hornos, microondas).",
            ejemplo="420",
        ),
        DefinicionAtributo(
            nombre="capacidad_kg_min", tipo="float", sticky=True,
            columna_sql="capacidad_kg", operador_sql=">=",
            descripcion_llm="Capacidad mínima en kg (lavadoras).",
            ejemplo="12",
        ),
        DefinicionAtributo(
            nombre="potencia_w_min", tipo="int", sticky=True,
            columna_sql="potencia_w", operador_sql=">=",
            descripcion_llm="Potencia mínima en W (licuadoras, secadores, aspiradoras).",
            ejemplo="1500",
        ),
        DefinicionAtributo(
            nombre="pulgadas", tipo="float", sticky=True,
            columna_sql="pulgadas", operador_sql="=",
            descripcion_llm="Pulgadas exactas (tolerancia ±0.5). Ej: 55 para TV de 55\".",
            ejemplo="55",
        ),
        # ── Booleanos con columna SQL dedicada ──────────────────────────────
        DefinicionAtributo(
            nombre="soporta_5g", tipo="bool", sticky=True,
            columna_sql="soporta_5g", operador_sql="=",
            descripcion_llm="True si el cliente exige 5G. Productos sin 5G confirmado quedan fuera.",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="gpu_dedicada", tipo="bool", sticky=True,
            columna_sql="gpu", operador_sql="bool_text",
            descripcion_llm=(
                "True para laptops/PCs con GPU dedicada (NVIDIA GeForce, AMD Radeon). "
                "NUNCA inferir GPU dedicada solo porque el procesador sea i7 o Ryzen 7."
            ),
            ejemplo="True",
        ),
        # ── Booleanos detectados en atributos_texto (LIKE keywords) ─────────
        DefinicionAtributo(
            nombre="inverter", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="Tecnología inverter (refrigeradoras, lavadoras, AC).",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="no_frost", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="Sistema No Frost (refrigeradoras).",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="smart_tv", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="Smart TV con SO (Android TV, Google TV, webOS, Tizen).",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="bluetooth_incluido", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="Bluetooth incluido.",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="nfc", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="NFC para pagos contactless.",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="usb_c", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="Puerto USB-C / Type-C.",
            ejemplo="True",
        ),
        DefinicionAtributo(
            nombre="hdmi_2_1", tipo="bool", sticky=True,
            columna_sql="", operador_sql="bool_text",
            descripcion_llm="HDMI 2.1 (gaming 4K@120Hz).",
            ejemplo="True",
        ),
        # ── String con operador LIKE / = ─────────────────────────────────────
        DefinicionAtributo(
            nombre="sistema_operativo", tipo="str", sticky=True,
            columna_sql="sistema_operativo", operador_sql="=",
            descripcion_llm="Sistema operativo (Android, iOS, Windows, macOS, Linux, FreeDOS, ChromeOS).",
            ejemplo="Android",
        ),
        DefinicionAtributo(
            nombre="tipo_panel", tipo="str", sticky=True,
            columna_sql="tipo_panel", operador_sql="=",
            descripcion_llm="Panel de pantalla.",
            ejemplo="OLED",
        ),
        DefinicionAtributo(
            nombre="resolucion", tipo="str", sticky=True,
            columna_sql="resolucion", operador_sql="=",
            descripcion_llm="Resolución de pantalla.",
            ejemplo="4K",
        ),
    )

    @classmethod
    def todos(cls) -> tuple[DefinicionAtributo, ...]:
        return cls._ATRIBUTOS

    @classmethod
    def sticky(cls) -> tuple[DefinicionAtributo, ...]:
        return tuple(a for a in cls._ATRIBUTOS if a.sticky)

    @classmethod
    def por_nombre(cls, nombre: str) -> DefinicionAtributo | None:
        for a in cls._ATRIBUTOS:
            if a.nombre == nombre:
                return a
        return None

    @classmethod
    def nombres_sticky(cls) -> frozenset[str]:
        return frozenset(a.nombre for a in cls._ATRIBUTOS if a.sticky)
