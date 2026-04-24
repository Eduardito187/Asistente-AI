from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from ...domain.shared.errors import DomainError
from ...domain.shared.normalizacion import NormalizadorTexto
from ...domain.shared.tokens_consulta import TokensConsulta
from ..commands.agregar_al_carrito import AgregarAlCarritoCommand, AgregarAlCarritoHandler
from ..commands.confirmar_orden import ConfirmarOrdenCommand, ConfirmarOrdenHandler
from ..commands.quitar_del_carrito import QuitarDelCarritoCommand, QuitarDelCarritoHandler
from ..commands.vaciar_carrito import VaciarCarritoCommand, VaciarCarritoHandler
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.comparar_productos import CompararProductosHandler, CompararProductosQuery
from ..queries.listar_categorias import ListarCategoriasHandler, ListarCategoriasQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
)
from ..queries.ver_carrito import VerCarritoHandler, VerCarritoQuery
from ..queries.ver_ordenes_sesion import VerOrdenesSesionHandler, VerOrdenesSesionQuery
from ..queries.ver_producto import VerProductoHandler, VerProductoQuery
from ..services.buscador_semantico import BuscadorSemantico
from ..services.clasificador_etapa_conversacional import ClasificadorEtapaConversacional
from ..services.detector_consulta_accesorio import DetectorConsultaAccesorio
from ..services.detector_exclusiones_mensaje import DetectorExclusionesMensaje
from ..services.generador_justificacion import GeneradorJustificacion
from ..services.reranker_por_perfil import ReRankerPorPerfil
from ..services.sanitizador_query_busqueda import SanitizadorQueryBusqueda
from ..services.sugeridor_accesorios_relacionados import SugeridorAccesoriosRelacionados
from ..services.umbrales_tier import UmbralesTier
from .helpers import ValueParser
from .serializers import CarritoSerializer, OrdenSerializer, ProductoSerializer
from .validador_filtros_duros import ValidadorFiltrosDuros

log = logging.getLogger("tool_dispatcher")


