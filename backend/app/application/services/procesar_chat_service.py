from __future__ import annotations

import re
from typing import Callable
from uuid import UUID

from ...domain.chat import RolMensaje
from ...domain.productos import SKU
from ...domain.shared.normalizacion import NormalizadorTexto
from ...domain.shared.tokens_consulta import TokensConsulta
from ..chat.agente_service import AgenteService
from ..chat.paso_agente import PasoAgente
from ..chat.serializers import ProductoSerializer
from ..chat.tool_dispatcher import ToolDispatcher
from ..commands.crear_sesion import CrearSesionCommand, CrearSesionHandler
from ..commands.registrar_mensaje import RegistrarMensajeCommand, RegistrarMensajeHandler
from ..ports import UnitOfWork
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.historial_chat import HistorialChatHandler, HistorialChatQuery
from .chat_input import ChatInput
from .chat_output import ChatOutput
from .detector_mentiras import DetectorMentiras
from .tools_mark import ToolsMark

SKU_PATTERN = re.compile(r"\[([A-Z0-9][A-Z0-9\-]{2,40})\]")
RX_LISTA_PRODUCTOS = re.compile(r"(?:bs\s*[\d\.,]+|opcion(?:es)?[:.])", re.IGNORECASE)
MAX_HISTORIAL = 10


