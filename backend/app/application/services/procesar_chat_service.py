from __future__ import annotations

import re
import time
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
from ..commands.actualizar_perfil_sesion import ActualizarPerfilSesionHandler
from ..commands.crear_sesion import CrearSesionCommand, CrearSesionHandler
from ..commands.registrar_alternativa_ofrecida import (
    RegistrarAlternativaOfrecidaCommand,
    RegistrarAlternativaOfrecidaHandler,
)
from ..commands.registrar_mensaje import RegistrarMensajeCommand, RegistrarMensajeHandler
from ..commands.registrar_metrica_turno import (
    RegistrarMetricaTurnoCommand,
    RegistrarMetricaTurnoHandler,
)
from ..commands.registrar_turno_mostrado import (
    RegistrarTurnoMostradoCommand,
    RegistrarTurnoMostradoHandler,
)
from ..ports import UnitOfWork
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from ..queries.historial_chat import HistorialChatHandler, HistorialChatQuery
from ..queries.obtener_perfil_sesion import (
    ObtenerPerfilSesionHandler,
    ObtenerPerfilSesionQuery,
    ResultadoObtenerPerfilSesion,
)
from .aplicador_cross_sell import AplicadorCrossSell
from .atajo_ordinal_carrito import AtajoOrdinalCarrito
from .atajo_sku_directo import AtajoSkuDirecto
from .chat_input import ChatInput
from .chat_output import ChatOutput
from .clasificador_intencion import ClasificadorIntencion
from .curador_conversaciones import CuradorConversaciones
from .detector_asesoria_mostrados import DetectorAsesoriaMostrados
from .detector_comparacion_explicita import DetectorComparacionExplicita
from .detector_consulta_accesorio import DetectorConsultaAccesorio
from .detector_genero_mencion import DetectorGeneroMencion
from .bloqueador_lista_repetida import BloqueadorListaRepetida
from .sugeridor_accesorios_relacionados import SugeridorAccesoriosRelacionados
from .umbrales_tier import UmbralesTier
from .verificador_claims_producto import VerificadorClaimsProducto
from .detector_consulta_relativa import DetectorConsultaRelativa, TipoConsultaRelativa
from .detector_consulta_disponibilidad import DetectorConsultaDisponibilidad
from .detector_exclusiones_mensaje import DetectorExclusionesMensaje
from .clasificador_etapa_conversacional import ClasificadorEtapaConversacional
from .recortador_cierres_comerciales import RecortadorCierresComerciales
from .renderizador_tabla_comparacion import RenderizadorTablaComparacion
from .silenciador_preguntas_redundantes import SilenciadorPreguntasRedundantes
from .normalizador_formato_producto import NormalizadorFormatoProducto
from .limpiador_lista_productos import LimpiadorListaProductos
from .detector_intencion_asesoria import DetectorIntencionAsesoria
from .detector_intencion_compra import DetectorIntencionCompra
from .detector_mentiras import DetectorMentiras
from .detector_pedido_detalle import DetectorPedidoDetalle
from .detector_refinamiento_shown import DetectorRefinamientoShown
from .detector_sku_mensaje import DetectorSkuMensaje
from .extractor_perfil_mensaje import ExtractorPerfilMensaje
from .gestor_feedback_post_orden import GestorFeedbackPostOrden
from .gestor_follow_ups_contextuales import GestorFollowUpsContextuales
from .manejador_producto_ausente import ManejadorProductoAusente
from .normalizador_moneda import NormalizadorMoneda
from .resolvedor_categoria_cercana import ResolvedorCategoriaCercana
from .detector_marca_mensaje import DetectorMarcaMensaje
from .detector_solicitud_similares import DetectorSolicitudSimilares
from .excluidor_juguetes_default import ExcluidorJuguetesDefault
from .responder_comparacion_explicita import ResponderComparacionExplicita
from .responder_consulta_disponibilidad import ResponderConsultaDisponibilidad
from .responder_productos_similares import ResponderProductosSimilares
from .responder_consulta_politica import ResponderConsultaPolitica
from .respuesta_follow_up import RespuestaFollowUp
from .sanitizador_query_busqueda import SanitizadorQueryBusqueda
from .tools_mark import ToolsMark

