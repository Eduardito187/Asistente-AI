from __future__ import annotations

import re
from typing import Optional

from ...domain.productos import Producto


class ExtractorSpecsProducto:
    """SRP: extrae especificaciones técnicas de un Producto combinando las
    columnas estructuradas del catálogo (ram_gb, pulgadas, procesador, etc.)
    con un parseo regex del `nombre + descripcion` para atributos que no
    tienen columna todavía (batería mAh, cámara MP, 5G, etc.).

    Los valores `None` representan 'No disponible' — el comparador los
    mostrará explícitamente en vez de inventarlos."""

    # Acepta "5000 mAh", "5,000 mAh", "5.000 mAh"
    _RX_BATERIA = re.compile(r"(\d{1,3}(?:[.,]\d{3})?|\d{3,5})\s*mAh\b", re.IGNORECASE)
    _RX_CAMARA_PRINCIPAL = re.compile(r"(\d{1,3})\s*MP\b", re.IGNORECASE)

    _MIN_BATERIA_MAH = 500   # bajo este umbral el regex probablemente matcheó algo espurio
    _MIN_CAMARA_MP = 2
    _RX_CAMARA_FRONTAL_CONTEXTO = re.compile(r"(?:selfie|frontal|front)", re.IGNORECASE)
    _RX_MP_NUMERO = re.compile(r"(\d{1,3})\s*MP", re.IGNORECASE)
    _RX_5G = re.compile(r"\b5\s?G\b", re.IGNORECASE)
    _RX_REFRESH = re.compile(r"(\d{2,3})\s*Hz\b", re.IGNORECASE)
    _RX_SO = re.compile(r"\b(android|ios|windows|webos|linux|wear\s*os|tizen)\b", re.IGNORECASE)

    @classmethod
    def extraer(cls, p: Producto) -> dict[str, object]:
        texto = f"{p.nombre} {p.descripcion or ''}"
        return {
            # base estructurada
            "sku": str(p.sku),
            "nombre": p.nombre,
            "marca": p.marca,
            "categoria": p.categoria,
            "subcategoria": p.subcategoria,
            "precio_bob": float(p.precio.monto),
            "precio_anterior_bob": float(p.precio_anterior.monto) if p.precio_anterior else None,
            "stock": p.stock,
            "color": p.color,
            # specs estructuradas
            "pulgadas": p.pulgadas,
            "ram_gb": p.ram_gb,
            "almacenamiento_gb": p.capacidad_gb,
            "capacidad_litros": p.capacidad_litros,
            "capacidad_kg": p.capacidad_kg,
            "potencia_w": p.potencia_w,
            "procesador": p.procesador,
            "tipo_panel": p.tipo_panel,
            "resolucion": p.resolucion,
            "es_electrico": p.es_electrico,
            # specs con fallback: columna estructurada > regex sobre nombre+desc
            "bateria_mah": p.bateria_mah if p.bateria_mah is not None
                else cls._validar_minimo(
                    cls._primer_match_int(cls._RX_BATERIA, texto), cls._MIN_BATERIA_MAH
                ),
            "camara_mp": p.camara_mp if p.camara_mp is not None
                else cls._validar_minimo(
                    cls._primer_match_int(cls._RX_CAMARA_PRINCIPAL, texto), cls._MIN_CAMARA_MP
                ),
            "camara_frontal_mp": p.camara_frontal_mp if p.camara_frontal_mp is not None
                else cls._validar_minimo(cls._camara_frontal(texto), cls._MIN_CAMARA_MP),
            "soporta_5g": p.soporta_5g if p.soporta_5g is not None
                else cls._detecta_5g(texto),
            "refresh_hz": p.refresh_hz if p.refresh_hz is not None
                else cls._primer_match_int(cls._RX_REFRESH, texto),
            "sistema_operativo": p.sistema_operativo
                if p.sistema_operativo is not None
                else cls._primer_match_str(cls._RX_SO, texto),
            "gpu": p.gpu,
        }

    @classmethod
    def _detecta_5g(cls, texto: str) -> bool:
        return bool(cls._RX_5G.search(texto))

    @staticmethod
    def _validar_minimo(valor: Optional[int], minimo: int) -> Optional[int]:
        if valor is None or valor < minimo:
            return None
        return valor

    @staticmethod
    def _primer_match_int(rx: re.Pattern, texto: str) -> Optional[int]:
        m = rx.search(texto)
        if not m:
            return None
        raw = m.group(1).replace(",", "").replace(".", "")
        try:
            return int(raw)
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _primer_match_str(rx: re.Pattern, texto: str) -> Optional[str]:
        m = rx.search(texto)
        if not m:
            return None
        return m.group(1).lower()

    @classmethod
    def _camara_frontal(cls, texto: str) -> Optional[int]:
        """Busca un 'N MP' dentro de 40 chars de una palabra como 'selfie',
        'frontal' o 'front'. Más simple y legible que una única regex con
        alternativas — y mismo resultado."""
        for contexto_match in cls._RX_CAMARA_FRONTAL_CONTEXTO.finditer(texto):
            inicio = max(0, contexto_match.start() - 40)
            fin = min(len(texto), contexto_match.end() + 40)
            ventana = texto[inicio:fin]
            mp_match = cls._RX_MP_NUMERO.search(ventana)
            if mp_match:
                try:
                    return int(mp_match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