@dataclass
class ToolDispatcher:
    """Traduce llamadas de herramientas del LLM a commands/queries. Un solo motivo de cambio: el catalogo de tools."""

    buscar: BuscarProductosHandler
    listar_cats: ListarCategoriasHandler
    ver_prod: VerProductoHandler
    ver_carrito: VerCarritoHandler
    ver_ordenes: VerOrdenesSesionHandler
    agregar: AgregarAlCarritoHandler
    quitar: QuitarDelCarritoHandler
    vaciar: VaciarCarritoHandler
    confirmar: ConfirmarOrdenHandler
    comparar: CompararProductosHandler
    obtener_perfil: ObtenerPerfilSesionHandler
    buscador_semantico: BuscadorSemantico
    reranker: ReRankerPorPerfil

    MIN_RESULTADOS_FULLTEXT = 3

    _TOOLS_TRANSACCIONALES = frozenset({"agregar_al_carrito", "confirmar_orden"})

    def ejecutar(
        self,
        nombre: str,
        args: dict,
        sesion_id: UUID,
        marca_indiferente: bool = False,
        mensaje_usuario: str = "",
        trace_actual: list | None = None,
    ) -> dict:
        handler = self._ruta(nombre)
        if handler is None:
            return {"error": f"herramienta desconocida: {nombre}"}
        if nombre in self._TOOLS_TRANSACCIONALES:
            gate = self._gate_transaccional(mensaje_usuario, sesion_id, trace_actual or [])
            if gate is not None:
                return gate
        try:
            if nombre == "buscar_productos":
                return self._buscar(
                    args,
                    sesion_id,
                    marca_indiferente=marca_indiferente,
                    mensaje_usuario=mensaje_usuario,
                )
            return handler(args, sesion_id)
        except DomainError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            log.exception("tool %s fallo", nombre)
            return {"error": str(exc)}

    def _gate_transaccional(
        self, mensaje: str, sesion_id: UUID, trace: list
    ) -> dict | None:
        """Bloquea agregar_al_carrito / confirmar_orden si la etapa no es de
        compra y el cliente no dio señal explícita. Devuelve dict de error
        que el LLM ve como tool result (no excepción), así el LLM ajusta la
        respuesta sin romper el flujo."""
        perfil = self.obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        etapa = ClasificadorEtapaConversacional.clasificar(mensaje, perfil, trace)
        if ClasificadorEtapaConversacional.permite_transaccion(etapa, mensaje):
            return None
        return {
            "error": (
                f"accion transaccional bloqueada en etapa '{etapa.value}'. "
                f"El cliente todavia esta en modo asesor — no uso el carrito "
                f"hasta que diga explicitamente 'lo llevo' / 'agregalo' / "
                f"'quiero comprarlo'. Seguinos conversando."
            ),
            "etapa": etapa.value,
        }

    def _ruta(self, nombre: str) -> Callable[[dict, UUID], dict] | None:
        return {
            "buscar_productos": self._buscar,
            "listar_categorias": self._listar_cats,
            "ver_producto": self._ver_prod,
            "ver_carrito": self._ver_carrito,
            "ver_ordenes_sesion": self._ver_ordenes,
            "agregar_al_carrito": self._agregar,
            "quitar_del_carrito": self._quitar,
            "vaciar_carrito": self._vaciar,
            "confirmar_orden": self._confirmar,
            "comparar_productos": self._comparar,
        }.get(nombre)

    def _buscar(
        self,
        a: dict,
        sid: UUID,
        *,
        marca_indiferente: bool = False,
        mensaje_usuario: str = "",
    ) -> dict:
        perfil = self.obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sid))
        filtros = self._filtros_enriquecidos(a, perfil, marca_indiferente=marca_indiferente)
        exclusiones = DetectorExclusionesMensaje.detectar(mensaje_usuario)
        if exclusiones:
            filtros["nombre_excluye"] = tuple(exclusiones)
        tipos_excluir = DetectorExclusionesMensaje.tipos_a_excluir(mensaje_usuario)
        if tipos_excluir:
            filtros["tipo_producto_excluye"] = tuple(tipos_excluir)
        if self._filtros_vacios(filtros):
            return {
                "error": (
                    "buscar_productos necesita un termino real del producto. El `query` recibido "
                    "no contiene palabras utiles (solo stopwords como 'dame', 'opciones', 'quiero'). "
                    "Re-invoca con el nombre del producto: query='laptop', query='freidora', "
                    "query='iphone'. O usa `categoria`/`marca`/`precio_max`."
                ),
                "productos": [],
                "total": 0,
            }
        es_accesorio = DetectorConsultaAccesorio.es_consulta_accesorio(
            filtros.get("query"), filtros.get("categoria"), filtros.get("subcategoria")
        )
        filtros["excluir_accesorios"] = not es_accesorio
        self._aplicar_tier_filtros(filtros, perfil)
        log.info(
            "buscar_productos intent=%s tier=%s sku_foco=%s filtros=%s",
            "exact" if perfil.sku_foco else "busqueda",
            perfil.desired_tier,
            perfil.sku_foco,
            {k: v for k, v in filtros.items() if v and k not in ("query", "solo_con_stock")},
        )
        productos = self.buscar.ejecutar(BuscarProductosQuery(**filtros))
        genero_sin_resultados = bool(filtros.get("genero")) and not productos
        if genero_sin_resultados:
            filtros_sin_genero = {**filtros, "genero": None}
            productos = self.buscar.ejecutar(BuscarProductosQuery(**filtros_sin_genero))
        if filtros["query"] and len(productos) < self.MIN_RESULTADOS_FULLTEXT:
            productos = self._agregar_candidatos_semanticos(filtros["query"], productos)
        productos = [p for p in productos if ValidadorFiltrosDuros.cumple(p, filtros)]
        productos = self._fallback_sin_query(productos, filtros)
        productos = self.reranker.reordenar(
            list(productos), perfil, marca_indiferente=marca_indiferente
        )
        productos = self._prepend_producto_foco(productos, perfil.sku_foco)
        log.info("buscar_productos count_final=%d", len(productos))
        descontinuados = [p for p in productos if getattr(p, "es_descontinuado", False)]
        productos_web = [p for p in productos if not getattr(p, "es_descontinuado", False)]
        sugeridos = self._cross_sell_accesorios(filtros, productos_web) if not es_accesorio else []
        respuesta = {
            "productos": [self._proyectar(p, perfil) for p in productos_web],
            "total": len(productos_web),
            "sugeridos": [self._proyectar(p, perfil) for p in sugeridos],
        }
        if perfil.sku_foco and productos_web and str(productos_web[0].sku) == perfil.sku_foco:
            respuesta["producto_foco_sku"] = perfil.sku_foco
        if genero_sin_resultados:
            respuesta["aviso_sin_metadata_genero"] = (
                f"El catalogo no marca productos por genero '{filtros.get('genero')}' "
                f"en esta subcategoria. Estos son los modelos disponibles sin distincion "
                f"de genero — comunicalo asi al cliente con honestidad."
            )
        if descontinuados:
            respuesta["tienda_fisica"] = (
                "Este producto ya no está disponible para compra online. "
                "Para adquirirlo debés acercarte a una tienda física Dismac."
            )
        return respuesta

    def _fallback_sin_query(self, productos: list, filtros: dict) -> list:
        """Si el LLM mando la oracion entera como `query` (ej. 'un reloj para
        ponerme en la mano') el FULLTEXT no matchea y devuelve 0. Cuando
        tenemos `categoria` o `subcategoria` resueltas, el query verbose solo
        agrega ruido — relanzamos la busqueda sin query. Evita falso positivo
        de 'no lo tenemos tal cual' en ManejadorProductoAusente."""
        if productos:
            return productos
        if not filtros.get("query"):
            return productos
        if not (filtros.get("categoria") or filtros.get("subcategoria")):
            return productos
        filtros_sin_query = {**filtros, "query": None}
        return self.buscar.ejecutar(BuscarProductosQuery(**filtros_sin_query))

    def _prepend_producto_foco(self, productos: list, sku_foco: str | None) -> list:
        """Si el cliente mencionó un modelo específico (ej. 's26 ultra' resuelto
        a sku_foco), ese SKU va primero. Si ya viene en la lista, lo movemos
        arriba; si no, lo vamos a buscar y lo insertamos como principal."""
        if not sku_foco:
            return productos
        por_sku = {str(p.sku): p for p in productos}
        if sku_foco in por_sku:
            foco = por_sku[sku_foco]
            rest = [p for p in productos if str(p.sku) != sku_foco]
            return [foco, *rest]
        try:
            obtener_res = self.ver_prod.ejecutar(VerProductoQuery(sku=sku_foco))
        except Exception:
            return productos
        if obtener_res is None or obtener_res.producto is None:
            return productos
        return [obtener_res.producto, *productos]

    def _aplicar_tier_filtros(self, filtros: dict, perfil) -> None:
        """Convierte `perfil.desired_tier` en piso/techo de precio. Si hay
        `sku_foco`, su precio se usa como ancla y, si no hay tier explícito,
        se infiere del propio foco (ej. S26 Ultra a Bs 18.699 en Smartphones
        → 'flagship'). Respeta `precio_min`/`precio_max` ya en filtros:
        solo sube el piso o baja el techo si el tier es más restrictivo."""
        subcat = filtros.get("subcategoria") or getattr(perfil, "subcategoria_foco", None)
        precio_foco, subcat = self._foco_ancla(perfil, subcat)
        tier = getattr(perfil, "desired_tier", None) or (
            UmbralesTier.tier_de(precio_foco, subcat) if precio_foco else None
        )
        if not tier:
            return
        precio_ancla = precio_foco if precio_foco is not None else filtros.get("precio_max")
        piso, techo = UmbralesTier.rango(tier=tier, subcategoria=subcat, precio_ancla=precio_ancla)
        if piso is not None:
            previo = filtros.get("precio_min")
            filtros["precio_min"] = max(piso, previo or 0.0) or None
        if techo is not None:
            previo = filtros.get("precio_max")
            filtros["precio_max"] = min(techo, previo) if previo is not None else techo

    def _foco_ancla(self, perfil, subcat_base: str | None) -> tuple[float | None, str | None]:
        """Resuelve el producto foco y devuelve (precio, subcategoria_resuelta).
        Devuelve (None, subcat_base) si no hay sku_foco o la tool falla."""
        sku_foco = getattr(perfil, "sku_foco", None)
        if not sku_foco:
            return None, subcat_base
        try:
            res = self.ver_prod.ejecutar(VerProductoQuery(sku=sku_foco))
        except Exception:
            return None, subcat_base
        if not res or not res.producto:
            return None, subcat_base
        return float(res.producto.precio.monto), subcat_base or res.producto.subcategoria

    def _cross_sell_accesorios(self, filtros: dict, principales: list) -> list:
        sugeridor = SugeridorAccesoriosRelacionados(self.buscar)
        return sugeridor.sugerir(
            principales,
            categoria=filtros.get("categoria"),
            subcategoria=filtros.get("subcategoria"),
        )

    @staticmethod
    def _proyectar(p, perfil) -> dict:
        base = ProductoSerializer.resumen(p)
        justificacion = GeneradorJustificacion.para(p, perfil)
        if justificacion:
            base["justificacion"] = justificacion
        return base

    _CAMPOS_ESTRUCTURADOS = (
        "categoria", "subcategoria", "marca",
        "pulgadas", "pulgadas_min", "pulgadas_max",
        "capacidad_gb_min", "ram_gb_min",
        "capacidad_litros_min", "capacidad_kg_min",
        "potencia_w_min", "potencia_w_max", "procesador",
        "tipo_panel", "resolucion", "color", "es_electrico",
    )

    @classmethod
    def _filtros_enriquecidos(cls, a: dict, perfil, *, marca_indiferente: bool = False) -> dict:
        marca_arg = cls._texto(a, "marca")
        marca_final = marca_arg if marca_indiferente else (marca_arg or perfil.marca_preferida or None)
        return {
            "query": SanitizadorQueryBusqueda.sanitizar(cls._texto(a, "query")),
            "categoria": cls._texto(a, "categoria") or perfil.categoria_efectiva() or None,
            "subcategoria": cls._texto(a, "subcategoria") or perfil.subcategoria_efectiva() or None,
            "marca": marca_final,
            "precio_min": ValueParser.a_float(a.get("precio_min")),
            "precio_max": cls._precio_max(a, perfil),
            "pulgadas": ValueParser.a_float(a.get("pulgadas")) or perfil.pulgadas,
            "pulgadas_min": ValueParser.a_float(a.get("pulgadas_min")),
            "pulgadas_max": ValueParser.a_float(a.get("pulgadas_max")),
            "capacidad_gb_min": ValueParser.a_int(a.get("capacidad_gb_min")),
            "ram_gb_min": ValueParser.a_int(a.get("ram_gb_min")),
            "capacidad_litros_min": ValueParser.a_float(a.get("capacidad_litros_min")),
            "capacidad_kg_min": ValueParser.a_float(a.get("capacidad_kg_min")),
            "potencia_w_min": ValueParser.a_int(a.get("potencia_w_min")),
            "potencia_w_max": ValueParser.a_int(a.get("potencia_w_max")),
            "procesador": cls._texto(a, "procesador", transform=str.lower),
            "tipo_panel": cls._texto(a, "tipo_panel", transform=str.upper) or perfil.tipo_panel,
            "resolucion": cls._texto(a, "resolucion", transform=str.upper) or perfil.resolucion,
            "color": cls._texto(a, "color", transform=str.lower),
            "es_electrico": ValueParser.a_bool(a.get("es_electrico")),
            "genero": cls._texto(a, "genero", transform=str.lower) or perfil.genero_declarado or None,
            "solo_con_stock": True,
        }

    @staticmethod
    def _texto(a: dict, clave: str, transform=None) -> str | None:
        valor = (a.get(clave) or "").strip()
        if not valor:
            return None
        return transform(valor) if transform else valor

    @staticmethod
    def _precio_max(a: dict, perfil) -> float | None:
        explicito = ValueParser.a_float(a.get("precio_max"))
        return explicito if explicito is not None else (perfil.presupuesto_max or None)

    @classmethod
    def _filtros_vacios(cls, filtros: dict) -> bool:
        query = filtros.get("query") or ""
        query_utiles = TokensConsulta.hay_terminos(NormalizadorTexto.normalizar(query)) if query else False
        estructurados = any(filtros.get(k) for k in cls._CAMPOS_ESTRUCTURADOS)
        return not query_utiles and not estructurados

    def _agregar_candidatos_semanticos(self, query: str, base: list) -> list:
        """Incorpora candidatos semanticos a la lista base sin filtrar aqui.

        El filtrado por atributos duros se hace una sola vez, afuera, contra
        toda la lista final — asi el criterio es uniforme para cualquier fuente
        (fulltext o semantica) y no se degrada a un parche por caso."""
        skus_semantica = self.buscador_semantico.buscar_skus(query)
        if not skus_semantica:
            return base
        vistos = {str(p.sku) for p in base}
        extras = [s for s in skus_semantica if s not in vistos]
        if not extras:
            return base
        try:
            resultado = self.comparar.ejecutar(CompararProductosQuery(skus=tuple(extras)))
        except Exception:
            return base
        return list(base) + list(resultado.productos)

    def _listar_cats(self, _a: dict, _sid: UUID) -> dict:
        return {"categorias": self.listar_cats.ejecutar(ListarCategoriasQuery())}

    def _ver_prod(self, a: dict, _sid: UUID) -> dict:
        res = self.ver_prod.ejecutar(VerProductoQuery(sku=a.get("sku", "")))
        if res.producto is None:
            return {
                "error": f"SKU {a.get('sku')} no encontrado",
                "skus_similares_en_catalogo": res.skus_similares,
            }
        return ProductoSerializer.detalle(res.producto)

    def _ver_carrito(self, _a: dict, sid: UUID) -> dict:
        return CarritoSerializer.a_dict(self.ver_carrito.ejecutar(VerCarritoQuery(sesion_id=sid)))

    def _ver_ordenes(self, _a: dict, sid: UUID) -> dict:
        ordenes = self.ver_ordenes.ejecutar(VerOrdenesSesionQuery(sesion_id=sid))
        return {"ordenes": [OrdenSerializer.a_dict(o) for o in ordenes]}

    def _agregar(self, a: dict, sid: UUID) -> dict:
        res = self.agregar.ejecutar(
            AgregarAlCarritoCommand(sesion_id=sid, sku=a.get("sku", ""), cantidad=int(a.get("cantidad") or 1))
        )
        return {
            "ok": True,
            "sku": res.sku,
            "nombre": res.nombre,
            "cantidad_agregada": res.cantidad_agregada,
            "precio_unitario_bob": res.precio_unitario_bob,
        }

    def _quitar(self, a: dict, sid: UUID) -> dict:
        self.quitar.ejecutar(QuitarDelCarritoCommand(sesion_id=sid, sku=a.get("sku", "")))
        return {"ok": True, "sku": a.get("sku")}

    def _vaciar(self, _a: dict, sid: UUID) -> dict:
        self.vaciar.ejecutar(VaciarCarritoCommand(sesion_id=sid))
        return {"ok": True}

    def _confirmar(self, a: dict, sid: UUID) -> dict:
        res = self.confirmar.ejecutar(
            ConfirmarOrdenCommand(
                sesion_id=sid,
                cliente_nombre=a.get("cliente_nombre", ""),
                cliente_email=a.get("cliente_email"),
                cliente_telefono=a.get("cliente_telefono"),
                notas=a.get("notas"),
            )
        )
        return {
            "ok": True,
            "numero_orden": res.numero_orden,
            "orden_id": res.orden_id,
            "total_bob": res.total_bob,
            "items_cantidad": res.items_cantidad,
            "cliente_nombre": res.cliente_nombre,
            "cliente_email": res.cliente_email,
            "cliente_telefono": res.cliente_telefono,
        }

    def _comparar(self, a: dict, _sid: UUID) -> dict:
        skus_arg = a.get("skus") or []
        if isinstance(skus_arg, str):
            skus_arg = [s.strip() for s in skus_arg.split(",") if s.strip()]
        resultado = self.comparar.ejecutar(CompararProductosQuery(skus=tuple(skus_arg)))
        # La tabla + conclusión ya vienen armadas por ComparadorProductos.
        # El LLM solo debe renderizar, no recalcular.
        salida: dict = {
            "productos": [ProductoSerializer.resumen(p) for p in resultado.productos],
            "tabla": resultado.tabla,
            "conclusion": resultado.conclusion,
        }
        if resultado.skus_no_encontrados:
            salida["skus_no_encontrados"] = resultado.skus_no_encontrados
        return salida