SKU_PATTERN = re.compile(
    r"\[(?:sku[:\s]+)?([A-ZÑ0-9][A-ZÑ0-9\-.#_/()]{2,60})\]",
    re.IGNORECASE,
)
RX_LISTA_PRODUCTOS = re.compile(
    r"(?:bs\s*[\d\.,]+|\bopcion(?:es)?\b|\brecomiendo\b|\bsugiero\b|\bpodrias\b|\bte ofrec|\baqui (?:van|tienes|tengo))",
    re.IGNORECASE,
)
RX_LISTA_NUMERADA = re.compile(r"(?m)^\s*\d+[\.\)]\s+\S.+$")
MARCADOR_NO_DISPONIBLE = "[no disponible]"
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
        manejador_ausente: ManejadorProductoAusente,
        clasificador: ClasificadorIntencion,
        curador: CuradorConversaciones,
        registrar_metrica: RegistrarMetricaTurnoHandler,
        atajo_sku: AtajoSkuDirecto,
        atajo_ordinal: AtajoOrdinalCarrito,
        extractor_perfil: ExtractorPerfilMensaje,
        actualizar_perfil: ActualizarPerfilSesionHandler,
        obtener_perfil: ObtenerPerfilSesionHandler,
        cross_sell: AplicadorCrossSell,
        gestor_feedback: GestorFeedbackPostOrden,
        registrar_turno_mostrado: RegistrarTurnoMostradoHandler,
        gestor_follow_ups: GestorFollowUpsContextuales,
        registrar_alternativa: RegistrarAlternativaOfrecidaHandler,
        resolvedor_categoria: ResolvedorCategoriaCercana,
        responder_consulta_disponibilidad: ResponderConsultaDisponibilidad,
        responder_comparacion_explicita: ResponderComparacionExplicita,
        responder_similares: ResponderProductosSimilares,
    ) -> None:
        self._uow_factory = uow_factory
        self._crear_sesion = crear_sesion
        self._registrar = registrar_mensaje
        self._historial = historial_chat
        self._agente = agente
        self._dispatcher = dispatcher
        self._buscar = buscar_productos
        self._detector = detector
        self._manejador_ausente = manejador_ausente
        self._clasificador = clasificador
        self._curador = curador
        self._registrar_metrica = registrar_metrica
        self._atajo_sku = atajo_sku
        self._atajo_ordinal = atajo_ordinal
        self._extractor_perfil = extractor_perfil
        self._actualizar_perfil = actualizar_perfil
        self._obtener_perfil = obtener_perfil
        self._cross_sell = cross_sell
        self._gestor_feedback = gestor_feedback
        self._registrar_turno_mostrado = registrar_turno_mostrado
        self._gestor_follow_ups = gestor_follow_ups
        self._registrar_alternativa = registrar_alternativa
        self._resolvedor_categoria = resolvedor_categoria
        self._responder_consulta_disp = responder_consulta_disponibilidad
        self._responder_comparacion_explicita = responder_comparacion_explicita
        self._responder_similares = responder_similares

    async def procesar(self, inp: ChatInput) -> ChatOutput:
        t0 = time.monotonic()
        sesion_id = inp.sesion_id or self._crear_sesion.ejecutar(CrearSesionCommand())

        if inp.sesion_id:
            with self._uow_factory() as uow:
                if not uow.sesiones.existe(sesion_id):
                    raise LookupError("sesion no encontrada")

        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.USER, contenido=inp.mensaje)
        )

        self._actualizar_perfil.ejecutar(
            self._extractor_perfil.extraer(sesion_id, inp.mensaje)
        )

        cierre_feedback = self._gestor_feedback.intentar_registrar_respuesta(
            inp.mensaje, sesion_id
        )
        if cierre_feedback is not None:
            return self._responder_feedback(sesion_id, inp.mensaje, cierre_feedback, t0)

        directa = self._clasificador.respuesta_directa(inp.mensaje)
        if directa is not None:
            self._registrar.ejecutar(
                RegistrarMensajeCommand(
                    sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=directa.texto
                )
            )
            self._registrar_metrica.ejecutar(
                RegistrarMetricaTurnoCommand(
                    sesion_id=sesion_id,
                    mensaje_usuario_len=len(inp.mensaje),
                    respuesta_len=len(directa.texto),
                    tool_calls=0,
                    mentiras_detectadas=0,
                    productos_citados=0,
                    ruta=f"atajo_{directa.intencion.value}",
                    tiempo_ms=int((time.monotonic() - t0) * 1000),
                )
            )
            return ChatOutput(sesion_id=sesion_id, respuesta=directa.texto)

        # Boton 'Similares' del card: atajo determinista antes de cualquier
        # otro detector (follow-ups, atajos) que pueda distraer el flujo.
        similares_sc = self._short_circuit_similares(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if similares_sc is not None:
            return similares_sc

        sku_directo = self._atajo_sku.resolver(inp.mensaje, sesion_id)
        if sku_directo is not None:
            return self._responder_atajo_sku(sesion_id, inp.mensaje, sku_directo, t0)

        ordinal = self._atajo_ordinal.resolver(inp.mensaje, sesion_id)
        if ordinal is not None:
            return self._responder_follow_up(sesion_id, inp.mensaje, ordinal, t0)

        politica = ResponderConsultaPolitica.responder(inp.mensaje)
        if politica is not None:
            return self._responder_follow_up(sesion_id, inp.mensaje, politica, t0)

        follow_up = self._gestor_follow_ups.intentar(inp.mensaje, sesion_id)
        if follow_up is not None:
            return self._responder_follow_up(sesion_id, inp.mensaje, follow_up, t0)

        historial = [
            {"role": m.rol.value, "content": m.contenido}
            for m in self._historial.ejecutar(
                HistorialChatQuery(sesion_id=sesion_id, limite=MAX_HISTORIAL)
            )
        ]
        comparacion_explicita = self._short_circuit_comparacion_explicita(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if comparacion_explicita is not None:
            return comparacion_explicita

        asesoria_mostrados = self._short_circuit_asesoria_mostrados(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if asesoria_mostrados is not None:
            return asesoria_mostrados

        short_circuit = await self._short_circuit_resolver(
            inp=inp, historial=historial, sesion_id=sesion_id, t0=t0
        )
        if short_circuit is not None:
            return short_circuit

        contexto_turno = self._contexto_del_turno(inp.mensaje, sesion_id)
        marca_indif = DetectorIntencionAsesoria.marca_es_indiferente(inp.mensaje)
        resultado = await self._agente.conversar(
            sesion_id, historial, contexto_turno, marca_indiferente=marca_indif
        )
        respuesta = resultado.texto
        trace: list[PasoAgente] = list(resultado.trace)
        skus_tool = list(resultado.skus_tocados)

        tools_ok = {p.tool for p in trace if not p.result.get("error")}
        faltantes = self._detector.detectar(respuesta, tools_ok)
        mentiras_detectadas = len(faltantes)
        if faltantes:
            respuesta, trace = self._ejecutar_fallback_acciones(
                sesion_id, inp.mensaje, faltantes, respuesta, trace
            )

        if self._debe_forzar_busqueda(respuesta, trace, inp.mensaje):
            respuesta, trace, skus_tool = self._forzar_busqueda(inp.mensaje, sesion_id, trace)

        respuesta = NormalizadorMoneda.normalizar(respuesta)
        respuesta = self._inyectar_foco_si_falta(respuesta, trace)
        respuesta, productos = self._sanear_skus_y_enriquecer(respuesta, skus_tool)
        # Si el LLM cito SKUs del cross-sell como productos principales, los
        # movemos a la seccion "También podría interesarte" donde pertenecen.
        productos = self._separar_sugeridos_citados(productos, trace)
        # Si el mensaje tenia un SKU explicito pero la respuesta no lo cito,
        # igual mostramos la tarjeta (el LLM respondio con datos de la ficha).
        if not productos:
            sku_msg = DetectorSkuMensaje.extraer(inp.mensaje)
            if sku_msg:
                with self._uow_factory() as uow:
                    prods_sku = uow.productos.obtener_varios([SKU(sku_msg)])
                    if prods_sku:
                        productos = [ProductoSerializer.detalle(prods_sku[0])]
        respuesta = VerificadorClaimsProducto.corregir(respuesta, productos)
        respuesta = NormalizadorFormatoProducto.normalizar(respuesta)
        if productos:
            respuesta = LimpiadorListaProductos.limpiar(respuesta)

        respuesta, trace, productos, skus_tool = self._evitar_lista_repetida(
            respuesta, productos, trace, skus_tool, inp.mensaje, sesion_id
        )

        if self._necesita_manejo_ausente(respuesta, productos, trace):
            respuesta, trace, productos = await self._delegar_a_manejador_ausente(
                inp.mensaje, historial, trace, sesion_id
            )

        respuesta = self._reemplazar_tabla_comparacion(respuesta, trace)
        respuesta = self._cross_sell.aplicar(respuesta, trace, productos)
        respuesta = self._recortar_cierres(respuesta, inp.mensaje, sesion_id, trace)

        self._persistir_turno_mostrado(sesion_id, productos)

        llevo_a_orden = any(
            p.tool == "confirmar_orden" and not p.result.get("error") for p in trace
        )
        respuesta = self._gestor_feedback.anexar_pregunta_si_cerro(respuesta, llevo_a_orden)

        self._registrar_respuesta(sesion_id, respuesta, trace)
        self._curar_si_cerro_sesion(sesion_id, mentiras_detectadas, llevo_a_orden)

        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(respuesta),
                tool_calls=len(trace),
                mentiras_detectadas=mentiras_detectadas,
                productos_citados=len(productos),
                ruta="agente",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )

        sugeridos = self._extraer_sugeridos_del_trace(trace, productos)
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=ToolsMark.strip(respuesta),
            productos_citados=productos,
            productos_sugeridos=sugeridos,
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

    _TOKENS_PREMIUM = (
        "tope de gama", "tope gama", "alta gama", "gama alta", "premium",
        "flagship", "lo mejor", "el mejor", "la mejor", "high end",
        "ultra", "pro max",
    )
    _RATIO_PISO_PREMIUM = 0.5

    @classmethod
    def _filtrar_por_gama(
        cls, productos: list, mensaje: str, sku_foco: str | None
    ) -> list:
        """Cuando el cliente pidió gama alta o ya hay un producto foco premium,
        filtra del listado los productos cuyo precio esté muy por debajo del
        foco (o del top de la lista si no hay foco). Evita mezclar S26 Ultra
        con Huavi H-120 en el mismo bloque."""
        if not productos:
            return productos
        norm = NormalizadorTexto.normalizar(mensaje or "")
        pidio_premium = any(tok in norm for tok in cls._TOKENS_PREMIUM)
        foco = None
        if sku_foco:
            foco = next((p for p in productos if str(p.sku) == sku_foco), None)
        if foco is None and not pidio_premium:
            return productos
        anchor_precio = foco.precio.monto if foco else max(p.precio.monto for p in productos)
        piso = anchor_precio * cls._RATIO_PISO_PREMIUM
        filtrados = [p for p in productos if p.precio.monto >= piso]
        return filtrados or productos[:1]

    def _evitar_lista_repetida(
        self,
        respuesta: str,
        productos: list[dict],
        trace: list,
        skus_tool: list[str],
        mensaje: str,
        sesion_id: UUID,
    ) -> tuple[str, list, list[dict], list[str]]:
        """Si el cliente pidió 'otra opción / distintas' y la respuesta
        repite SKUs ya mostrados, re-ejecuta forzar_busqueda excluyendo los
        vistos. Solo corrige cuando hay señal de follow-up — no toca
        búsquedas nuevas."""
        if not BloqueadorListaRepetida.es_follow_up_de_repeticion(mensaje):
            return respuesta, trace, productos, skus_tool
        skus_nuevos = [p["sku"] for p in productos if p.get("sku")]
        if not skus_nuevos:
            return respuesta, trace, productos, skus_tool
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        mostrados = BloqueadorListaRepetida.skus_del_perfil(perfil.ultimos_skus_mostrados)
        if not BloqueadorListaRepetida.lista_repetida(skus_nuevos, mostrados):
            return respuesta, trace, productos, skus_tool
        respuesta_nueva, trace_nuevo, skus_tool_nuevo = self._forzar_busqueda(
            mensaje, sesion_id, list(trace), excluir_skus=tuple(mostrados)
        )
        respuesta_nueva = NormalizadorMoneda.normalizar(respuesta_nueva)
        respuesta_nueva, productos_nuevos = self._sanear_skus_y_enriquecer(
            respuesta_nueva, skus_tool_nuevo
        )
        return respuesta_nueva, trace_nuevo, productos_nuevos, skus_tool_nuevo

    def _precio_del_foco(self, sku_foco: str | None) -> float | None:
        """Fetch el precio del producto foco cuando hay sku_foco. Silencioso
        ante errores — no bloquea la búsqueda si la tool falla."""
        if not sku_foco:
            return None
        try:
            with self._uow_factory() as uow:
                from ...domain.productos import SKU
                prod = uow.productos.obtener_por_sku(SKU(sku_foco))
        except Exception:
            return None
        return float(prod.precio.monto) if prod else None

    def _prepend_sku_foco(self, productos: list, sku_foco: str | None) -> list:
        """Mismo patron que ToolDispatcher._prepend_producto_foco pero para
        _forzar_busqueda: si el cliente mencionó un modelo (ej. 's26 ultra' →
        sku_foco), ese SKU va primero. Si ya viene, lo subimos; si no, lo
        buscamos por SKU exacto y lo insertamos."""
        if not sku_foco:
            return productos
        por_sku = {str(p.sku): p for p in productos}
        if sku_foco in por_sku:
            foco = por_sku[sku_foco]
            rest = [p for p in productos if str(p.sku) != sku_foco]
            return [foco, *rest]
        with self._uow_factory() as uow:
            from ...domain.productos import SKU
            try:
                foco = uow.productos.obtener_por_sku(SKU(sku_foco))
            except Exception:
                foco = None
        if foco is None:
            return productos
        return [foco, *productos]

    @staticmethod
    def _inyectar_foco_si_falta(respuesta: str, trace: list[PasoAgente]) -> str:
        """Safety net: si el dispatcher identifico un `producto_foco_sku` y el
        LLM se olvido de citarlo entre corchetes en su texto, le agregamos la
        cita al final para que la tarjeta aparezca igual."""
        focos = {
            paso.result.get("producto_foco_sku")
            for paso in trace
            if paso.tool == "buscar_productos" and paso.result.get("producto_foco_sku")
        }
        if not focos:
            return respuesta
        for sku in focos:
            if sku and f"[{sku}]" not in respuesta:
                respuesta = f"{respuesta.rstrip()}\n[{sku}]"
        return respuesta

    @staticmethod
    def _extraer_sugeridos_del_trace(
        trace: list, productos_citados: list[dict]
    ) -> list[dict]:
        """Consolida los accesorios sugeridos (cross-sell) de todos los
        buscar_productos del turno, excluyendo los SKUs ya citados en la
        respuesta principal."""
        skus_citados = {p.get("sku") for p in productos_citados if p.get("sku")}
        vistos: set[str] = set()
        sugeridos: list[dict] = []
        for paso in trace:
            if paso.tool != "buscar_productos":
                continue
            for s in paso.result.get("sugeridos") or []:
                sku = s.get("sku")
                if not sku or sku in skus_citados or sku in vistos:
                    continue
                vistos.add(sku)
                sugeridos.append(s)
        return sugeridos

    def _short_circuit_asesoria_mostrados(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Cuando el cliente pide 'ayudame a decidir / cual me conviene'
        sobre productos ya mostrados, dispara una comparación estructurada
        con los `ultimos_skus_mostrados` del perfil. Sin LLM, sin búsqueda
        nueva: tabla + conclusión directa sobre lo que el cliente ya vio."""
        if not DetectorAsesoriaMostrados.es_asesoria_sobre_mostrados(inp.mensaje):
            return None
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        mostrados = [
            s for s in (perfil.ultimos_skus_mostrados or "").split(",") if s.strip()
        ]
        if len(mostrados) < 2:
            return None
        respuesta = self._responder_comparacion_explicita.responder_por_skus(
            mostrados[:4]
        )
        if respuesta is None:
            return None
        productos_citados = [
            ProductoSerializer.detalle(p) for p in respuesta.resultado.productos
        ]
        resultado_tool = {
            "productos": [ProductoSerializer.resumen(p) for p in respuesta.resultado.productos],
            "tabla": respuesta.resultado.tabla,
            "conclusion": respuesta.resultado.conclusion,
        }
        trace = [
            PasoAgente(
                tool="comparar_productos",
                args={"skus": [str(p.sku) for p in respuesta.resultado.productos]},
                result=resultado_tool,
                fallback=True,
            )
        ]
        self._registrar_respuesta(sesion_id, respuesta.texto, trace)
        self._persistir_turno_mostrado(sesion_id, productos_citados)
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(respuesta.texto),
                tool_calls=1,
                mentiras_detectadas=0,
                productos_citados=len(productos_citados),
                ruta="asesoria_mostrados",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=respuesta.texto,
            productos_citados=productos_citados,
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

    def _short_circuit_comparacion_explicita(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Cuando el cliente nombra 2+ modelos para comparar (ej. 's26 ultra
        vs iphone 17 pro max'), short-circuit: resolvemos cada uno a su SKU
        via aliases, llamamos al comparador estructurado y devolvemos la
        tabla + conclusión formateada. El LLM no participa — es determinista."""
        intent = DetectorComparacionExplicita.detectar(inp.mensaje)
        if intent is None:
            return None
        respuesta = self._responder_comparacion_explicita.responder(intent)
        if respuesta is None:
            return None
        productos_citados = [
            ProductoSerializer.detalle(p) for p in respuesta.resultado.productos
        ]
        skus_tool = [str(p.sku) for p in respuesta.resultado.productos]
        resultado_tool = {
            "productos": [ProductoSerializer.resumen(p) for p in respuesta.resultado.productos],
            "tabla": respuesta.resultado.tabla,
            "conclusion": respuesta.resultado.conclusion,
        }
        trace = [
            PasoAgente(
                tool="comparar_productos",
                args={"skus": skus_tool},
                result=resultado_tool,
                fallback=True,
            )
        ]
        self._registrar_respuesta(sesion_id, respuesta.texto, trace)
        self._persistir_turno_mostrado(sesion_id, productos_citados)
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(respuesta.texto),
                tool_calls=1,
                mentiras_detectadas=0,
                productos_citados=len(productos_citados),
                ruta="comparacion_explicita",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=respuesta.texto,
            productos_citados=productos_citados,
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

    def _short_circuit_similares(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Cliente pidio alternativas a un SKU especifico (ej. click en boton
        'Similares' del card). Busca productos de la misma categoria/subcategoria
        en rango de precio cercano, excluyendo el SKU original. No pasa por LLM."""
        sku = DetectorSolicitudSimilares.sku_si_pide_similares(inp.mensaje)
        if not sku:
            return None
        respuesta = self._responder_similares.responder(sku)
        if respuesta is None:
            return None
        productos_citados = [
            ProductoSerializer.detalle(p) for p in respuesta.productos
        ]
        trace = [
            PasoAgente(
                tool="buscar_productos",
                args={"similares_a": respuesta.sku_original},
                result={
                    "productos": [ProductoSerializer.resumen(p) for p in respuesta.productos],
                    "total": len(respuesta.productos),
                },
                fallback=True,
            )
        ]
        self._registrar_respuesta(sesion_id, respuesta.texto, trace)
        self._persistir_turno_mostrado(sesion_id, productos_citados)
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(respuesta.texto),
                tool_calls=1,
                mentiras_detectadas=0,
                productos_citados=len(productos_citados),
                ruta="similares",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=respuesta.texto,
            productos_citados=productos_citados,
            productos_sugeridos=self._sugeridos_para_cards(productos_citados),
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

    async def _short_circuit_resolver(
        self,
        inp: ChatInput,
        historial: list[dict],
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Decide en BD si el mensaje pega contra categorias_relacionadas
        (producto pedido != catalogo pero hay cercanos) o contra un sinonimo
        directo + pregunta de disponibilidad. Ambos caminos cierran turno
        antes de invocar al LLM."""
        cercana = self._resolvedor_categoria.resolver(inp.mensaje)
        if cercana is None:
            return None
        if cercana.fuente == "relacionada":
            respuesta, trace, productos = await self._delegar_a_manejador_ausente(
                inp.mensaje, historial, [], sesion_id
            )
            return self._finalizar_turno_ausente(
                sesion_id=sesion_id,
                inp=inp,
                respuesta=respuesta,
                trace=trace,
                productos=productos,
                t0=t0,
            )
        if cercana.fuente == "sinonimo" and DetectorConsultaDisponibilidad.es_consulta_disponibilidad(
            inp.mensaje
        ):
            genero = DetectorGeneroMencion.detectar(inp.mensaje)
            marca = DetectorMarcaMensaje.extraer(inp.mensaje)
            respuesta_disp = self._responder_consulta_disp.responder(
                cercana, genero=genero, marca=marca
            )
            if respuesta_disp is not None:
                return self._responder_follow_up(
                    sesion_id, inp.mensaje, respuesta_disp, t0
                )
        return None

    def _finalizar_turno_ausente(
        self,
        sesion_id: UUID,
        inp: ChatInput,
        respuesta: str,
        trace: list[PasoAgente],
        productos: list[dict],
        t0: float,
    ) -> ChatOutput:
        """Cierre de turno cuando el short-circuit determinista via
        ResolvedorCategoriaCercana ya decidio la respuesta. Persiste el
        mensaje, metricas y devuelve ChatOutput sin pasar por el LLM."""
        respuesta = NormalizadorMoneda.normalizar(respuesta)
        respuesta = NormalizadorFormatoProducto.normalizar(respuesta)
        respuesta = self._recortar_cierres(respuesta, inp.mensaje, sesion_id, trace)
        self._persistir_turno_mostrado(sesion_id, productos)
        self._registrar_respuesta(sesion_id, respuesta, trace)
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(respuesta),
                tool_calls=len(trace),
                mentiras_detectadas=0,
                productos_citados=len(productos),
                ruta="manejador_ausente_short_circuit",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=ToolsMark.strip(respuesta),
            productos_citados=productos,
            productos_sugeridos=self._sugeridos_para_cards(productos),
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

    @staticmethod
    def _reemplazar_tabla_comparacion(respuesta: str, trace: list[PasoAgente]) -> str:
        """Si el LLM invoco comparar_productos, usamos la tabla+conclusion
        del tool result (construida por ComparadorProductos) y reemplazamos
        cualquier tabla/resumen que el LLM haya redactado. Evita que el LLM
        invente valores o bullets de conclusion."""
        paso = next(
            (
                p for p in reversed(trace or [])
                if p.tool == "comparar_productos" and not (p.result or {}).get("error")
            ),
            None,
        )
        if paso is None:
            return respuesta
        result = paso.result or {}
        tabla = result.get("tabla")
        conclusion = result.get("conclusion")
        if not tabla or not conclusion:
            return respuesta
        # productos vienen como dicts desde ProductoSerializer.resumen —
        # armamos un shim con atributo .nombre para que el renderer funcione.
        productos = result.get("productos") or []
        por_sku: dict = {}
        for p in productos:
            sku = p.get("sku")
            if sku:
                por_sku[str(sku)] = type("P", (), {"nombre": p.get("nombre", "")})()
        rendered = RenderizadorTablaComparacion.render(
            tabla=tabla, conclusion=conclusion, productos_por_sku=por_sku
        )
        return rendered or respuesta

    def _recortar_cierres(
        self,
        respuesta: str,
        mensaje: str,
        sesion_id: UUID,
        trace: list[PasoAgente],
    ) -> str:
        """Computa la etapa del turno, recorta cierres plantilla y silencia
        preguntas sobre slots ya declarados. Single point para aplicar reglas
        5/6/7 del prompt como codigo post-LLM."""
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        etapa = ClasificadorEtapaConversacional.clasificar(mensaje, perfil, trace)
        respuesta = SilenciadorPreguntasRedundantes.silenciar(respuesta, perfil)
        return RecortadorCierresComerciales.recortar(respuesta, etapa)

    def _contexto_del_turno(self, mensaje: str, sesion_id: UUID) -> str | None:
        bloques = [
            self._bloque_perfil(sesion_id),
            self._bloque_shown_products(sesion_id),
            self._bloque_intencion(mensaje),
            self._bloque_consulta_relativa(mensaje),
            self._bloque_intencion_compra(mensaje),
            self._bloque_sku(mensaje, sesion_id),
        ]
        bloques_validos = [b for b in bloques if b]
        return "\n\n".join(bloques_validos) if bloques_validos else None

    @staticmethod
    def _bloque_intencion_compra(mensaje: str) -> str | None:
        if not DetectorIntencionCompra.tiene_intencion(mensaje):
            return None
        return (
            "INTENCION DE COMPRA DETECTADA: el cliente quiere cerrar la venta. "
            "Guialo al flujo: (1) si todavia no esta en carrito, agrega el SKU "
            "mencionado con agregar_al_carrito; (2) pedi el nombre (y email/telefono "
            "si los dio) y llama confirmar_orden. NO sigas listando alternativas ni "
            "abras nuevas busquedas."
        )

    def _bloque_shown_products(self, sesion_id: UUID) -> str | None:
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        skus_str = perfil.ultimos_skus_mostrados
        if not skus_str:
            return None
        skus = [s for s in skus_str.split(",") if s]
        if not skus:
            return None
        partes = [
            "PRODUCTOS YA MOSTRADOS AL CLIENTE EN EL TURNO ANTERIOR (usalos como ancla, no los repitas):",
            f"- SKUs: {', '.join(skus)}",
        ]
        if perfil.precio_min_mostrado is not None:
            partes.append(f"- Precio minimo mostrado: Bs {perfil.precio_min_mostrado:.0f}")
        if perfil.precio_max_mostrado is not None:
            partes.append(f"- Precio maximo mostrado: Bs {perfil.precio_max_mostrado:.0f}")
        partes.append(
            "Si el cliente pide 'mas barato' usa precio_max POR DEBAJO del precio minimo de "
            "arriba. Si pide 'uno mejor' / 'algo mejor', subi calidad: premium brand, panel "
            "(MINILED/QLED/OLED), resolucion alta y precio_min POR ENCIMA del precio maximo "
            "mostrado. Si pide 'otra opcion', EXCLUI los SKUs de arriba."
        )
        return "\n".join(partes)

    def _persistir_turno_mostrado(self, sesion_id: UUID, productos: list[dict]) -> None:
        if not productos:
            return
        skus: list[str] = []
        precios: list[float] = []
        for p in productos:
            sku = p.get("sku")
            if sku:
                skus.append(str(sku))
            precio = p.get("precio_bob")
            if precio is not None:
                try:
                    precios.append(float(precio))
                except (TypeError, ValueError):
                    pass
        if not skus:
            return
        self._registrar_turno_mostrado.ejecutar(
            RegistrarTurnoMostradoCommand(
                sesion_id=sesion_id,
                skus=tuple(skus),
                precios=tuple(precios),
            )
        )

    @staticmethod
    def _bloque_consulta_relativa(mensaje: str) -> str | None:
        consulta = DetectorConsultaRelativa.detectar(mensaje)
        if consulta is None:
            return None
        partes = ["FOLLOW-UP RELATIVO AL CONTEXTO PREVIO (no abras categoria nueva):"]
        if consulta.tipo is TipoConsultaRelativa.MAS_BARATO:
            partes.append(
                "- El cliente pidio algo MAS BARATO que lo ya mostrado. Reusa los "
                "filtros del perfil (categoria, marca, pulgadas, panel, resolucion) "
                "y llama buscar_productos BAJANDO el precio_max por debajo del "
                "precio minimo de los productos mostrados en el turno anterior. "
                "NO vuelvas a preguntar categoria/tamanio."
            )
        elif consulta.tipo is TipoConsultaRelativa.MAS_CARO:
            partes.append(
                "- El cliente pidio algo MAS PREMIUM / MAS CARO. Reusa los filtros "
                "del perfil y llama buscar_productos usando precio_min por encima "
                "del precio maximo de los productos mostrados en el turno anterior, "
                "priorizando panel premium (MINILED/QLED), resolucion alta (4K/8K) "
                "y marcas top. NO vuelvas a preguntar categoria."
            )
        elif consulta.tipo is TipoConsultaRelativa.OTRA_OPCION:
            partes.append(
                "- El cliente pide OTRA OPCION / ALTERNATIVA. Reusa los filtros del "
                "perfil y llama buscar_productos EXCLUYENDO los SKUs que ya mostraste "
                "en el turno anterior (mira el historial). Mantene categoria, marca, "
                "presupuesto y atributos tecnicos — NO los vuelvas a preguntar."
            )
        elif consulta.tipo is TipoConsultaRelativa.COMPARAR_MOSTRADOS:
            partes.append(
                "- El cliente quiere COMPARAR los productos que ya mostraste. Lee "
                "los SKUs entre corchetes del turno anterior y llama comparar_productos "
                "con esos SKUs. NO abras una busqueda nueva."
            )
        return "\n".join(partes)

    @staticmethod
    def _bloque_intencion(mensaje: str) -> str | None:
        asesor = DetectorIntencionAsesoria.es_modo_asesor(mensaje)
        marca_indif = DetectorIntencionAsesoria.marca_es_indiferente(mensaje)
        if not asesor and not marca_indif:
            return None
        partes = ["SENIALES DE ESTE TURNO (detectadas en el mensaje del cliente):"]
        if asesor:
            partes.append(
                "- MODO ASESOR: el cliente pide recomendacion, no busqueda puntual. "
                "Si te falta algun dato clave (uso, presupuesto, tamanio), haz 1-3 "
                "preguntas breves ANTES de listar productos. Luego aplica la plantilla "
                "de asesor: opcion principal + 1-2 alternativas + por que + pregunta de cierre."
            )
        if marca_indif:
            partes.append(
                "- MARCA INDIFERENTE: el cliente declaro que no le importa la marca. "
                "NO pases 'marca' al llamar buscar_productos aunque la tengas en el "
                "perfil previo. Recomienda por calidad/precio, no por marca."
            )
        return "\n".join(partes)

    def _bloque_perfil(self, sesion_id: UUID) -> str | None:
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        if perfil.esta_vacio():
            return None
        return self._formatear_perfil(perfil)

    @staticmethod
    def _formatear_perfil(perfil: ResultadoObtenerPerfilSesion) -> str:
        partes = ["PERFIL DECLARADO POR EL CLIENTE (no vuelvas a preguntarle esto):"]
        if perfil.presupuesto_max:
            partes.append(f"- Presupuesto maximo: Bs {perfil.presupuesto_max:.0f}")
        if perfil.marca_preferida:
            partes.append(f"- Marca preferida: {perfil.marca_preferida}")
        if perfil.categoria_foco:
            partes.append(f"- Categoria de interes: {perfil.categoria_foco}")
        elif perfil.alternativa_ofrecida:
            partes.append(
                f"- Categoria activa (alternativa ofrecida por el agente, "
                f"el cliente la esta explorando): {perfil.alternativa_ofrecida}"
            )
        if perfil.uso_declarado:
            partes.append(f"- Uso declarado: {perfil.uso_declarado}")
        if perfil.pulgadas:
            partes.append(f"- Pulgadas: {perfil.pulgadas:g}\"")
        if perfil.tipo_panel:
            partes.append(f"- Tipo de panel: {perfil.tipo_panel}")
        if perfil.resolucion:
            partes.append(f"- Resolucion: {perfil.resolucion}")
        partes.append(
            "Al llamar buscar_productos, usa estos campos como filtros implicitos "
            "SIEMPRE, aunque el mensaje actual no los repita. Si el cliente dice "
            "'mas barato', 'otra opcion', 'cual me conviene' o cualquier follow-up "
            "sin categoria nueva, MANTENE estos filtros y solo ajusta precio_max u "
            "ordena distinto — NO vuelvas a preguntar categoria ni tamanio."
        )
        return "\n".join(partes)

    def _bloque_sku(self, mensaje: str, sesion_id: UUID) -> str | None:
        ficha = self._atajo_sku.ficha_si_existe(mensaje, sesion_id)
        if not ficha:
            return None
        if ficha.get("solo_tienda_fisica") or ficha.get("es_descontinuado"):
            return None
        partes = [
            "CONTEXTO DE ESTE TURNO (datos ya verificados por el sistema, usalos sin volver a buscar):",
            f"- SKU: {ficha.get('sku')}",
            f"- Nombre: {ficha.get('nombre')}",
        ]
        if ficha.get("marca"):
            partes.append(f"- Marca: {ficha.get('marca')}")
        if ficha.get("categoria"):
            partes.append(f"- Categoria: {ficha.get('categoria')}")
        if ficha.get("precio_bob") is not None:
            partes.append(f"- Precio: Bs {ficha['precio_bob']:.0f}")
        if ficha.get("precio_anterior_bob"):
            partes.append(f"- Precio anterior: Bs {ficha['precio_anterior_bob']:.0f}")
        # Specs estructuradas (columnas indexadas)
        if ficha.get("atributos"):
            partes.append("- Specs:")
            for k, v in ficha["atributos"].items():
                partes.append(f"  {k}: {v}")
        # Descripcion larga (hasta 1200 chars, incluye seccion de caracteristicas)
        if ficha.get("descripcion"):
            partes.append(f"- Descripcion: {ficha['descripcion']}")
        if ficha.get("caracteristicas"):
            partes.append(f"- Caracteristicas: {ficha['caracteristicas']}")
        # Atributos Akeneo (datos comerciales extra: peso, idioma teclado, garantia, etc.)
        if ficha.get("atributos_akeneo"):
            partes.append("- Atributos comerciales:")
            for k, v in ficha["atributos_akeneo"].items():
                partes.append(f"  {k}: {v}")
        sku = ficha.get("sku", "")
        partes.append(
            f"INSTRUCCION: el cliente ya escribio el SKU en su mensaje. NO llames "
            f"ver_producto ni buscar_productos — todos los datos estan en el CONTEXTO. "
            f"Cita el SKU [{sku}] entre corchetes en tu respuesta para que el sistema "
            f"muestre la tarjeta del producto."
        )
        if DetectorPedidoDetalle.es_pedido_detalle(mensaje):
            partes.append(
                "El cliente pidio DETALLES/ESPECIFICACIONES. Usa exclusivamente los datos "
                "del CONTEXTO de arriba. Lista TODAS las specs disponibles: procesador, "
                "RAM, almacenamiento, pantalla (tamanio + tipo + resolucion), GPU, bateria, "
                "puertos, conectividad, peso, sistema operativo, garantia, color y cualquier "
                "otro dato presente. No resumas en 3 bullets: si hay 10 datos, lista los 10. "
                "Si un dato no esta en la ficha, decilo explicitamente. "
                "Cierra con una pregunta de cierre de venta."
            )
        return "\n".join(partes)

    def _responder_atajo_sku(
        self,
        sesion_id: UUID,
        mensaje_usuario: str,
        directa,
        t0: float,
    ) -> ChatOutput:
        self._registrar.ejecutar(
            RegistrarMensajeCommand(
                sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=directa.texto
            )
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(mensaje_usuario),
                respuesta_len=len(directa.texto),
                tool_calls=1,
                mentiras_detectadas=0,
                productos_citados=1,
                ruta="atajo_sku",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        citados = [directa.producto] if directa.producto else []
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=directa.texto,
            productos_citados=citados,
            productos_sugeridos=self._sugeridos_para_cards(citados),
        )

    def _sugeridos_para_cards(self, productos_citados: list[dict]) -> list[dict]:
        """Genera cross-sell para cualquier short-circuit que devuelva productos.
        Centraliza la logica — asi el boton 'También podría interesarte' aparece
        consistentemente en todo el catalogo, no solo en la ruta del LLM."""
        if not productos_citados:
            return []
        skus = [str(p.get("sku") or "") for p in productos_citados if p.get("sku")]
        if not skus:
            return []
        with self._uow_factory() as uow:
            principales = uow.productos.obtener_varios([SKU(s) for s in skus])
        if not principales:
            return []
        sugeridor = SugeridorAccesoriosRelacionados(self._buscar)
        sugeridos = sugeridor.sugerir(
            principales,
            categoria=principales[0].categoria,
            subcategoria=principales[0].subcategoria,
        )
        return [ProductoSerializer.resumen(p) for p in sugeridos]

    def _responder_follow_up(
        self,
        sesion_id: UUID,
        mensaje_usuario: str,
        follow_up: RespuestaFollowUp,
        t0: float,
    ) -> ChatOutput:
        self._registrar.ejecutar(
            RegistrarMensajeCommand(
                sesion_id=sesion_id,
                rol=RolMensaje.ASSISTANT,
                contenido=follow_up.texto,
            )
        )
        if follow_up.skus:
            self._registrar_turno_mostrado.ejecutar(
                RegistrarTurnoMostradoCommand(
                    sesion_id=sesion_id,
                    skus=tuple(follow_up.skus),
                    precios=tuple(
                        float(p["precio_bob"])
                        for p in follow_up.productos
                        if p.get("precio_bob") is not None
                    ),
                )
            )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(mensaje_usuario),
                respuesta_len=len(follow_up.texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=len(follow_up.productos),
                ruta=follow_up.ruta,
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=follow_up.texto,
            productos_citados=list(follow_up.productos),
            productos_sugeridos=self._sugeridos_para_cards(list(follow_up.productos)),
            pasos=[{"tool": follow_up.ruta, "args": {}, "result": {"skus": follow_up.skus}}],
        )

    def _responder_feedback(
        self,
        sesion_id: UUID,
        mensaje_usuario: str,
        texto_cierre: str,
        t0: float,
    ) -> ChatOutput:
        self._registrar.ejecutar(
            RegistrarMensajeCommand(
                sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto_cierre
            )
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(mensaje_usuario),
                respuesta_len=len(texto_cierre),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta="feedback_post_orden",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto_cierre)

    def _curar_si_cerro_sesion(
        self, sesion_id: UUID, mentiras_detectadas: int, llevo_a_orden: bool
    ) -> None:
        if not llevo_a_orden:
            return
        mensajes = self._historial.ejecutar(
            HistorialChatQuery(sesion_id=sesion_id, limite=200)
        )
        self._curador.evaluar_y_guardar(
            sesion_id=sesion_id,
            mensajes=mensajes,
            mentiras_detectadas=mentiras_detectadas,
            llevo_a_orden=llevo_a_orden,
        )

    def _debe_forzar_busqueda(
        self, respuesta: str, trace: list[PasoAgente], mensaje: str
    ) -> bool:
        """Casos en los que el LLM no busco bien y lo corregimos:
          a) respondio listando productos sin haber llamado buscar_productos
             con resultados (alucina productos).
          b) no llamo buscar_productos en absoluto y el mensaje menciona una
             categoria reconocida (sinonimo en BD).

        NO se fuerza si el mensaje tiene un SKU explicito: el LLM respondio
        usando el contexto de la ficha y no necesita buscar."""
        if DetectorSkuMensaje.extraer(mensaje):
            return False
        busco_con_resultados = any(
            p.tool == "buscar_productos"
            and not p.result.get("error")
            and (p.result.get("total") or 0) > 0
            for p in trace
        )
        if self._parece_listado_productos(respuesta) and not busco_con_resultados:
            return True
        if any(p.tool == "buscar_productos" for p in trace):
            return False
        cercana = self._resolvedor_categoria.resolver(mensaje)
        return cercana is not None and cercana.fuente == "sinonimo"

    def _parece_listado_productos(self, respuesta: str) -> bool:
        if RX_LISTA_PRODUCTOS.search(respuesta):
            return True
        return len(RX_LISTA_NUMERADA.findall(respuesta)) >= 2

    def _necesita_manejo_ausente(
        self, respuesta: str, productos: list[dict], trace: list[PasoAgente]
    ) -> bool:
        if MARCADOR_NO_DISPONIBLE in respuesta:
            return True
        busco_con_resultados = any(
            p.tool == "buscar_productos"
            and not p.result.get("error")
            and (p.result.get("total") or 0) > 0
            for p in trace
        )
        if busco_con_resultados:
            return False
        busco_vacio = any(
            p.tool == "buscar_productos"
            and not p.result.get("error")
            and (p.result.get("total") or 0) == 0
            for p in trace
        )
        if busco_vacio and not productos:
            return True
        return bool(self._parece_listado_productos(respuesta) and not productos)

    async def _delegar_a_manejador_ausente(
        self,
        mensaje: str,
        historial: list[dict],
        trace: list[PasoAgente],
        sesion_id: UUID,
    ) -> tuple[str, list[PasoAgente], list[dict]]:
        contexto = self._contexto_textual(historial, mensaje)
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        precio_foco = self._precio_del_foco(perfil.sku_foco)
        tier_efectivo = perfil.desired_tier or (
            UmbralesTier.tier_de(precio_foco, perfil.subcategoria_efectiva())
            if precio_foco else None
        )
        piso_tier, techo_tier = UmbralesTier.rango(
            tier=tier_efectivo,
            subcategoria=perfil.subcategoria_efectiva(),
            precio_ancla=precio_foco or perfil.presupuesto_max,
        )
        precio_max_efectivo = perfil.presupuesto_max
        if techo_tier is not None:
            precio_max_efectivo = (
                min(techo_tier, precio_max_efectivo) if precio_max_efectivo else techo_tier
            )
        nombre_excluye = tuple(DetectorExclusionesMensaje.detectar(mensaje)) or None
        tipo_producto_excluye = tuple(DetectorExclusionesMensaje.tipos_a_excluir(mensaje)) or None
        res = await self._manejador_ausente.manejar(
            mensaje,
            contexto,
            categoria_activa=perfil.categoria_efectiva() or None,
            subcategoria_activa=perfil.subcategoria_efectiva() or None,
            refinamiento=DetectorRefinamientoShown.detectar(mensaje),
            marca_preferida=perfil.marca_preferida or None,
            precio_max=precio_max_efectivo,
            precio_min=piso_tier,
            nombre_excluye=nombre_excluye,
            tipo_producto_excluye=tipo_producto_excluye,
        )
        if res.categoria_ofrecida:
            self._registrar_alternativa.ejecutar(
                RegistrarAlternativaOfrecidaCommand(
                    sesion_id=sesion_id,
                    categoria=res.categoria_ofrecida,
                    subcategoria=res.subcategoria_ofrecida,
                )
            )
        trace.append(
            PasoAgente(
                tool="manejador_producto_ausente",
                args={"mensaje": mensaje},
                result={
                    "sugerencia_registrada": res.sugerencia_registrada,
                    "alternativas": len(res.productos_alternativos),
                    "categoria_ofrecida": res.categoria_ofrecida,
                },
                fallback=True,
            )
        )
        return res.texto, trace, res.productos_alternativos

    @staticmethod
    def _contexto_textual(historial: list[dict], mensaje_actual: str) -> str:
        ultimos = historial[-6:] if len(historial) > 6 else historial
        partes = [f"{m['role']}: {m['content']}" for m in ultimos]
        partes.append(f"user: {mensaje_actual}")
        return "\n".join(partes)[:2000]

    def _forzar_busqueda(
        self,
        mensaje: str,
        sesion_id: UUID,
        trace: list[PasoAgente],
        excluir_skus: tuple[str, ...] | None = None,
    ) -> tuple[str, list[PasoAgente], list[str]]:
        query, es_accesorio, perfil = self._construir_query_forzado(
            mensaje, sesion_id, excluir_skus
        )
        if not query.query and not query.categoria and not perfil.pulgadas:
            return (
                "Necesito un poco mas de contexto para buscar — decime el producto "
                "(ej. 'laptop', 'freidora', 'celular') y si tenes marca o presupuesto.",
                trace,
                [],
            )
        productos, genero_sin_resultados = self._ejecutar_query_con_fallbacks(query)
        productos = self._prepend_sku_foco(productos, perfil.sku_foco)
        productos = self._filtrar_por_gama(productos, mensaje, perfil.sku_foco)
        skus_mostrados = {s for s in (perfil.ultimos_skus_mostrados or "").split(",") if s}
        inedito = [p for p in productos if str(p.sku) not in skus_mostrados]
        productos_efectivos = inedito if inedito else productos
        sugeridos = (
            SugeridorAccesoriosRelacionados(self._buscar).sugerir(
                productos_efectivos, query.categoria, query.subcategoria
            ) if not es_accesorio else []
        )
        self._registrar_paso_forzado(
            trace, query, productos_efectivos, sugeridos, perfil, genero_sin_resultados
        )
        texto = self._texto_resultados_forzados(
            productos_efectivos, genero_sin_resultados, query
        )
        return (texto, trace, [str(p.sku) for p in productos_efectivos[:3]])

    def _construir_query_forzado(
        self,
        mensaje: str,
        sesion_id: UUID,
        excluir_skus: tuple[str, ...] | None,
    ):
        """Construye el BuscarProductosQuery para _forzar_busqueda."""
        from dataclasses import replace as dc_replace  # noqa: F401 — importado donde se usa
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        mensaje_limpio = SanitizadorQueryBusqueda.sanitizar(mensaje)
        mensaje_norm = NormalizadorTexto.normalizar(mensaje_limpio or "")
        tiene_terminos = bool(mensaje_limpio) and TokensConsulta.hay_terminos(mensaje_norm)
        cat_ef = perfil.categoria_efectiva() or None
        subcat_ef = perfil.subcategoria_efectiva() or None
        es_accesorio = DetectorConsultaAccesorio.es_consulta_accesorio(
            mensaje_limpio if tiene_terminos else None, cat_ef, subcat_ef
        )
        precio_min, precio_max_final = self._rango_precio_tier(perfil, subcat_ef)
        ram_gb_min = self._extraer_ram_gb_mensaje(mensaje)
        tipos_excluir = list(DetectorExclusionesMensaje.tipos_a_excluir(mensaje))
        if ExcluidorJuguetesDefault.debe_excluir(
            mensaje_limpio if tiene_terminos else None,
            cat_ef, subcat_ef, mensaje
        ) and "juguete" not in tipos_excluir:
            tipos_excluir.append("juguete")
        tier_pide_caros = perfil.desired_tier in ("flagship", "alto")
        query = BuscarProductosQuery(
            query=mensaje_limpio if tiene_terminos else None,
            categoria=cat_ef,
            subcategoria=subcat_ef,
            marca=perfil.marca_preferida or None,
            precio_min=precio_min,
            precio_max=precio_max_final,
            pulgadas=perfil.pulgadas,
            tipo_panel=perfil.tipo_panel,
            resolucion=perfil.resolucion,
            ram_gb_min=ram_gb_min,
            limite=12,
            excluir_accesorios=not es_accesorio,
            genero=perfil.genero_declarado or None,
            excluir_skus=excluir_skus,
            nombre_excluye=tuple(DetectorExclusionesMensaje.detectar(mensaje)) or None,
            tipo_producto_excluye=tuple(tipos_excluir) or None,
            orden_precio="desc" if tier_pide_caros else "asc",
        )
        return query, es_accesorio, perfil

    @staticmethod
    def _extraer_ram_gb_mensaje(mensaje: str) -> int | None:
        """Extrae ram_gb_min del mensaje: '16gb ram', 'ram 16gb', '16 gb de ram'."""
        import re
        m = re.search(
            r'\b(\d+)\s*gb\s+(?:de\s+)?ram\b|\bram\s+(?:de\s+)?(\d+)\s*gb\b',
            mensaje, re.IGNORECASE
        )
        if m:
            val = int(m.group(1) or m.group(2))
            return val if val in (4, 8, 12, 16, 24, 32, 48, 64) else None
        return None

    def _rango_precio_tier(self, perfil, subcat_ef: str | None) -> tuple:
        """Devuelve (precio_min, precio_max) ajustado por tier del perfil."""
        precio_foco = self._precio_del_foco(perfil.sku_foco)
        tier = perfil.desired_tier or (
            UmbralesTier.tier_de(precio_foco, subcat_ef) if precio_foco else None
        )
        piso, techo = UmbralesTier.rango(
            tier=tier,
            subcategoria=subcat_ef,
            precio_ancla=precio_foco or perfil.presupuesto_max,
        )
        precio_max = perfil.presupuesto_max
        if techo is not None:
            precio_max = min(techo, precio_max) if precio_max else techo
        return piso, precio_max

    def _ejecutar_query_con_fallbacks(
        self, query: BuscarProductosQuery
    ) -> tuple[list, bool]:
        """Ejecuta query con dos fallbacks:
        1) sin filtro de género cuando no hay resultados con género.
        2) sin query textual cuando el FULLTEXT falla con frases largas."""
        from dataclasses import replace
        productos = self._buscar.ejecutar(query)
        genero_sin_resultados = bool(query.genero) and not productos
        if genero_sin_resultados:
            productos = self._buscar.ejecutar(replace(query, genero=None))
        # Frase larga como query ("un reloj para ponerme en la mano") → FULLTEXT falla.
        # Con categoria resuelta, reintentamos sin query.
        if not productos and query.query and (query.categoria or query.subcategoria):
            productos = self._buscar.ejecutar(replace(query, query=None))
        # Filtro de panel (ej. OLED) demasiado restrictivo junto a otros filtros → sin panel.
        if not productos and query.tipo_panel:
            productos = self._buscar.ejecutar(replace(query, tipo_panel=None))
        return productos, genero_sin_resultados

    def _registrar_paso_forzado(
        self,
        trace: list[PasoAgente],
        query: BuscarProductosQuery,
        productos_efectivos: list,
        sugeridos: list,
        perfil,
        genero_sin_resultados: bool,
    ) -> None:
        args = {k: v for k, v in {
            "query": query.query, "categoria": query.categoria, "marca": query.marca,
            "precio_max": query.precio_max, "pulgadas": query.pulgadas,
            "tipo_panel": query.tipo_panel, "resolucion": query.resolucion,
            "genero": query.genero,
        }.items() if v is not None}
        resultado = {
            "productos": [ProductoSerializer.resumen(p) for p in productos_efectivos],
            "total": len(productos_efectivos),
            "sugeridos": [ProductoSerializer.resumen(p) for p in sugeridos],
        }
        if perfil.sku_foco and productos_efectivos and str(productos_efectivos[0].sku) == perfil.sku_foco:
            resultado["producto_foco_sku"] = perfil.sku_foco
        if genero_sin_resultados:
            resultado["aviso_sin_metadata_genero"] = (
                f"El catalogo no marca productos por genero '{query.genero}' "
                f"en esta subcategoria — son modelos unisex."
            )
        trace.append(PasoAgente(tool="buscar_productos", args=args, result=resultado, fallback=True))

    @staticmethod
    def _texto_resultados_forzados(
        productos_efectivos: list,
        genero_sin_resultados: bool,
        query: BuscarProductosQuery,
    ) -> str:
        if not productos_efectivos:
            return (
                "Ups, no encontre nada exacto con eso en el catalogo. "
                "Me das mas pistas? Marca preferida, presupuesto o tamanio me ayudarian un monton."
            )
        aviso = (
            f"En esta categoria no diferenciamos por genero '{query.genero}', "
            f"son modelos unisex. Igual te muestro los disponibles:\n"
            if genero_sin_resultados else ""
        )
        lineas = [f"{aviso}Estas son las opciones que te puedo ofrecer:"]
        for p in productos_efectivos[:3]:
            extra = f" (antes Bs {p.precio_anterior.monto:.0f})" if p.precio_anterior else ""
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]")
        lineas.append("Contame que te importa mas (presupuesto, marca, uso) y te ayudo a elegir.")
        return "\n".join(lineas)

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

    @staticmethod
    def _separar_sugeridos_citados(
        productos: list[dict], trace: list[PasoAgente]
    ) -> list[dict]:
        """Si el LLM cito SKUs que el cross-sell marco como 'sugeridos', los
        quitamos de productos_citados. Asi los accesorios siempre terminan en
        la seccion 'También podría interesarte' (via _extraer_sugeridos_del_trace),
        no mezclados con los productos principales."""
        skus_sugeridos: set[str] = set()
        for paso in trace:
            if paso.tool != "buscar_productos":
                continue
            for s in paso.result.get("sugeridos") or []:
                sku = s.get("sku")
                if sku:
                    skus_sugeridos.add(sku)
        if not skus_sugeridos:
            return productos
        return [p for p in productos if p.get("sku") not in skus_sugeridos]

    def _sanear_skus_y_enriquecer(
        self, respuesta: str, skus_tool: list[str]
    ) -> tuple[str, list[dict]]:
        """Valida los SKUs del texto y devuelve SOLO los productos que el LLM cita
        explicitamente entre corchetes. `skus_tool` se usa unicamente para validar
        (sanear SKUs inventados), nunca para enriquecer la UI — asi el cliente solo
        ve lo que el asistente efectivamente recomendo."""
        skus_texto = [m.group(1) for m in SKU_PATTERN.finditer(respuesta)]
        candidatos = list({*skus_texto, *skus_tool})
        if not candidatos:
            return respuesta, []

        with self._uow_factory() as uow:
            existentes = uow.productos.existen_skus(candidatos)
            orden: list[str] = []
            vistos: set[str] = set()
            for s in skus_texto:
                if s in existentes and s not in vistos:
                    vistos.add(s)
                    orden.append(s)
            productos = uow.productos.obtener_varios([SKU(s) for s in orden])
            por_sku = {str(p.sku): p for p in productos}
            productos_orden = [por_sku[s] for s in orden if s in por_sku]

        def _sub(match: re.Match[str]) -> str:
            return match.group(0) if match.group(1) in existentes else "[no disponible]"

        respuesta = SKU_PATTERN.sub(_sub, respuesta)
        return respuesta, [ProductoSerializer.detalle(p) for p in productos_orden]

    def _registrar_respuesta(self, sesion_id: UUID, respuesta: str, trace: list[PasoAgente]) -> None:
        contenido = ToolsMark.wrap(respuesta, ToolsMark.resumir(trace))
        self._registrar.ejecutar(
            RegistrarMensajeCommand(
                sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=contenido
            )
        )
