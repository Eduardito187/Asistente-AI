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
from ..queries.listar_categorias import ListarCategoriasHandler, ListarCategoriasQuery
from ..queries.ver_carrito import VerCarritoHandler, VerCarritoQuery
from ..queries.ver_ordenes_sesion import VerOrdenesSesionHandler, VerOrdenesSesionQuery
from ..queries.ver_producto import VerProductoHandler, VerProductoQuery
from .helpers import ValueParser
from .serializers import CarritoSerializer, OrdenSerializer, ProductoSerializer

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

    def ejecutar(self, nombre: str, args: dict, sesion_id: UUID) -> dict:
        handler = self._ruta(nombre)
        if handler is None:
            return {"error": f"herramienta desconocida: {nombre}"}
        try:
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
        }.get(nombre)

    def _buscar(self, a: dict, _sid: UUID) -> dict:
        query = (a.get("query") or "").strip()
        categoria = (a.get("categoria") or "").strip()
        subcategoria = (a.get("subcategoria") or "").strip()
        marca = (a.get("marca") or "").strip()
        precio_min = ValueParser.a_float(a.get("precio_min"))
        precio_max = ValueParser.a_float(a.get("precio_max"))
        query_utiles = TokensConsulta.hay_terminos(NormalizadorTexto.normalizar(query)) if query else False
        tiene_filtro_estructurado = any([categoria, subcategoria, marca, precio_min, precio_max])
        if not query_utiles and not tiene_filtro_estructurado:
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
        productos = self.buscar.ejecutar(
            BuscarProductosQuery(
                query=query or None,
                categoria=categoria or None,
                subcategoria=subcategoria or None,
                marca=marca or None,
                precio_min=precio_min,
                precio_max=precio_max,
                solo_con_stock=bool(a.get("solo_con_stock", True)),
            )
        )
        return {"productos": [ProductoSerializer.resumen(p) for p in productos], "total": len(productos)}

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
