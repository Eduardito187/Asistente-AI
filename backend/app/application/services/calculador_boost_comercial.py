from __future__ import annotations

from ...domain.productos import Producto

BOOST_PANEL_TOP = 1.4
BOOST_PANEL_PREMIUM = 1.2
BOOST_PANEL_MEDIO = 0.6
BOOST_RESOLUCION_4K_8K = 0.8
BOOST_SMART_TV = 0.7
BOOST_OFERTA = 0.5

PANEL_TOP = ("OLED",)
PANEL_PREMIUM = ("MINILED", "QLED")
PANEL_MEDIO = ("NANOCELL",)

RESOLUCION_ALTA = ("8K", "4K")

PALABRAS_SMART_TV = (
    "google tv", "android tv", "androidtv", "googletv",
    "webos", "tizen", "smart tv", "smarttv",
)


class CalculadorBoostComercial:
    """Boost independiente del perfil del cliente: prioriza productos con
    mejor ticket promedio, mejor panel, smart features y ofertas activas.

    Se combina con CalculadorBoostPerfil. La idea es que, entre dos opciones
    que cumplen el filtro duro por igual, el ranking elija la que tiene mas
    valor comercial (QLED sobre LED, 4K sobre FHD, con Smart TV sobre no-smart,
    con descuento activo sobre precio lleno).

    No mira la marca — la decision por marca ya la maneja el boost de perfil
    o queda neutral si el cliente declaro 'marca indiferente'."""

    @classmethod
    def score(cls, producto: Producto) -> float:
        return (
            cls._boost_panel(producto)
            + cls._boost_resolucion(producto)
            + cls._boost_smart_tv(producto)
            + cls._boost_oferta(producto)
        )

    @staticmethod
    def _boost_panel(p: Producto) -> float:
        panel = (p.tipo_panel or "").upper()
        if not panel:
            return 0.0
        if panel in PANEL_TOP:
            return BOOST_PANEL_TOP
        if panel in PANEL_PREMIUM:
            return BOOST_PANEL_PREMIUM
        if panel in PANEL_MEDIO:
            return BOOST_PANEL_MEDIO
        return 0.0

    @staticmethod
    def _boost_resolucion(p: Producto) -> float:
        resolucion = (p.resolucion or "").upper()
        return BOOST_RESOLUCION_4K_8K if resolucion in RESOLUCION_ALTA else 0.0

    @staticmethod
    def _boost_smart_tv(p: Producto) -> float:
        texto = f"{p.nombre} {p.descripcion or ''}".lower()
        return BOOST_SMART_TV if any(k in texto for k in PALABRAS_SMART_TV) else 0.0

    @staticmethod
    def _boost_oferta(p: Producto) -> float:
        if p.precio_anterior is None:
            return 0.0
        return BOOST_OFERTA if p.precio_anterior.monto > p.precio.monto else 0.0
