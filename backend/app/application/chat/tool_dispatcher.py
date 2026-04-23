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
from ..services.detector_consulta_accesorio import DetectorConsultaAccesorio
from ..services.generador_justificacion import GeneradorJustificacion
from ..services.reranker_por_perfil import ReRankerPorPerfil
from ..services.sanitizador_query_busqueda import SanitizadorQueryBusqueda
from ..services.sugeridor_accesorios_relacionados import SugeridorAccesoriosRelacionados
from .helpers import ValueParser
from .serializers import CarritoSerializer, ComparacionSerializer, OrdenSerializer, ProductoSerializer
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

    def ejecutar(
        self,
        nombre: str,
        args: dict,
        sesion_id: UUID,
        marca_indiferente: bool = False,
    ) -> dict:
        handler = self._ruta(nombre)
        if handler is None:
            return {"error": f"herramienta desconocida: {nombre}"}
        try:
            if nombre == "buscar_productos":
                return self._buscar(args, sesion_id, marca_indiferente=marca_indiferente)
            return handler(args, sesion_id)
        except DomainError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            log.exception("tool %s fallo", nombre)
            return {"error": str(exc)}

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

    def _buscar(self, a: dict, sid: UUID, *, marca_indiferente: bool = False) -> dict:
        perfil = self.obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sid))
        filtros = self._filtros_enriquecidos(a, perfil, marca_indiferente=marca_indiferente)
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
        productos = self.buscar.ejecutar(BuscarProductosQuery(**filtros))
        genero_sin_resultados = bool(filtros.get("genero")) and not productos
        if genero_sin_resultados:
            filtros_sin_genero = {**filtros, "genero": None}
            productos = self.buscar.ejecutar(BuscarProductosQuery(**filtros_sin_genero))
        if filtros["query"] and len(productos) < self.MIN_RESULTADOS_FULLTEXT:
            productos = self._agregar_candidatos_semanticos(filtros["query"], productos)
        productos = [p for p in productos if ValidadorFiltrosDuros.cumple(p, filtros)]
        productos = self.reranker.reordenar(
            list(productos), perfil, marca_indiferente=marca_indiferente
        )
        sugeridos = self._cross_sell_accesorios(filtros, productos) if not es_accesorio else []
        respuesta = {
            "productos": [self._proyectar(p, perfil) for p in productos],
            "total": len(productos),
            "sugeridos": [self._proyectar(p, perfil) for p in sugeridos],
        }
        if genero_sin_resultados:
            respuesta["aviso_sin_metadata_genero"] = (
                f"El catalogo no marca productos por genero '{filtros.get('genero')}' "
                f"en esta subcategoria. Estos son los modelos disponibles sin distincion "
                f"de genero — comunicalo asi al cliente con honestidad."
            )
        return respuesta

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
        salida = ComparacionSerializer.a_dict(resultado.productos)
        if resultado.skus_no_encontrados:
            salida["skus_no_encontrados"] = resultado.skus_no_encontrados
        return salida