class ProcesarChatService:
    """Caso de uso top-level que coordina persistencia + agente + anti-mentiras."""

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        crear_sesion: CrearSesionHandler,
        registrar_mensaje: RegistrarMensajeHandler,
        historial_chat: HistorialChatHandler,
        agente: AgenteService,
        dispatcher: ToolDispatcher,
        buscar_productos: BuscarProductosHandler,
        detector: DetectorMentiras,
    ) -> None:
        self._uow_factory = uow_factory
        self._crear_sesion = crear_sesion
        self._registrar = registrar_mensaje
        self._historial = historial_chat
        self._agente = agente
        self._dispatcher = dispatcher
        self._buscar = buscar_productos
        self._detector = detector

    async def procesar(self, inp: ChatInput) -> ChatOutput:
        sesion_id = inp.sesion_id or self._crear_sesion.ejecutar(CrearSesionCommand())

        if inp.sesion_id:
            with self._uow_factory() as uow:
                if not uow.sesiones.existe(sesion_id):
                    raise LookupError("sesion no encontrada")

        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.USER, contenido=inp.mensaje)
        )
        historial = [
            {"role": m.rol.value, "content": m.contenido}
            for m in self._historial.ejecutar(
                HistorialChatQuery(sesion_id=sesion_id, limite=MAX_HISTORIAL)
            )
        ]

        resultado = await self._agente.conversar(sesion_id, historial)
        respuesta = resultado.texto
        trace: list[PasoAgente] = list(resultado.trace)
        skus_tool = list(resultado.skus_tocados)

        tools_ok = {p.tool for p in trace if not p.result.get("error")}
        faltantes = self._detector.detectar(respuesta, tools_ok)
        if faltantes:
            respuesta, trace = self._ejecutar_fallback_acciones(
                sesion_id, inp.mensaje, faltantes, respuesta, trace
            )

        hubo_tool_util = any(not p.result.get("error") for p in trace)
        parece_listar = bool(RX_LISTA_PRODUCTOS.search(respuesta))
        if parece_listar and not hubo_tool_util:
            respuesta, trace, skus_tool = self._forzar_busqueda(inp.mensaje, trace)

        respuesta, productos = self._sanear_skus_y_enriquecer(respuesta, skus_tool)

        self._registrar_respuesta(sesion_id, respuesta, trace)

        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=ToolsMark.strip(respuesta),
            productos_citados=productos,
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

    def _forzar_busqueda(
        self, mensaje: str, trace: list[PasoAgente]
    ) -> tuple[str, list[PasoAgente], list[str]]:
        mensaje_norm = NormalizadorTexto.normalizar(mensaje)
        if not TokensConsulta.hay_terminos(mensaje_norm):
            return (
                "Necesito un poco mas de contexto para buscar — decime el producto "
                "(ej. 'laptop', 'freidora', 'celular') y si tenes marca o presupuesto.",
                trace,
                [],
            )
        productos = self._buscar.ejecutar(BuscarProductosQuery(query=mensaje))
        resultado = {"productos": [ProductoSerializer.resumen(p) for p in productos], "total": len(productos)}
        trace.append(
            PasoAgente(tool="buscar_productos", args={"query": mensaje}, result=resultado, fallback=True)
        )
        if not productos:
            return (
                "Ups, no encontre nada exacto con eso en el catalogo. "
                "Me das mas pistas? Marca preferida, presupuesto o tamanio me ayudarian un monton.",
                trace,
                [],
            )
        lineas = ["Mira lo que tengo para vos!"]
        for p in productos[:3]:
            extra = f" (antes Bs {p.precio_anterior.monto:.0f})" if p.precio_anterior else ""
            stock_txt = f"stock: {p.stock}" if p.stock else "sin stock"
            lineas.append(f"- [{p.sku}] {p.nombre} — Bs {p.precio.monto:.0f}{extra}, {stock_txt}")
        lineas.append("Queres que te lo agregue al carrito o te muestro mas opciones?")
        return "\n".join(lineas), trace, [str(p.sku) for p in productos[:3]]

    def _ejecutar_fallback_acciones(
        self,
        sesion_id: UUID,
        mensaje: str,
        faltantes: list[str],
        respuesta_original: str,
        trace: list[PasoAgente],
    ) -> tuple[str, list[PasoAgente]]:
        skus_msg = [m.group(1) for m in SKU_PATTERN.finditer(mensaje)]
        carrito_actual = self._dispatcher.ejecutar("ver_carrito", {}, sesion_id)
        skus_en_carrito = [i["sku"] for i in carrito_actual.get("items", [])]

        confirmaciones: list[str] = []
        for tool_name in faltantes:
            sku = skus_msg[0] if skus_msg else None

            if tool_name == "vaciar_carrito":
                if not skus_en_carrito:
                    continue
                res = self._dispatcher.ejecutar("vaciar_carrito", {}, sesion_id)
                trace.append(PasoAgente(tool=tool_name, args={}, result=res, fallback=True))
                if not res.get("error"):
                    confirmaciones.append("vacie tu carrito")
                continue

            if tool_name == "quitar_del_carrito":
                if not sku and len(skus_en_carrito) == 1:
                    sku = skus_en_carrito[0]
                if not sku:
                    continue
                res = self._dispatcher.ejecutar("quitar_del_carrito", {"sku": sku}, sesion_id)
                trace.append(PasoAgente(tool=tool_name, args={"sku": sku}, result=res, fallback=True))
                if not res.get("error"):
                    confirmaciones.append(f"quite [{sku}] del carrito")

            elif tool_name == "agregar_al_carrito":
                if not sku:
                    continue
                res = self._dispatcher.ejecutar("agregar_al_carrito", {"sku": sku}, sesion_id)
                trace.append(PasoAgente(tool=tool_name, args={"sku": sku}, result=res, fallback=True))
                if not res.get("error"):
                    confirmaciones.append(f"agregue [{sku}] al carrito")

        if not confirmaciones:
            return respuesta_original, trace

        carrito_final = self._dispatcher.ejecutar("ver_carrito", {}, sesion_id)
        total = carrito_final.get("total_bob", 0)
        items = carrito_final.get("items", [])
        partes = ["Listo, " + " y ".join(confirmaciones) + "."]
        if items:
            detalle = ", ".join(f"[{i['sku']}] x{i['cantidad']}" for i in items)
            partes.append(f"Carrito: {detalle}. Total Bs {total:.2f}.")
        else:
            partes.append("Tu carrito quedo vacio.")
        return " ".join(partes), trace

    def _sanear_skus_y_enriquecer(
        self, respuesta: str, skus_tool: list[str]
    ) -> tuple[str, list[dict]]:
        skus_texto = [m.group(1) for m in SKU_PATTERN.finditer(respuesta)]
        candidatos = list({*skus_texto, *skus_tool})
        if not candidatos:
            return respuesta, []

        with self._uow_factory() as uow:
            existentes = uow.productos.existen_skus(candidatos)
            orden: list[str] = []
            vistos: set[str] = set()
            for s in [*skus_texto, *skus_tool]:
                if s in existentes and s not in vistos:
                    vistos.add(s)
                    orden.append(s)
            productos = uow.productos.obtener_varios([SKU(s) for s in orden])
            por_sku = {str(p.sku): p for p in productos}
            productos_orden = [por_sku[s] for s in orden if s in por_sku]

        def _sub(match: re.Match[str]) -> str:
            return match.group(0) if match.group(1) in existentes else "[no disponible]"

        respuesta = SKU_PATTERN.sub(_sub, respuesta)
        return respuesta, [ProductoSerializer.resumen(p) for p in productos_orden]

    def _registrar_respuesta(self, sesion_id: UUID, respuesta: str, trace: list[PasoAgente]) -> None:
        contenido = ToolsMark.wrap(respuesta, ToolsMark.resumir(trace))
        self._registrar.ejecutar(
            RegistrarMensajeCommand(
                sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=contenido
            )
        )
