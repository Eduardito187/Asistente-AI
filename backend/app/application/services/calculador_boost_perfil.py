from __future__ import annotations

import re

from ...domain.productos import Producto
from ..queries.obtener_perfil_sesion import ResultadoObtenerPerfilSesion

BOOST_MARCA = 3.0
BOOST_CATEGORIA = 2.0
BOOST_USO = 1.5
BOOST_DENTRO_PRESUPUESTO = 1.0
PENALIZACION_FUERA_PRESUPUESTO = 5.0

PALABRAS_CLAVE_USO: dict[str, tuple[str, ...]] = {
    "gaming": ("gaming", "gamer", "rtx", "gtx", "rog", "tuf", "nvidia", "geforce", "legion", "helios", "predator", "nitro", "alienware", "fps", "moba"),
    "oficina": ("oficina", "office", "trabajo", "empresarial", "corporate", "excel", "word", "powerpoint", "teams"),
    "estudio": ("estudiante", "estudio", "universitario", "escolar", "colegio", "universidad", "tarea", "clase"),
    "diseno": ("diseño", "diseno", "editor", "creador", "4k", "retina", "adobe", "photoshop", "illustrator", "render", "renderizado", "colorimetria", "pantone"),
    "cocina": ("cocina", "cocinar", "horno", "freidora", "licuadora", "blender", "microondas", "tostadora"),
    "hogar": ("hogar", "sala", "dormitorio", "familia", "casa", "living", "habitacion"),
    "streaming": ("streaming", "netflix", "youtube", "twitch", "contenido", "stream", "transmision"),
    "programacion": ("programacion", "programar", "codigo", "developer", "python", "javascript", "ide", "terminal", "compilar"),
    "fotografia": ("fotografia", "foto", "camara", "disparo", "lente", "raw", "lightroom"),
    "musica": ("musica", "audio", "auriculares", "altavoz", "sonido", "dj", "mezcla", "estudio grabacion"),
    "viaje": ("viaje", "viajero", "portatil", "avion", "mochila", "liviano", "compacto"),
}


class CalculadorBoostPerfil:
    """SRP: calcular cuanto sube o baja un producto segun el perfil declarado."""

    @classmethod
    def score(
        cls,
        producto: Producto,
        perfil: ResultadoObtenerPerfilSesion,
        *,
        marca_indiferente: bool = False,
    ) -> float:
        if perfil.esta_vacio():
            return 0.0
        marca_score = 0.0 if marca_indiferente else cls._boost_marca(producto, perfil.marca_preferida)
        return (
            marca_score
            + cls._boost_categoria(producto, perfil.categoria_foco)
            + cls._boost_uso(producto, perfil.uso_declarado)
            + cls._ajuste_presupuesto(producto, perfil.presupuesto_max)
        )

    @staticmethod
    def _boost_marca(p: Producto, marca_pref: str | None) -> float:
        if not marca_pref or not p.marca:
            return 0.0
        return BOOST_MARCA if marca_pref.lower() == p.marca.lower() else 0.0

    @staticmethod
    def _boost_categoria(p: Producto, cat_foco: str | None) -> float:
        if not cat_foco or not p.categoria:
            return 0.0
        return BOOST_CATEGORIA if cat_foco.lower() in p.categoria.lower() else 0.0

    @classmethod
    def _boost_uso(cls, p: Producto, uso: str | None) -> float:
        if not uso:
            return 0.0
        claves = PALABRAS_CLAVE_USO.get(uso.lower(), ())
        if not claves:
            return 0.0
        texto = f"{p.nombre} {p.descripcion or ''}".lower()
        return BOOST_USO if any(re.search(rf"\b{re.escape(k)}\b", texto) for k in claves) else 0.0

    @staticmethod
    def _ajuste_presupuesto(p: Producto, presupuesto: float | None) -> float:
        if not presupuesto:
            return 0.0
        if p.precio.monto <= presupuesto:
            return BOOST_DENTRO_PRESUPUESTO
        return -PENALIZACION_FUERA_PRESUPUESTO
