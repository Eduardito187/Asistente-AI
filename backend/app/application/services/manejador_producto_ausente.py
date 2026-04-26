from __future__ import annotations

import logging

from ..chat.serializers import ProductoSerializer
from ..chat.validador_filtros_duros import ValidadorFiltrosDuros
from ..commands.registrar_sugerencia_catalogo import (
    RegistrarSugerenciaCatalogoCommand,
    RegistrarSugerenciaCatalogoHandler,
)
from .refinamiento_shown import RefinamientoShown
from .resolvedor_categoria_cercana import CategoriaCercana, ResolvedorCategoriaCercana
from .respuesta_producto_ausente import RespuestaProductoAusente
from .sugeridor_productos_alternativos import SugeridorProductosAlternativos
from .validador_producto_real import ValidadorProductoReal

log = logging.getLogger("manejador_producto_ausente")


class ManejadorProductoAusente:
    """SRP: orquestar el caso 'cliente pide algo que no esta en catalogo'.

    Precedencia determinista (prohibe negar categorias que SI existen):
      1. ResolvedorCategoriaCercana: busca sinonimo/relacion en BD antes que nada.
         Si hay match, usamos esa categoria/subcategoria real.
      2. Solo si el resolver no sabe, caemos al ValidadorProductoReal (LLM)
         para decidir si el pedido es un producto real que podamos registrar.
      3. Siempre intentamos buscar alternativas reales antes de decir 'no hay'."""

    TXT_NO_HAY_SIMILARES = (
        "Lo siento, de momento no tenemos productos similares a lo que buscas. "
        "Si me das un poco mas de detalle (categoria, marca o para que lo "
        "necesitas), busco con otro enfoque."
    )

    TXT_NO_HAY_REFINAMIENTO = (
        "De los que te mostre ninguno cumple con {descripcion}, y no encuentro "
        "otros en esa linea con esa caracteristica. Queres que probemos otra "
        "marca o cambiemos el filtro?"
    )

    def __init__(
        self,
        validador: ValidadorProductoReal,
        sugeridor: SugeridorProductosAlternativos,
        registrar_sugerencia: RegistrarSugerenciaCatalogoHandler,
        resolvedor_categoria: ResolvedorCategoriaCercana,
    ) -> None:
        self._validador = validador
        self._sugeridor = sugeridor
        self._registrar = registrar_sugerencia
        self._resolvedor = resolvedor_categoria

    async def manejar(
        self,
        texto_cliente: str,
        contexto_conversacion: str | None = None,
        categoria_activa: str | None = None,
        subcategoria_activa: str | None = None,
        refinamiento: RefinamientoShown | None = None,
        marca_preferida: str | None = None,
        precio_max: float | None = None,
        precio_min: float | None = None,
        nombre_excluye: tuple[str, ...] | None = None,
        tipo_producto_excluye: tuple[str, ...] | None = None,
        marca_excluye: tuple[str, ...] | None = None,
        pulgadas: float | None = None,
    ) -> RespuestaProductoAusente:
        cercana = self._resolvedor.resolver(texto_cliente)
        validacion = None
        sugerencia_registrada = False
        if cercana is None and not categoria_activa:
            validacion, sugerencia_registrada = await self._validar_y_registrar(
                texto_cliente, contexto_conversacion
            )

        filtros = self._elegir_filtros(
            categoria_activa, subcategoria_activa, cercana, validacion,
            marca_preferida=marca_preferida,
        )
        alternativas = self._buscar_alternativas(
            filtros, precio_max=precio_max, precio_min=precio_min,
            nombre_excluye=nombre_excluye, tipo_producto_excluye=tipo_producto_excluye,
            marca_excluye=marca_excluye, pulgadas=pulgadas,
        )
        alternativas = self._aplicar_refinamiento(alternativas, refinamiento)

        if not alternativas:
            texto_vacio = (
                self.TXT_NO_HAY_REFINAMIENTO.format(
                    descripcion=refinamiento.descripcion_humana()
                )
                if refinamiento is not None
                else self.TXT_NO_HAY_SIMILARES
            )
            return RespuestaProductoAusente(
                texto=texto_vacio,
                productos_alternativos=[],
                skus_alternativos=[],
                sugerencia_registrada=sugerencia_registrada,
            )

        razon_falaz = self._razon_promete_marca(cercana) and not self._alguna_alternativa_es_de_marca(
            alternativas, cercana
        )
        texto = self._armar_texto_con_alternativas(
            nombre_pedido=(
                (validacion.nombre_canonico if validacion else None)
                or texto_cliente.strip()
            ),
            es_producto_real=bool(validacion and validacion.es_real),
            cercana=cercana,
            alternativas_resumen=[ProductoSerializer.detalle(p) for p in alternativas],
            razon_falaz=razon_falaz,
            contexto_activo=bool(categoria_activa and cercana is None and validacion is None),
            refinamiento=refinamiento,
        )
        return RespuestaProductoAusente(
            texto=texto,
            productos_alternativos=[ProductoSerializer.detalle(p) for p in alternativas],
            skus_alternativos=[str(p.sku) for p in alternativas],
            sugerencia_registrada=sugerencia_registrada,
            categoria_ofrecida=filtros[0],
            subcategoria_ofrecida=filtros[1],
        )

    async def _validar_y_registrar(
        self, texto_cliente: str, contexto_conversacion: str | None
    ):
        validacion = await self._validador.validar(texto_cliente)
        if not (validacion.es_real and validacion.nombre_canonico):
            return validacion, False
        try:
            res = self._registrar.ejecutar(
                RegistrarSugerenciaCatalogoCommand(
                    nombre=validacion.nombre_canonico,
                    categoria_estimada=validacion.categoria,
                    marca_estimada=validacion.marca,
                    contexto_cliente=(contexto_conversacion or texto_cliente)[:2000],
                )
            )
            return validacion, bool(res.sugerencia_id)
        except Exception as exc:
            log.warning("no se pudo registrar sugerencia: %s", exc)
            return validacion, False

    def _buscar_alternativas(
        self,
        filtros: tuple[str | None, str | None, str | None, str | None],
        precio_max: float | None = None,
        precio_min: float | None = None,
        nombre_excluye: tuple[str, ...] | None = None,
        tipo_producto_excluye: tuple[str, ...] | None = None,
        marca_excluye: tuple[str, ...] | None = None,
        pulgadas: float | None = None,
    ):
        categoria, subcategoria, marca, nombre = filtros
        return self._sugeridor.sugerir(
            categoria=categoria,
            marca=marca,
            nombre_canonico=nombre,
            subcategoria=subcategoria,
            precio_max=precio_max,
            precio_min=precio_min,
            nombre_excluye=nombre_excluye,
            tipo_producto_excluye=tipo_producto_excluye,
            marca_excluye=marca_excluye,
            pulgadas=pulgadas,
        )

    @staticmethod
    def _aplicar_refinamiento(
        alternativas, refinamiento: RefinamientoShown | None
    ):
        """Filtra sugerencias por el atributo pedido ('electricas', 'OLED').
        Honestidad: si el cliente pregunto por X, no le mostremos no-X."""
        if refinamiento is None or refinamiento.vacio():
            return alternativas
        filtros = {
            k: v
            for k, v in (
                ("es_electrico", refinamiento.es_electrico),
                ("tipo_panel", refinamiento.tipo_panel),
                ("resolucion", refinamiento.resolucion),
                ("color", refinamiento.color),
            )
            if v is not None
        }
        return [p for p in alternativas if ValidadorFiltrosDuros.cumple(p, filtros)]

    @staticmethod
    def _elegir_filtros(
        categoria_activa: str | None,
        subcategoria_activa: str | None,
        cercana: CategoriaCercana | None,
        validacion,
        marca_preferida: str | None = None,
    ) -> tuple[str | None, str | None, str | None, str | None]:
        if cercana is not None:
            # Si el cliente declaró una marca (ej. "marca apple"), se prioriza
            # sobre la marca inferida por la relación cross-categoría.
            return (
                cercana.categoria,
                cercana.subcategoria,
                marca_preferida or cercana.marca,
                cercana.palabra_clave,
            )
        if categoria_activa:
            return categoria_activa, subcategoria_activa, marca_preferida, None
        if validacion is not None:
            return (
                validacion.categoria,
                None,
                marca_preferida or validacion.marca,
                validacion.nombre_canonico,
            )
        return None, None, marca_preferida, None

    @staticmethod
    def _alguna_alternativa_es_de_marca(alternativas, cercana: CategoriaCercana | None) -> bool:
        if cercana is None or not cercana.marca:
            return True
        objetivo = cercana.marca.strip().lower()
        return any((p.marca or "").strip().lower() == objetivo for p in alternativas)

    @staticmethod
    def _razon_promete_marca(cercana: CategoriaCercana | None) -> bool:
        if cercana is None or not cercana.marca or not cercana.razon:
            return False
        razon_norm = cercana.razon.lower()
        marca_norm = cercana.marca.lower()
        if marca_norm not in razon_norm:
            return False
        return razon_norm.lstrip().startswith(("tenemos", "hay ", "si tenemos"))

    @staticmethod
    def _armar_texto_con_alternativas(
        nombre_pedido: str,
        es_producto_real: bool,
        cercana: CategoriaCercana | None,
        alternativas_resumen: list[dict],
        razon_falaz: bool = False,
        contexto_activo: bool = False,
        refinamiento: RefinamientoShown | None = None,
    ) -> str:
        if cercana is not None:
            razon_base = cercana.razon or (
                f"lo mas cercano que tenemos es {cercana.subcategoria or cercana.categoria}"
            )
            if razon_falaz and cercana.marca:
                razon = (
                    f"no tenemos {cercana.marca} en esa categoria, pero si otras "
                    f"marcas de {cercana.subcategoria or cercana.categoria}"
                )
            else:
                razon = razon_base
            encabezado = (
                f'"{nombre_pedido}" no lo tenemos tal cual — {razon}. '
                "Mira estas opciones del catalogo:"
            )
        elif contexto_activo:
            if refinamiento is not None and not refinamiento.vacio():
                encabezado = (
                    f"Dentro de esa linea, estas son las {refinamiento.descripcion_humana()}:"
                )
            else:
                encabezado = (
                    "Siguiendo con lo que te mostre, estas son las opciones que "
                    "tengo dentro de esa linea:"
                )
        elif es_producto_real:
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
        return "\n".join(lineas)
