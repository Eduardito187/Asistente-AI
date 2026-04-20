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
from .detector_consulta_relativa import DetectorConsultaRelativa, TipoConsultaRelativa
from .detector_consulta_disponibilidad import DetectorConsultaDisponibilidad
from .detector_intencion_asesoria import DetectorIntencionAsesoria
from .detector_intencion_compra import DetectorIntencionCompra
from .detector_mentiras import DetectorMentiras
from .detector_pedido_detalle import DetectorPedidoDetalle
from .detector_refinamiento_shown import DetectorRefinamientoShown
from .extractor_perfil_mensaje import ExtractorPerfilMensaje
from .gestor_feedback_post_orden import GestorFeedbackPostOrden
from .gestor_follow_ups_contextuales import GestorFollowUpsContextuales
from .manejador_producto_ausente import ManejadorProductoAusente
from .normalizador_moneda import NormalizadorMoneda
from .resolvedor_categoria_cercana import ResolvedorCategoriaCercana
from .responder_consulta_disponibilidad import ResponderConsultaDisponibilidad
from .responder_consulta_politica import ResponderConsultaPolitica
from .respuesta_follow_up import RespuestaFollowUp
from .sanitizador_query_busqueda import SanitizadorQueryBusqueda
from .tools_mark import ToolsMark

SKU_PATTERN = re.compile(r"\[([A-Z0-9][A-Z0-9\-.#_]{2,40})\]")
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
        respuesta, productos = self._sanear_skus_y_enriquecer(respuesta, skus_tool)

        if self._necesita_manejo_ausente(respuesta, productos, trace):
            respuesta, trace, productos = await self._delegar_a_manejador_ausente(
                inp.mensaje, historial, trace, sesion_id
            )

        respuesta = self._cross_sell.aplicar(respuesta, trace, productos)

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

        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=ToolsMark.strip(respuesta),
            productos_citados=productos,
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
            respuesta_disp = self._responder_consulta_disp.responder(cercana)
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
            pasos=[{"tool": p.tool, "args": p.args, "result": p.result} for p in trace],
        )

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
        if ficha.get("descripcion"):
            partes.append(f"- Descripcion: {ficha.get('descripcion')}")
        partes.append(
            "INSTRUCCION: el cliente ya escribio el SKU en su mensaje. NO le pidas el "
            "SKU de vuelta ni llames ver_producto: los datos de arriba son verificados."
        )
        if DetectorPedidoDetalle.es_pedido_detalle(mensaje):
            partes.append(
                "El cliente pidio DETALLES/ESPECIFICACIONES. Enumera de forma completa "
                "TODAS las caracteristicas que encuentres en la descripcion: procesador, "
                "memoria RAM, almacenamiento, pantalla (tamanio + resolucion + tipo/panel), "
                "teclado (iluminacion/layout), GPU/grafica, bateria, puertos, conectividad, "
                "sistema operativo, peso y cualquier otra spec relevante. No resumas en "
                "3 bullets — si la descripcion trae 8 datos, lista los 8. Si un dato NO "
                "esta en la descripcion, no lo inventes: decilo explicitamente (ej: 'no "
                "tengo ese dato en la ficha'). Cierra con una pregunta que avance la venta."
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
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=directa.texto,
            productos_citados=[directa.producto] if directa.producto else [],
        )

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
             categoria reconocida (sinonimo en BD)."""
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
        res = await self._manejador_ausente.manejar(
            mensaje,
            contexto,
            categoria_activa=perfil.categoria_efectiva() or None,
            subcategoria_activa=perfil.subcategoria_efectiva() or None,
            refinamiento=DetectorRefinamientoShown.detectar(mensaje),
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
        self, mensaje: str, sesion_id: UUID, trace: list[PasoAgente]
    ) -> tuple[str, list[PasoAgente], list[str]]:
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        mensaje_limpio = SanitizadorQueryBusqueda.sanitizar(mensaje)
        mensaje_norm = NormalizadorTexto.normalizar(mensaje_limpio or "")
        tiene_terminos = bool(mensaje_limpio) and TokensConsulta.hay_terminos(mensaje_norm)
        query = BuscarProductosQuery(
            query=mensaje_limpio if tiene_terminos else None,
            categoria=perfil.categoria_efectiva() or None,
            subcategoria=perfil.subcategoria_efectiva() or None,
            marca=perfil.marca_preferida or None,
            precio_max=perfil.presupuesto_max,
            pulgadas=perfil.pulgadas,
            tipo_panel=perfil.tipo_panel,
            resolucion=perfil.resolucion,
            limite=12,
        )
        if not tiene_terminos and not perfil.categoria_efectiva() and not perfil.pulgadas:
            return (
                "Necesito un poco mas de contexto para buscar — decime el producto "
                "(ej. 'laptop', 'freidora', 'celular') y si tenes marca o presupuesto.",
                trace,
                [],
            )
        productos = self._buscar.ejecutar(query)
        skus_mostrados = {
            s for s in (perfil.ultimos_skus_mostrados or "").split(",") if s
        }
        inedito = [p for p in productos if str(p.sku) not in skus_mostrados]
        productos_efectivos = inedito if inedito else productos
        args = {k: v for k, v in {
            "query": query.query, "categoria": query.categoria, "marca": query.marca,
            "precio_max": query.precio_max, "pulgadas": query.pulgadas,
            "tipo_panel": query.tipo_panel, "resolucion": query.resolucion,
        }.items() if v is not None}
        resultado = {
            "productos": [ProductoSerializer.resumen(p) for p in productos_efectivos],
            "total": len(productos_efectivos),
        }
        trace.append(
            PasoAgente(tool="buscar_productos", args=args, result=resultado, fallback=True)
        )
        if not productos_efectivos:
            return (
                "Ups, no encontre nada exacto con eso en el catalogo. "
                "Me das mas pistas? Marca preferida, presupuesto o tamanio me ayudarian un monton.",
                trace,
                [],
            )
        lineas = ["Mira lo que tengo para vos!"]
        for p in productos_efectivos[:3]:
            extra = f" (antes Bs {p.precio_anterior.monto:.0f})" if p.precio_anterior else ""
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]")
        lineas.append("Queres que te lo agregue al carrito o te muestro mas opciones?")
        return (
            "\n".join(lineas),
            trace,
            [str(p.sku) for p in productos_efectivos[:3]],
        )

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
