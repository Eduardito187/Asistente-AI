from __future__ import annotations

import logging

from ..chat.serializers import ProductoSerializer
from ..commands.registrar_sugerencia_catalogo import (
    RegistrarSugerenciaCatalogoCommand,
    RegistrarSugerenciaCatalogoHandler,
)
from .respuesta_producto_ausente import RespuestaProductoAusente
from .sugeridor_productos_alternativos import SugeridorProductosAlternativos
from .validador_producto_real import ValidadorProductoReal

log = logging.getLogger("manejador_producto_ausente")


class ManejadorProductoAusente:
    """SRP: orquestar el caso 'cliente pide algo que no esta en catalogo'.
    Valida con IA si el pedido es un producto real, guarda silenciosamente la
    sugerencia si corresponde y ofrece alternativas similares."""

    TXT_NO_HAY_SIMILARES = (
        "Lo siento, de momento no tenemos productos similares a lo que buscas. "
        "Si me das un poco mas de detalle (categoria, marca o para que lo "
        "necesitas), busco con otro enfoque."
    )

    def __init__(
        self,
        validador: ValidadorProductoReal,
        sugeridor: SugeridorProductosAlternativos,
        registrar_sugerencia: RegistrarSugerenciaCatalogoHandler,
    ) -> None:
        self._validador = validador
        self._sugeridor = sugeridor
        self._registrar = registrar_sugerencia

    async def manejar(
        self,
        texto_cliente: str,
        contexto_conversacion: str | None = None,
        categoria_activa: str | None = None,
    ) -> RespuestaProductoAusente:
        validacion = await self._validador.validar(texto_cliente)

        sugerencia_registrada = False
        if validacion.es_real and validacion.nombre_canonico:
            try:
                res = self._registrar.ejecutar(
                    RegistrarSugerenciaCatalogoCommand(
                        nombre=validacion.nombre_canonico,
                        categoria_estimada=validacion.categoria,
                        marca_estimada=validacion.marca,
                        contexto_cliente=(contexto_conversacion or texto_cliente)[:2000],
                    )
                )
                sugerencia_registrada = bool(res.sugerencia_id)
            except Exception as exc:
                log.warning("no se pudo registrar sugerencia: %s", exc)

        categoria_para_buscar = categoria_activa or validacion.categoria
        marca_para_buscar = None if categoria_activa else validacion.marca
        nombre_para_buscar = None if categoria_activa else validacion.nombre_canonico
        alternativas = self._sugeridor.sugerir(
            categoria=categoria_para_buscar,
            marca=marca_para_buscar,
            nombre_canonico=nombre_para_buscar,
        )

        if not alternativas:
            return RespuestaProductoAusente(
                texto=self.TXT_NO_HAY_SIMILARES,
                productos_alternativos=[],
                skus_alternativos=[],
                sugerencia_registrada=sugerencia_registrada,
            )

        texto = self._armar_texto_con_alternativas(
            nombre_pedido=validacion.nombre_canonico or texto_cliente.strip(),
            es_producto_real=validacion.es_real,
            alternativas_resumen=[ProductoSerializer.resumen(p) for p in alternativas],
        )
        return RespuestaProductoAusente(
            texto=texto,
            productos_alternativos=[ProductoSerializer.resumen(p) for p in alternativas],
            skus_alternativos=[str(p.sku) for p in alternativas],
            sugerencia_registrada=sugerencia_registrada,
        )

    @staticmethod
    def _armar_texto_con_alternativas(
        nombre_pedido: str, es_producto_real: bool, alternativas_resumen: list[dict]
    ) -> str:
        if es_producto_real:
            encabezado = (
                f'Uy, "{nombre_pedido}" ahorita no lo tenemos en el catalogo — '
                "muy pronto posiblemente lo tengamos. Mientras tanto, mira "
                "estas opciones similares que si hay en stock:"
            )
        else:
            encabezado = (
                "Eso exacto no lo tengo en el catalogo, pero encontre estas "
                "opciones parecidas por si te sirven:"
            )
        lineas = [encabezado]
        for p in alternativas_resumen:
            extra = (
                f" (antes Bs {p['precio_anterior_bob']:.0f})"
                if p.get("precio_anterior_bob")
                else ""
            )
            lineas.append(
                f"- {p['nombre']} — Bs {p['precio_bob']:.0f}{extra} [{p['sku']}]"
            )
        lineas.append("¿Te sirve alguna? Si queres te la agrego al carrito.")
        return "\n".join(lineas)
