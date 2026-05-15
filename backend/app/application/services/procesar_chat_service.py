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
from ..commands.auto_curar_conversacion import (
    AutoCurarConversacionCommand,
    AutoCurarConversacionHandler,
)
from ..commands.guardar_perfil_historico import (
    GuardarPerfilHistoricoCommand,
    GuardarPerfilHistoricoHandler,
)
from ..commands.registrar_synonym_candidato import (
    RegistrarSynonymCandidatoCommand,
    RegistrarSynonymCandidatoHandler,
)
from ..queries.obtener_perfil_historico import (
    ObtenerPerfilHistoricoHandler,
    ObtenerPerfilHistoricoQuery,
)
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
from .detector_tier_deseado import DetectorTierDeseado
from .detector_consulta_disponibilidad import DetectorConsultaDisponibilidad
from .detector_consulta_oferta import DetectorConsultaOferta
from .detector_exclusiones_mensaje import DetectorExclusionesMensaje
from .clasificador_etapa_conversacional import ClasificadorEtapaConversacional
from .recortador_cierres_comerciales import RecortadorCierresComerciales
from .renderizador_tabla_comparacion import RenderizadorTablaComparacion
from .limpiador_secciones_vacias import LimpiadorSeccionesVacias
from .silenciador_preguntas_redundantes import SilenciadorPreguntasRedundantes
from .normalizador_acentos_respuesta import NormalizadorAcentosRespuesta
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
from .ajustador_respuesta_formato import AjustadorRespuestaFormato
from .bloque_capacidad_hard import BloqueCapacidadHard
from .bloque_conclusion_riesgo import BloqueConclusionRiesgo
from .bloque_fallback_marca import BloqueFallbackMarca
from .bloque_formato_solicitado import BloqueFormatoSolicitado
from .bloque_freedos_warning import BloqueFreedosWarning
from .bloque_requisitos_nd import BloqueRequisitosND
from .bloque_subcategoria_excluida import BloqueSubcategoriaExcluida
from .bloque_tres_secciones_filtros import BloqueTresSeccionesFiltros
from .detector_formato_solicitado import DetectorFormatoSolicitado
from .filtros_duros_busqueda import FiltrosDurosBusqueda
from .formato_solicitado import FormatoSolicitado
from .generador_cierre_contextual import GeneradorCierreContextual
from .manejador_producto_ausente import ManejadorProductoAusente
from .parser_productos_pegados import ParserProductosPegados
from .renderizador_formato_forzado import RenderizadorFormatoForzado
from .renderizador_productos_pegados import RenderizadorProductosPegados
from .normalizador_moneda import NormalizadorMoneda
from .resolvedor_categoria_cercana import ResolvedorCategoriaCercana
from .detector_marca_mensaje import DetectorMarcaMensaje
from .detector_solicitud_similares import DetectorSolicitudSimilares
from .excluidor_juguetes_default import ExcluidorJuguetesDefault
from .detector_contradiccion_presupuesto import DetectorContradiccionPresupuesto
from .detector_prioridades_jerarquicas import DetectorPrioridadesJerarquicas
from .detector_intencion_vaga import DetectorIntentionVaga
from .detector_marca_excluida import DetectorMarcaExcluida
from .detector_gpu_dedicada import DetectorGpuDedicada
from .detector_preferencia_blanda import DetectorPreferenciaBlanda
from .reranker_por_perfil import ReRankerPorPerfil
from .responder_comparacion_explicita import ResponderComparacionExplicita
from .responder_consulta_disponibilidad import ResponderConsultaDisponibilidad
from .responder_productos_similares import ResponderProductosSimilares
from .responder_consulta_politica import ResponderConsultaPolitica
from .respuesta_follow_up import RespuestaFollowUp
from .detector_despedida import DetectorDespedida
from .detector_frustracion import DetectorFrustracion
from .detector_pregunta_tecnica import DetectorPreguntaTecnica
from .detector_indecision import DetectorIndecision
from .detector_jailbreak import DetectorJailbreak
from .detector_manipulacion import DetectorManipulacion
from .detector_pregunta_repetida import DetectorPreguntaRepetida
from .detector_saturacion_cognitiva import DetectorSaturacionCognitiva
from .detector_urgencia import DetectorUrgencia
from .detector_consulta_financiamiento import DetectorConsultaFinanciamiento
from .detector_intencion_compra_inmediata import DetectorIntencionCompraInmediata
from .detector_contexto_regalo import DetectorContextoRegalo
from .detector_ya_decidido import DetectorYaDecidido
from .detector_objecion_precio import DetectorObjecionPrecio
from .detector_upgrade_intent import DetectorUpgradeIntent
from .detector_ciudad_mencion import DetectorCiudadMencion
from .detector_objecion_factura import DetectorObjecionFactura
from .detector_objecion_devolucion import DetectorObjecionDevolucion
from .detector_variante_solicitada import DetectorVarianteSolicitada
from .detector_abandono_temporal import DetectorAbandonoTemporal
from .detector_cliente_mayorista import DetectorClienteMayorista
from .detector_cambio_tema import DetectorCambiaTema
from .detector_presupuesto_flexible import DetectorPresupuestoFlexible
from .detector_multiple_productos import DetectorMultipleProductos
from .detector_yapa_negociacion import DetectorYapaNegociacion
from .generador_bundle_regalo import GeneradorBundleRegalo
from .evaluador_frustracion_acumulada import EvaluadorFrustracionAcumulada
from .horario_atencion import HorarioAtencion
from .responder_derivar_ventas import ResponderDerivarVentas
from .responder_rechazo_jailbreak import ResponderRechazoJailbreak
from .formateador_detalle_producto import FormateadorDetalleProducto
from .resolvedor_sku_contextual import ResolvedorSkuContextual
from .skills import ContextoSkill, SkillRegistry
from .verificador_avance_turno import VerificadorAvanceTurno
from .sanitizador_query_busqueda import SanitizadorQueryBusqueda
from .tools_mark import ToolsMark
from .anunciador_fallback_marca import AnunciadorFallbackMarca
from .limpiador_emoji_spam import LimpiadorEmojiSpam
from ..commands.limpiar_perfil_sesion import LimpiarPerfilSesionCommand, LimpiarPerfilSesionHandler
from .generador_resumen_conversacion import GeneradorResumenConversacion
from .validador_sku_resultado import ValidadorSkuResultado
from .generador_link_sesion import GeneradorLinkSesion

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
        auto_curar: "AutoCurarConversacionHandler | None" = None,
        registrar_synonym: "RegistrarSynonymCandidatoHandler | None" = None,
        guardar_perfil_historico: "GuardarPerfilHistoricoHandler | None" = None,
        obtener_perfil_historico: "ObtenerPerfilHistoricoHandler | None" = None,
        skill_registry: "SkillRegistry | None" = None,
        limpiar_perfil: "LimpiarPerfilSesionHandler | None" = None,
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
        self._auto_curar = auto_curar
        self._registrar_synonym = registrar_synonym
        self._guardar_perfil_historico = guardar_perfil_historico
        self._obtener_perfil_historico = obtener_perfil_historico
        self._skill_registry = skill_registry
        self._limpiar_perfil = limpiar_perfil

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

        self._hidratar_perfil_historico_si_aplica(sesion_id, inp.mensaje)

        # Incrementa contador acumulado de frustracion en el perfil cuando se
        # detecta una señal pero NO se llega a derivar (que cortaria el flujo).
        # Esto alimenta a EvaluadorFrustracionAcumulada para el siguiente turno.
        self._incrementar_frustracion_si_aplica(sesion_id, inp.mensaje)

        if DetectorCambiaTema.es_cambio_tema(inp.mensaje) and self._limpiar_perfil:
            self._limpiar_perfil.ejecutar(LimpiarPerfilSesionCommand(sesion_id=sesion_id))

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

        sc_manip = self._short_circuit_manipulacion(inp=inp, sesion_id=sesion_id, t0=t0)
        if sc_manip is not None:
            return sc_manip

        # Intento de prompt injection / role hijacking: cambiar identidad del
        # agente, override de instrucciones, cambio de tienda, inyección
        # estructural. Distinto de manipulación comercial — corta antes del LLM.
        sc_jailbreak = self._short_circuit_jailbreak(inp=inp, sesion_id=sesion_id, t0=t0)
        if sc_jailbreak is not None:
            return sc_jailbreak

        # Cliente frustrado: pide humano, insulta al bot, o acumula 2+ señales
        # de queja. Lo derivamos a ventas telefonicas antes de gastar tokens
        # en un turno donde el cliente ya se canso del bot.
        sc_frustracion = self._short_circuit_frustracion(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if sc_frustracion is not None:
            return sc_frustracion

        # Saturación crítica: 15+ productos vistos sin items en carrito.
        # El cliente está en parálisis de decisión — derivamos a humano
        # antes de seguir mostrando opciones que no van a destrabar.
        sc_saturacion = self._short_circuit_saturacion_critica(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if sc_saturacion is not None:
            return sc_saturacion

        # Skills custom del usuario (auto-descubiertos en app/skills/).
        # Se evalúan después de defensas y antes de atajos UI: si un skill
        # devuelve respuesta, corta el turno; si solo devuelve contexto,
        # se inyecta más abajo en _contexto_del_turno.
        sc_skill = self._short_circuit_skill(inp=inp, sesion_id=sesion_id, t0=t0)
        if sc_skill is not None:
            return sc_skill

        # Boton 'Similares' del card: atajo determinista antes de cualquier
        # otro detector (follow-ups, atajos) que pueda distraer el flujo.
        similares_sc = self._short_circuit_similares(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if similares_sc is not None:
            return similares_sc

        # Productos pegados: si el cliente pego >=2 lineas con specs (marca
        # + ram/ssd/precio), gana SOBRE atajo_sku — el cliente quiere comparar
        # lo pegado, no que lookee 'asus x515' como alias del catalogo.
        sc_pegados = self._short_circuit_productos_pegados(inp, sesion_id, t0)
        if sc_pegados is not None:
            return sc_pegados

        sku_directo = self._atajo_sku.resolver(inp.mensaje, sesion_id)
        if sku_directo is not None:
            return self._responder_atajo_sku(sesion_id, inp.mensaje, sku_directo, t0)

        # Pedido de detalle pronominal: "sus características", "más info", "specs"
        # SIN nombrar producto. Resolvemos el SKU desde el contexto persistido
        # (sku_foco / ultimos_skus_mostrados / historial assistant) y devolvemos
        # ficha completa formateada — sin pasar por el LLM.
        sc_detalle = self._short_circuit_detalle_contextual(
            inp=inp, sesion_id=sesion_id, t0=t0
        )
        if sc_detalle is not None:
            return sc_detalle

        ordinal = self._atajo_ordinal.resolver(inp.mensaje, sesion_id)
        if ordinal is not None:
            return self._responder_follow_up(sesion_id, inp.mensaje, ordinal, t0)

        politica = ResponderConsultaPolitica.responder(inp.mensaje)
        if politica is not None:
            return self._responder_follow_up(sesion_id, inp.mensaje, politica, t0)

        if DetectorConsultaOferta.es_consulta_oferta(inp.mensaje):
            return self._responder_consulta_oferta(sesion_id, inp, t0)

        follow_up = self._gestor_follow_ups.intentar(inp.mensaje, sesion_id)
        if follow_up is not None:
            return self._responder_follow_up(sesion_id, inp.mensaje, follow_up, t0)

        if DetectorIntentionVaga.es_vaga(inp.mensaje):
            return self._responder_intencion_vaga(sesion_id, inp, t0)

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
        respuesta = NormalizadorAcentosRespuesta.normalizar(respuesta)
        if productos:
            respuesta = LimpiadorListaProductos.limpiar(respuesta)

        respuesta, trace, productos, skus_tool = self._evitar_lista_repetida(
            respuesta, productos, trace, skus_tool, inp.mensaje, sesion_id
        )

        if self._necesita_manejo_ausente(respuesta, productos, trace):
            respuesta, trace, productos = await self._delegar_a_manejador_ausente(
                inp.mensaje, historial, trace, sesion_id
            )

        respuesta = AnunciadorFallbackMarca.aplicar(respuesta, inp.mensaje, productos)
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
        tiempo_ms = int((time.monotonic() - t0) * 1000)
        self._auto_curar_si_exitoso(
            sesion_id, inp.mensaje, respuesta, productos, "agente", tiempo_ms, mentiras_detectadas
        )
        self._registrar_synonym_candidato_si_no_resuelve(inp.mensaje, productos, trace)
        self._persistir_perfil_historico_si_compra(sesion_id, inp.mensaje, trace, productos)

        # Verificador de avance: detecta turnos circulares para metric / debug.
        avanzo = self._evaluar_avance_turno(respuesta, productos, sesion_id, trace)
        busquedas_sin_resultado = not productos and any(
            p.tool == "buscar_productos" for p in trace
        )

        from ..chat.system_prompt import PROMPT_VERSION
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(respuesta),
                tool_calls=len(trace),
                mentiras_detectadas=mentiras_detectadas,
                productos_citados=len(productos),
                ruta="agente" if avanzo else "agente_sin_avance",
                tiempo_ms=tiempo_ms,
                prompt_version=PROMPT_VERSION,
                variant_name=getattr(self._agente, "variante_actual", None),
                busquedas_sin_resultado=busquedas_sin_resultado,
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

    def _short_circuit_productos_pegados(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Cuando el cliente pega varios productos con specs (formato libre),
        no buscamos en catalogo — comparamos lo que pego deterministicamente.
        Caso: 'asus tuf f16 i5 16 ram 512 bs 10699 / asus x515 i7 16 ram 512 bs 10799 / ...'.
        Antes: bot decia 'no tenemos similares'. Ahora: tabla comparativa."""
        listado = ParserProductosPegados.parsear(inp.mensaje)
        if listado.vacio():
            return None
        texto = RenderizadorProductosPegados.renderizar(listado)
        if not texto:
            return None
        trace = [
            PasoAgente(
                tool="parser_productos_pegados",
                args={"n_productos": len(listado.productos)},
                result={"productos": [p.raw[:80] for p in listado.productos]},
                fallback=True,
            )
        ]
        self._registrar_respuesta(sesion_id, texto, trace)
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta="productos_pegados",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

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

    def _short_circuit_manipulacion(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        if not DetectorManipulacion.es_manipulacion(inp.mensaje):
            return None
        texto = DetectorManipulacion.respuesta_rechazo()
        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto)
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta="rechazo_manipulacion",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

    def _short_circuit_jailbreak(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Si el cliente intenta cambiar identidad/rol/instrucciones del
        agente (prompt injection / role hijacking), corta el turno con
        una respuesta firme que reafirma identidad. Métrica:
        ruta=rechazo_jailbreak_<tipo> para análisis posterior."""
        tipo = DetectorJailbreak.tipo(inp.mensaje)
        if tipo is None:
            return None
        texto = ResponderRechazoJailbreak.responder(tipo)
        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto)
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta=f"rechazo_jailbreak_{tipo}",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

    def _short_circuit_frustracion(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Deriva al canal humano en dos casos:
        1. Frustración inmediata: el mensaje actual cruza el umbral del
           DetectorFrustracion (pide humano, insulta, 2+ señales medias).
        2. Frustración acumulada: el cliente acumula 3+ señales en sus
           últimos 5 mensajes (deterioro progresivo). Lee del historial
           sin necesidad de cambios de schema.
        Cierra el turno sin LLM en ambos casos."""
        motivo = self._motivo_derivacion(inp.mensaje, sesion_id)
        if motivo is None:
            return None
        # Construir resumen de conversación para el agente humano receptor.
        try:
            historial_raw = self._historial.ejecutar(
                HistorialChatQuery(sesion_id=sesion_id, limite=MAX_HISTORIAL)
            )
            perfil_h = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
            perfil_txt = GeneradorResumenConversacion.resumen_perfil(
                categoria=perfil_h.categoria_foco,
                presupuesto=perfil_h.presupuesto_max,
                marca=perfil_h.marca_preferida,
                ciudad=getattr(perfil_h, "ciudad_sesion", None),
            )
            resumen = GeneradorResumenConversacion.resumir(
                historial_user=[m.contenido for m in historial_raw if m.rol == RolMensaje.USER],
                historial_assistant=[m.contenido for m in historial_raw if m.rol == RolMensaje.ASSISTANT],
                perfil_resumen=perfil_txt,
            )
        except Exception:
            resumen = None
        # Variante A/B + horario adaptativo. La variante asignada queda en
        # la métrica (`ruta=derivar_ventas_<motivo>_<variante>`) para análisis.
        texto = ResponderDerivarVentas.responder(
            motivo="frustracion", sesion_id=sesion_id, resumen_conversacion=resumen
        )
        variante = ResponderDerivarVentas.variante_asignada(sesion_id)
        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto)
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta=f"derivar_ventas_{motivo}_{variante}",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

    def _short_circuit_saturacion_critica(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Si el cliente vio 15+ productos sin agregar nada al carrito, está
        en parálisis de decisión severa. El bloque de contexto LLM ya no
        alcanza — derivamos a un asesor humano que pueda hacer 2 preguntas
        cara a cara y cerrar la venta."""
        try:
            perfil = self._obtener_perfil.ejecutar(
                ObtenerPerfilSesionQuery(sesion_id=sesion_id)
            )
            skus = DetectorSaturacionCognitiva.contar_skus_acumulados(
                perfil.ultimos_skus_mostrados
            )
            carrito = self._ver_carrito_handler_si_existe(sesion_id)
            items = len(carrito.items) if carrito else 0
        except Exception:
            return None
        if not DetectorSaturacionCognitiva.es_critico(skus, items):
            return None
        texto = ResponderDerivarVentas.responder(
            motivo="saturacion", sesion_id=sesion_id
        )
        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto)
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta=f"derivar_ventas_saturacion_{skus}skus",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

    def _short_circuit_skill(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Si algún skill custom (auto-descubierto en app/skills/) decide
        cortar el flujo con respuesta directa, ejecuta y registra."""
        if self._skill_registry is None or self._skill_registry.cuenta() == 0:
            return None
        ctx = self._construir_contexto_skill(inp.mensaje, sesion_id)
        if ctx is None:
            return None
        match = self._skill_registry.short_circuit_respuesta(ctx)
        if match is None:
            return None
        nombre_skill, texto = match
        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto)
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta=f"skill_{nombre_skill}",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

    def _short_circuit_detalle_contextual(
        self,
        inp: ChatInput,
        sesion_id: UUID,
        t0: float,
    ) -> ChatOutput | None:
        """Resuelve 'cuéntame más / sus características / dame las specs'
        cuando el cliente NO menciona SKU pero hay uno claro en el contexto
        (sku_foco, último mostrado, último citado por el assistant). Llama
        ver_producto y formatea ficha completa — todo determinístico,
        sin LLM, para que NUNCA pierda el hilo entre turnos."""
        if not DetectorPedidoDetalle.es_pedido_detalle(inp.mensaje):
            return None
        # "cual me conviene X o Y" es comparación, no pedido de detalle de contexto.
        if DetectorComparacionExplicita.detectar(inp.mensaje) is not None:
            return None
        # "comparame los anteriores", "más barato", "otra opción" son follow-ups
        # de contexto — los maneja GestorFollowUps, no este short-circuit.
        if DetectorConsultaRelativa.detectar(inp.mensaje) is not None:
            return None
        # Mensajes largos o multi-línea son búsquedas nuevas con requisitos,
        # no pedidos de detalle de un producto previo ("más info", "sus specs").
        if len(inp.mensaje) > 120 or "\n" in inp.mensaje:
            return None
        # Si ya hay SKU en el mensaje actual, lo maneja AtajoSkuDirecto.
        if DetectorSkuMensaje.extraer(inp.mensaje):
            return None
        try:
            perfil = self._obtener_perfil.ejecutar(
                ObtenerPerfilSesionQuery(sesion_id=sesion_id)
            )
            historial_assistant = self._historial_solo_assistant(sesion_id)
            historial_user = self._historial_solo_user(sesion_id)
        except Exception:
            return None
        sku = ResolvedorSkuContextual.resolver(
            perfil,
            historial_assistant=historial_assistant,
            historial_user=historial_user,
        )
        if not sku:
            return None
        try:
            ficha = self._dispatcher.ejecutar("ver_producto", {"sku": sku}, sesion_id)
        except Exception:
            return None
        if not ficha or ficha.get("error"):
            return None
        texto = FormateadorDetalleProducto.formatear(ficha)
        self._registrar.ejecutar(
            RegistrarMensajeCommand(sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto)
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=1,
                mentiras_detectadas=0,
                productos_citados=1,
                ruta="detalle_contextual",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=texto,
            productos_citados=[ficha],
        )

    def _historial_solo_assistant(self, sesion_id: UUID) -> list[str]:
        """Helper: extrae solo los mensajes del assistant del historial,
        cronológico. Usado por ResolvedorSkuContextual para encontrar
        SKUs `[XXX]` que el agente citó previamente."""
        mensajes = self._historial.ejecutar(
            HistorialChatQuery(sesion_id=sesion_id, limite=MAX_HISTORIAL)
        )
        return [m.contenido for m in mensajes if m.rol == RolMensaje.ASSISTANT]

    def _construir_contexto_skill(self, mensaje: str, sesion_id: UUID) -> ContextoSkill | None:
        """Arma el ContextoSkill leyendo perfil + historial UNA vez para
        que múltiples skills no hagan N consultas a la BD."""
        try:
            from datetime import datetime, timezone
            perfil = self._obtener_perfil.ejecutar(
                ObtenerPerfilSesionQuery(sesion_id=sesion_id)
            )
            historial_user = self._historial_solo_user(sesion_id)
            return ContextoSkill(
                mensaje=mensaje,
                sesion_id=sesion_id,
                perfil=perfil,
                historial_user=historial_user,
                ahora=datetime.now(timezone.utc),
            )
        except Exception:
            return None

    def _bloque_skills(self, mensaje: str, sesion_id: UUID) -> str | None:
        """Concatena los bloques de contexto de todos los skills activos
        para inyectar al system prompt del LLM."""
        if self._skill_registry is None or self._skill_registry.cuenta() == 0:
            return None
        ctx = self._construir_contexto_skill(mensaje, sesion_id)
        if ctx is None:
            return None
        bloques = self._skill_registry.bloques_contexto(ctx)
        if not bloques:
            return None
        return "\n\n".join(
            f"=== SKILL «{nombre}» ===\n{texto}"
            for nombre, texto in bloques
        )

    def _motivo_derivacion(self, mensaje: str, sesion_id: UUID) -> str | None:
        """Devuelve 'alto'/'medio' (frustración inmediata), 'acumulada'
        (deterioro progresivo) o None (sin derivación).

        Guard contra falsos positivos: si la unica senal es 'no sirve/no
        funciona/insulto' (que puede ser pregunta tecnica como 'sirve este
        modelo o no?'), NO derivamos cuando el mensaje es claramente una
        pregunta tecnica. Solo `pidio_humano_explicito` (pase a humano,
        whatsapp, telefono) NO se bloquea NUNCA."""
        # Pidio humano explicito: deriva siempre.
        if DetectorFrustracion.pidio_humano_explicito(mensaje):
            return DetectorFrustracion.nivel(mensaje)
        # Pregunta tecnica: bloquea cualquier otro motivo (alto-falso, medio,
        # acumulada). El cliente esta consultando, no pidiendo humano.
        if DetectorPreguntaTecnica.es_pregunta_tecnica(mensaje):
            return None
        if DetectorFrustracion.debe_derivar(mensaje):
            return DetectorFrustracion.nivel(mensaje)
        mensajes_user = self._historial_solo_user(sesion_id)
        if EvaluadorFrustracionAcumulada.debe_derivar(mensajes_user, mensaje):
            return "acumulada"
        return None

    def _historial_solo_user(self, sesion_id: UUID) -> list[str]:
        """Helper: extrae solo los mensajes del cliente (rol=user) del
        historial de chat, en orden cronológico."""
        mensajes = self._historial.ejecutar(
            HistorialChatQuery(sesion_id=sesion_id, limite=MAX_HISTORIAL)
        )
        return [m.contenido for m in mensajes if m.rol == RolMensaje.USER]

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

    def _responder_consulta_oferta(
        self,
        sesion_id: UUID,
        inp: ChatInput,
        t0: float,
    ) -> ChatOutput:
        """Short-circuit para consultas de ofertas/descuentos: busca productos
        con precio_anterior_bob > precio_bob y responde sin pasar por el LLM."""
        from dataclasses import replace as dc_replace
        query, _, perfil_of = self._construir_query_forzado(inp.mensaje, sesion_id, None)
        cat_of = perfil_of.categoria_efectiva() or None
        query = dc_replace(
            query,
            solo_en_oferta=True,
            categoria=cat_of,
            query=None,
            limite=12,
        )
        productos = self._buscar.ejecutar(query)
        if not productos:
            texto = "Ahora mismo no encontré productos con descuento activo. Volvé a consultar pronto."
        else:
            items = "\n".join(
                f"- {p.nombre} — Bs {p.precio.monto:,.0f} (antes Bs {p.precio_anterior.monto:,.0f}) [{p.sku}]"
                for p in productos[:6]
                if p.precio_anterior
            )
            texto = f"Estos productos están en oferta ahora:\n{items}"
        productos_citados = [ProductoSerializer.detalle(p) for p in productos[:6]]
        trace = [PasoAgente(tool="buscar_productos", args={"solo_en_oferta": True},
                            result={"total": len(productos)}, fallback=True)]
        self._registrar_respuesta(sesion_id, texto, trace)
        self._persistir_turno_mostrado(sesion_id, productos_citados)
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=1,
                mentiras_detectadas=0,
                productos_citados=len(productos_citados),
                ruta="oferta",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(
            sesion_id=sesion_id,
            respuesta=texto,
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
        if self._cercana_contradice_perfil_bloqueado(cercana, sesion_id, inp.mensaje):
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

    def _cercana_contradice_perfil_bloqueado(
        self, cercana, sesion_id: UUID, mensaje: str
    ) -> bool:
        """Si el perfil ya tiene una categoria bloqueada (de turnos anteriores)
        y la 'cercana' inferida del mensaje cae en otra categoria distinta, NO
        cortocircuites: muy probablemente sea ruido de n-grama (ej. 'civil 3D'
        matcheando 'Basculas' por la palabra 'civil'). Solo se permite el
        cambio si el cliente lo pidio explicito."""
        from .detector_cambio_categoria import DetectorCambioCategoria
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        cat_bloqueada = perfil.categoria_efectiva()
        if not cat_bloqueada:
            return False
        cat_cercana = (cercana.categoria or "").lower()
        cat_bloq = cat_bloqueada.lower()
        prefix = min(len(cat_cercana), len(cat_bloq), 5)
        if prefix >= 5 and cat_cercana[:prefix] == cat_bloq[:prefix]:
            return False
        if DetectorCambioCategoria.hay_cambio(mensaje):
            return False
        return True

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
        respuesta = NormalizadorAcentosRespuesta.normalizar(respuesta)
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
        respuesta = LimpiadorSeccionesVacias.limpiar(respuesta)
        respuesta = SilenciadorPreguntasRedundantes.silenciar(respuesta, perfil)
        respuesta = RecortadorCierresComerciales.recortar(respuesta, etapa)
        # Caps duros del formato pedido por el cliente — corre AL FINAL
        # para que tope la respuesta ya saneada (no las plantillas vacias).
        fmt = DetectorFormatoSolicitado.detectar(mensaje)
        respuesta = AjustadorRespuestaFormato.ajustar(respuesta, fmt)
        return LimpiadorEmojiSpam.limpiar(respuesta)

    def _contexto_del_turno(self, mensaje: str, sesion_id: UUID) -> str | None:
        bloques = [
            self._bloque_perfil(sesion_id),
            self._bloque_categoria_bloqueada(sesion_id),
            self._bloque_shown_products(sesion_id),
            self._bloque_intencion(mensaje),
            self._bloque_consulta_relativa(mensaje),
            self._bloque_intencion_compra(mensaje),
            self._bloque_sku(mensaje, sesion_id),
            self._bloque_exclusiones(mensaje),
            self._bloque_preferencia_blanda(mensaje),
            self._bloque_prioridades(mensaje),
            self._bloque_formato_tres_opciones(mensaje),
            self._bloque_formato_solicitado(mensaje),
            BloqueRequisitosND.renderizar(mensaje),
            BloqueFreedosWarning.renderizar(mensaje),
            BloqueFallbackMarca.renderizar(mensaje),
            BloqueConclusionRiesgo.renderizar(mensaje),
            BloqueCapacidadHard.renderizar(mensaje),
            BloqueSubcategoriaExcluida.renderizar(mensaje),
            BloqueTresSeccionesFiltros.renderizar(mensaje),
            self._bloque_no_humo(mensaje),
            # === Bloques de tono / decisión (no cortan flujo, ajustan al LLM) ===
            self._bloque_frustracion_baja(mensaje),
            self._bloque_indecision(mensaje),
            self._bloque_urgencia(mensaje),
            self._bloque_financiamiento(mensaje),
            self._bloque_compra_inmediata(mensaje),
            self._bloque_regalo(mensaje),
            self._bloque_ya_decidido(mensaje),
            self._bloque_objecion_precio(mensaje),
            self._bloque_upgrade_intent(mensaje),
            self._bloque_ciudad(sesion_id),
            self._bloque_objecion_factura(mensaje),
            self._bloque_objecion_devolucion(mensaje),
            self._bloque_variante_solicitada(mensaje),
            self._bloque_abandono_temporal(mensaje, sesion_id),
            self._bloque_cliente_mayorista(mensaje),
            self._bloque_cambio_tema(mensaje),
            self._bloque_presupuesto_flexible(mensaje),
            self._bloque_multiple_productos(mensaje),
            self._bloque_yapa(mensaje),
            self._bloque_despedida(mensaje, sesion_id),
            self._bloque_saturacion_cognitiva(sesion_id),
            self._bloque_pregunta_repetida(mensaje, sesion_id),
            self._bloque_cliente_recurrente(mensaje),
            self._bloque_mensaje_vacio(mensaje, sesion_id),
            # Skills custom del usuario (auto-descubiertos): se inyectan
            # como un único bloque concatenado al final del system prompt.
            self._bloque_skills(mensaje, sesion_id),
        ]
        bloques_validos = [b for b in bloques if b]
        return "\n\n".join(bloques_validos) if bloques_validos else None

    # ===== Bloques nuevos =====================================================

    @staticmethod
    def _bloque_frustracion_baja(mensaje: str) -> str | None:
        """Cuando hay UNA señal blanda (no deriva pero hay tensión), pide al
        LLM bajar el tono comercial y ser empático/conciso. Si fuera 2+
        señales ya estaríamos en derivación — esto previene escalación."""
        if DetectorFrustracion.debe_derivar(mensaje):
            return None
        if DetectorFrustracion.nivel(mensaje) != "bajo":
            return None
        return (
            "TONO ESTE TURNO: el cliente muestra señal de impaciencia. "
            "Respondé corto y empático (sin disculparte mil veces). Sin frases "
            "comerciales largas, sin múltiples opciones — UNA respuesta directa. "
            "Si ya hay productos mostrados, reusalos en vez de listar nuevos."
        )

    @staticmethod
    def _bloque_indecision(mensaje: str) -> str | None:
        if not DetectorIndecision.es_indeciso(mensaje):
            return None
        return (
            "MODO DECISIVO: el cliente está indeciso y pide que elijas por él. "
            "REGLAS:\n"
            "- Elegí UN solo producto (no dos, no tres) de los que ya mostraste "
            "  o de la búsqueda actual.\n"
            "- Justificá la elección en 1-2 líneas con características concretas.\n"
            "- NO abras búsqueda nueva ni listes alternativas.\n"
            "- NO digas 'depende de tu uso' si ya tenés contexto del cliente.\n"
            "- Cerrá ofreciendo agregar al carrito."
        )

    @staticmethod
    def _bloque_urgencia(mensaje: str) -> str | None:
        if not DetectorUrgencia.es_urgente(mensaje):
            return None
        return (
            "URGENCIA DETECTADA: el cliente necesita el producto pronto. "
            "Al llamar buscar_productos pasá `solo_con_stock=True`. Si está "
            "disponible la opción `envio_rapido=True` priorizala. En la "
            "respuesta mencioná explícitamente disponibilidad y, si lo sabés, "
            "tiempos de entrega/retiro. Si no hay producto con stock, ofrecé "
            "el más cercano disponible y avisá del tiempo extra."
        )

    @staticmethod
    def _bloque_financiamiento(mensaje: str) -> str | None:
        if not DetectorConsultaFinanciamiento.es_consulta_financiamiento(mensaje):
            return None
        return (
            "CONSULTA DE FINANCIAMIENTO: el cliente pregunta sobre formas de pago "
            "(cuotas, QR, Tigo Money, tarjeta, transferencia, crédito). "
            "Menciona las opciones disponibles en Dismac: pagos con QR (Tigo Money, "
            "BCP), tarjetas Visa/Mastercard, transferencias bancarias. "
            "Si hay planes de cuotas disponibles para el producto, inclúyelos. "
            "Sé concreto con montos y condiciones. No inventes tasas de interés."
        )

    @staticmethod
    def _bloque_compra_inmediata(mensaje: str) -> str | None:
        if not DetectorIntencionCompraInmediata.es_compra_inmediata(mensaje):
            return None
        return (
            "COMPRA INMEDIATA: el cliente ya decidió y quiere cerrar ahora "
            "('lo llevo', 'de frente', 'de una', 'al tiro', 'jalo ese', etc.). "
            "NO listes más alternativas. Acción prioritaria: (1) confirmá el SKU "
            "elegido con agregar_al_carrito, (2) pedí datos de contacto mínimos "
            "(nombre), (3) cerrá con confirmar_orden. Tono: breve y eficiente."
        )

    @staticmethod
    def _bloque_regalo(mensaje: str) -> str | None:
        if not DetectorContextoRegalo.es_regalo(mensaje):
            return None
        destinatario = DetectorContextoRegalo.destinatario(mensaje)
        dest_txt = f" para {destinatario}" if destinatario else ""
        base = (
            f"CONTEXTO DE REGALO: el cliente busca un producto como regalo{dest_txt}. "
            "Priorizá opciones con buena presentación, dentro de un rango de precio "
            "moderado (salvo que pida premium). Si no está claro el destinatario ni su uso, "
            "preguntá brevemente ('¿para quién es? ¿qué uso le dará?'). "
            "Evitá modelos refurbished o con packaging deteriorado."
        )
        return base

    @staticmethod
    def _bloque_ya_decidido(mensaje: str) -> str | None:
        if not DetectorYaDecidido.es_ya_decidido(mensaje):
            return None
        return (
            "CLIENTE YA DECIDIDO: llegó con un producto específico en mente "
            "(se lo recomendaron, lo vio en redes, ya eligió). "
            "NO ofrezcas alternativas ni hagas exploración. Acción: "
            "(1) confirmá disponibilidad del producto mencionado, "
            "(2) informá precio y condiciones, "
            "(3) guiá directo al carrito si hay stock."
        )

    @staticmethod
    def _bloque_objecion_precio(mensaje: str) -> str | None:
        if not DetectorObjecionPrecio.es_objecion_precio(mensaje):
            return None
        competidor = DetectorObjecionPrecio.menciona_competidor(mensaje)
        comp_txt = f" (menciona {competidor})" if competidor else ""
        return (
            f"OBJECIÓN DE PRECIO detectada{comp_txt}: el cliente dice que está caro "
            "o que lo vio más barato en otro lado. Respuesta correcta: "
            "(1) reconocé la objeción sin ponerte defensivo, "
            "(2) diferenciá con garantía oficial, servicio técnico propio, "
            "financiamiento disponible, y respaldo post-venta de Dismac, "
            "(3) si aplica, ofrecer una cuota accesible o un modelo similar con mejor precio. "
            "NUNCA inventes precios de la competencia ni digas que no podés igualar."
        )

    @staticmethod
    def _bloque_upgrade_intent(mensaje: str) -> str | None:
        if not DetectorUpgradeIntent.es_upgrade(mensaje):
            return None
        producto_actual = DetectorUpgradeIntent.producto_actual(mensaje)
        prod_txt = f" (tiene actualmente: {producto_actual})" if producto_actual else ""
        return (
            f"UPGRADE INTENT: el cliente quiere reemplazar un producto que ya tiene{prod_txt}. "
            "Estrategia: (1) preguntá brevemente qué le faltó o falló en el actual "
            "(si no está claro), (2) recomendá mejora concreta sobre ese punto, "
            "(3) no des opciones entry-level si hay señal de que ya usó algo similar. "
            "El cliente tiene experiencia con la categoría — tratalo como usuario intermedio."
        )

    @staticmethod
    def _bloque_objecion_factura(mensaje: str) -> str | None:
        tipo = DetectorObjecionFactura.tipo(mensaje)
        if tipo is None:
            return None
        if tipo == "sin_factura":
            return (
                "CONSULTA SIN FACTURA: el cliente pregunta por precio sin factura. "
                "Respuesta: la factura es obligatoria por ley en Bolivia y está incluida "
                "en el precio. No hay precio diferente sin factura. Enfatizá los beneficios: "
                "garantía oficial, reclamo ante defecto, deducción de impuestos si aplica."
            )
        if tipo == "con_factura":
            return (
                "CONSULTA CON FACTURA: el cliente quiere confirmar que incluye factura. "
                "Confirmá que sí, que la factura está siempre incluida en el precio de Dismac."
            )
        return (
            "FACTURA EMPRESARIAL: el cliente necesita factura a nombre de empresa/NIT. "
            "Indicá que pueden emitir factura empresarial con NIT y razón social. "
            "Pedirle que tenga a mano el NIT y razón social al momento de comprar."
        )

    @staticmethod
    def _bloque_objecion_devolucion(mensaje: str) -> str | None:
        if not DetectorObjecionDevolucion.es_consulta_devolucion(mensaje):
            return None
        return (
            "CONSULTA DE DEVOLUCIÓN/GARANTÍA: el cliente pregunta por política de cambios. "
            "Informá: (1) productos con defecto de fábrica tienen garantía oficial del fabricante "
            "(varía por producto, típicamente 1 año), (2) Dismac gestiona el reclamo ante el "
            "fabricante, (3) para cambio por no gustar, consultar política en tienda según el "
            "producto. NO inventes plazos específicos que no conozcas."
        )

    @staticmethod
    def _bloque_variante_solicitada(mensaje: str) -> str | None:
        if not DetectorVarianteSolicitada.es_variante(mensaje):
            return None
        partes = ["VARIANTE SOLICITADA: el cliente busca una variante específica."]
        color = DetectorVarianteSolicitada.color(mensaje)
        if color:
            partes.append(f"- Color pedido: {color}")
        cap = DetectorVarianteSolicitada.capacidad_gb(mensaje)
        if cap:
            partes.append(f"- Capacidad pedida: {cap} GB")
        partes.append(
            "Al buscar productos, intentá filtrar o mencionar explícitamente si "
            "hay disponibilidad de esa variante. Si no hay, indicá las disponibles."
        )
        return "\n".join(partes)

    def _bloque_abandono_temporal(self, mensaje: str, sesion_id: UUID) -> str | None:
        if not DetectorAbandonoTemporal.es_abandono_temporal(mensaje):
            return None
        link_txt = GeneradorLinkSesion.mensaje_retoma(sesion_id)
        return (
            "ABANDONO TEMPORAL: el cliente quiere pausar y volver después. "
            "Respuesta ideal: (1) confirmá que su sesión queda guardada, "
            f"(2) compartí el código de retoma: {link_txt}, "
            "(3) ofrecé resumir los productos que vio para cuando vuelva, "
            "(4) despedida cálida y breve. No insistas en cerrar la venta ahora."
        )

    @staticmethod
    def _bloque_cliente_mayorista(mensaje: str) -> str | None:
        if not DetectorClienteMayorista.es_mayorista(mensaje):
            return None
        cantidad = DetectorClienteMayorista.cantidad_aproximada(mensaje)
        cant_txt = f" (menciona {cantidad} unidades)" if cantidad else ""
        return (
            f"CLIENTE MAYORISTA{cant_txt}: compra en cantidad para negocio/reventa. "
            "Este cliente requiere atención especial: "
            "(1) indicá que para pedidos mayoristas deben contactar al área comercial, "
            "(2) preguntá qué producto y cantidad necesita para derivar correctamente, "
            "(3) NO des precios unitarios como si fuera precio mayorista — el precio "
            "publicado es para consumidor final."
        )

    @staticmethod
    def _bloque_cambio_tema(mensaje: str) -> str | None:
        if not DetectorCambiaTema.es_cambio_tema(mensaje):
            return None
        return (
            "CAMBIO DE TEMA EXPLÍCITO: el cliente abandonó lo anterior y quiere buscar algo nuevo. "
            "Ignorá completamente el contexto previo (productos mostrados, categoría anterior). "
            "Tratá este mensaje como el inicio de una conversación nueva. "
            "No menciones los productos anteriores."
        )

    @staticmethod
    def _bloque_presupuesto_flexible(mensaje: str) -> str | None:
        if DetectorPresupuestoFlexible.es_flexible(mensaje):
            return (
                "PRESUPUESTO FLEXIBLE: el cliente puede gastar más si la opción lo justifica. "
                "Mostrá la opción en su presupuesto declarado Y una opción premium ligeramente "
                "superior — explicá por qué vale la diferencia."
            )
        if DetectorPresupuestoFlexible.es_duro(mensaje):
            return (
                "PRESUPUESTO DURO: el cliente tiene un límite estricto que no puede superar. "
                "NO mostrés opciones por encima del presupuesto declarado. "
                "Si no hay nada en ese rango, decílo honestamente y ofrecé lo más cercano por debajo."
            )
        return None

    @staticmethod
    def _bloque_multiple_productos(mensaje: str) -> str | None:
        if not DetectorMultipleProductos.es_busqueda_multiple(mensaje):
            return None
        productos = DetectorMultipleProductos.productos_mencionados(mensaje)
        prod_txt = ", ".join(productos) if productos else "varios"
        return (
            f"BÚSQUEDA MÚLTIPLE: el cliente busca {prod_txt} en el mismo mensaje. "
            "Estrategia: (1) confirmá que vas a ayudar con ambos/todos, "
            "(2) atendé uno a la vez empezando por el que aparece primero, "
            "(3) al terminar con el primero, preguntá si seguimos con el siguiente."
        )

    @staticmethod
    def _bloque_yapa(mensaje: str) -> str | None:
        if DetectorYapaNegociacion.pide_yapa(mensaje):
            return (
                "PIDE YAPA: el cliente espera un extra con la compra. "
                "Respuesta: si el producto incluye accesorios en la caja, mencionálos. "
                "Si hay promoción activa con regalo, informála. Si no hay nada extra, "
                "explicá con amabilidad que el precio ya incluye todo."
            )
        if DetectorYapaNegociacion.pide_descuento(mensaje):
            return (
                "PIDE DESCUENTO/REBAJA: el cliente quiere negociar el precio. "
                "Respuesta: el precio es fijo (no hay regateo), pero podés destacar "
                "el valor diferencial: garantía, financiamiento, servicio técnico, "
                "o si hay descuento activo mencionalo. No prometás descuentos que no existen."
            )
        if DetectorYapaNegociacion.pide_precio_especial(mensaje):
            return (
                "PIDE PRECIO AL CONTADO/EFECTIVO: en Dismac el precio es el mismo "
                "independientemente del medio de pago. Informarlo con naturalidad "
                "y resaltar que el precio publicado ya es competitivo."
            )
        return None

    def _bloque_ciudad(self, sesion_id: UUID) -> str | None:
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        ciudad = getattr(perfil, "ciudad_sesion", None)
        if not ciudad:
            return None
        return (
            f"CIUDAD DEL CLIENTE: {ciudad}. "
            "Si hay diferencias de disponibilidad o tiempos de entrega entre "
            "ciudades, mencionálo. No supongas que todo producto tiene stock "
            "inmediato en esa ciudad — si no sabés confirmá antes de prometer."
        )

    def _bloque_despedida(self, mensaje: str, sesion_id: UUID) -> str | None:
        if not DetectorDespedida.es_despedida(mensaje):
            return None
        try:
            carrito = self._ver_carrito_handler_si_existe(sesion_id)
            tiene_compra = carrito and len(carrito.items) > 0
        except Exception:
            tiene_compra = False
        if tiene_compra:
            return (
                "CIERRE DE CONVERSACIÓN: el cliente se despide y tiene items "
                "en carrito. Cerrá con calidez y recordale el carrito pendiente "
                "(que puede confirmar la orden cuando quiera). NO empujes la "
                "venta agresivamente."
            )
        en_horario = HorarioAtencion.dentro_horario()
        contactos = (
            f"  Teléfono: {ResponderDerivarVentas.telefono()}\n"
            f"  WhatsApp: {ResponderDerivarVentas.whatsapp_numero()} "
            f"({ResponderDerivarVentas.whatsapp_link()})"
        )
        if en_horario:
            tono_horario = (
                "Tono: 'cuando quieras volver, escribime; o si preferís hablar "
                "con alguien del equipo de ventas, ahí tenés los contactos'."
            )
        else:
            cuando = HorarioAtencion.proxima_apertura()
            tono_horario = (
                f"FUERA DE HORARIO ({HorarioAtencion.descripcion_horario()}). "
                f"Mencioná que si escribe al WhatsApp ahora le responden {cuando}."
            )
        return (
            "CIERRE DE CONVERSACIÓN SIN COMPRA: el cliente se despide sin haber "
            "agregado nada al carrito. Cerrá cordial y al final ofrecé como "
            f"fallback el contacto humano de Dismac:\n{contactos}\n"
            f"{tono_horario} NO insistas."
        )

    def _bloque_saturacion_cognitiva(self, sesion_id: UUID) -> str | None:
        """Saturación escalada: medio (≥6) → bloque suave;  alto (≥10) →
        bloque enfático. El nivel crítico (≥15) lo maneja el short-circuit
        antes de llegar al LLM, así que aquí no aparece."""
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        skus_acum = DetectorSaturacionCognitiva.contar_skus_acumulados(
            perfil.ultimos_skus_mostrados
        )
        try:
            carrito = self._ver_carrito_handler_si_existe(sesion_id)
            items = len(carrito.items) if carrito else 0
        except Exception:
            items = 0
        nivel = DetectorSaturacionCognitiva.nivel(skus_acum, items)
        if nivel == DetectorSaturacionCognitiva.NIVEL_NINGUNO:
            return None
        if nivel == DetectorSaturacionCognitiva.NIVEL_ALTO:
            return (
                f"SATURACIÓN ALTA ({skus_acum} productos vistos sin decisión). "
                "REGLAS DURAS este turno:\n"
                "- PROHIBIDO abrir buscar_productos (ya viste suficiente).\n"
                "- PROHIBIDO listar productos nuevos.\n"
                "- Elegí UN solo SKU de los ya mostrados con justificación de "
                "  3-4 características concretas.\n"
                "- Si el cliente pregunta cosas vagas, preguntá UNA concreta "
                "  para destrabar (ej. '¿priorizás precio o cámara?').\n"
                "- Cerrá ofreciendo agregar al carrito."
            )
        # NIVEL_MEDIO
        return (
            f"SATURACIÓN COGNITIVA: el cliente lleva {skus_acum} productos "
            f"vistos sin decidirse (umbral {DetectorSaturacionCognitiva.umbral()}). "
            "Cambiá de estrategia: en vez de listar más opciones, recomendá UN "
            "producto concreto de los ya mostrados con justificación clara. O "
            "hacé UNA pregunta concreta para reducir el espacio (ej. "
            "'¿priorizás cámara o batería?'). NO listes más SKUs nuevos."
        )

    def _bloque_pregunta_repetida(self, mensaje: str, sesion_id: UUID) -> str | None:
        mensajes_user = self._historial_solo_user(sesion_id)
        if not DetectorPreguntaRepetida.es_repetida(mensaje, mensajes_user):
            return None
        return (
            "PREGUNTA REPETIDA: el cliente está volviendo a preguntar lo "
            "mismo (señal de que tu respuesta anterior no fue clara). "
            "REGLAS este turno:\n"
            "- Reconocé la repetición ('te explico de otra forma').\n"
            "- Respondé MÁS SIMPLE: una idea por línea, máximo 3 líneas.\n"
            "- NO listes productos nuevos.\n"
            "- Si el cliente pregunta sobre un producto/atributo específico, "
            "  contestá ese atributo concreto sin rodeos comerciales."
        )

    def _ver_carrito_handler_si_existe(self, sesion_id: UUID):
        """Devuelve el carrito o None si la lectura falla. Wrapper defensivo
        porque los bloques de contexto no deben tirar excepciones."""
        try:
            from ..queries.ver_carrito import VerCarritoQuery
            return self._dispatcher.ver_carrito.ejecutar(VerCarritoQuery(sesion_id=sesion_id))
        except Exception:
            return None

    def _bloque_cliente_recurrente(self, mensaje: str) -> str | None:
        """Cross-session memory: si el mensaje contiene email o telefono, busca
        en perfiles_historicos. Si encontramos al cliente, le avisamos al LLM
        que es recurrente y sus preferencias previas para personalizar."""
        if self._obtener_perfil_historico is None:
            return None
        from .detector_contacto_cliente import DetectorContactoCliente
        from .hasher_contacto import HasherContacto
        contacto = DetectorContactoCliente.detectar(mensaje)
        if not (contacto.email or contacto.telefono):
            return None
        contacto_hash = (
            HasherContacto.email(contacto.email) if contacto.email
            else HasherContacto.telefono(contacto.telefono)
        )
        try:
            res = self._obtener_perfil_historico.ejecutar(
                ObtenerPerfilHistoricoQuery(contacto_hash=contacto_hash)
            )
        except Exception:
            return None
        if not res or not res.encontrado:
            return None
        partes = [
            f"CLIENTE RECURRENTE: visita #{res.visitas + 1} (este es su {res.visitas + 1}º contacto)."
        ]
        if res.ultima_categoria:
            partes.append(f"- Última categoría comprada: {res.ultima_categoria}")
        if res.ultima_marca:
            partes.append(f"- Marca preferida histórica: {res.ultima_marca}")
        if res.ultima_compra_sku:
            partes.append(f"- Último SKU comprado: [{res.ultima_compra_sku}]")
        snapshot = res.perfil_snapshot or {}
        frust_h = snapshot.get("frustracion_count")
        if frust_h and frust_h >= 3:
            partes.append(
                f"- ALERTA: cliente acumuló {frust_h} señales de frustración "
                "antes. Tratá con extra cuidado, sé directo y empático."
            )
        partes.append(
            "Personalizá el saludo (sin ser invasivo, sin nombre que no diste). "
            "Si pregunta sobre la categoría histórica, asumí continuidad. "
            "Si cambia de categoría, no insistas con la anterior."
        )
        return "\n".join(partes)

    def _bloque_mensaje_vacio(self, mensaje: str, sesion_id: UUID) -> str | None:
        """Si el cliente envía 3 mensajes vacíos seguidos ('si', '?', 'ok'),
        pedile que aclare en lugar de gastar tokens en una respuesta vaga."""
        from .detector_mensajes_vacios import DetectorMensajesVacios
        mensajes_user = self._historial_solo_user(sesion_id)
        if not DetectorMensajesVacios.hay_racha(mensajes_user, mensaje):
            return None
        return (
            f"RACHA DE MENSAJES VACÍOS ({DetectorMensajesVacios.umbral_racha()} "
            "turnos seguidos sin contenido). NO abras búsqueda nueva ni asumas "
            "lo que el cliente quiere. Pedile UNA pregunta concreta para "
            "destrabar: '¿Buscás algo en particular o querés que te muestre "
            "ofertas del día?'"
        )

    def _bloque_categoria_bloqueada(self, sesion_id: UUID) -> str | None:
        """Intent/Category Lock: cuando el cliente ya estableció una categoría en
        la sesión, le dice al LLM que la use en buscar_productos y no la cambie
        salvo que el cliente lo pida explícitamente."""
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        cat = perfil.categoria_efectiva()
        if not cat:
            return None
        subcat = perfil.subcategoria_efectiva()
        cat_str = f"{cat}/{subcat}" if subcat else cat
        instruccion = (
            f"CATEGORÍA ACTIVA: el cliente ya estableció que busca en «{cat_str}». "
            f"Pasá siempre `categoria=\"{cat}\"` a buscar_productos en este turno"
        )
        if subcat:
            instruccion += f" y `subcategoria=\"{subcat}\"`"
        instruccion += (
            ". NO cambies la categoría a menos que el cliente mencione explícitamente "
            "otro tipo de producto."
        )
        return instruccion

    @staticmethod
    def _bloque_preferencia_blanda(mensaje: str) -> str | None:
        """Cuando el cliente dice 'prefiero X pero acepto Y', inyecta instrucción
        al LLM para mostrar ambas marcas sin aplicar filtro duro."""
        pref = DetectorPreferenciaBlanda.detectar(mensaje)
        if pref is None:
            return None
        alt_txt = f" y opciones de {pref.marca_alternativa.upper()}" if pref.marca_alternativa else " y la mejor alternativa disponible"
        return (
            f"PREFERENCIA BLANDA DE MARCA: el cliente prefiere {pref.marca_preferida.upper()}"
            f"{alt_txt}. "
            f"NO uses marca como filtro duro en buscar_productos — busca sin restricción de marca "
            f"y presenta primero opciones de {pref.marca_preferida.upper()}, luego las mejores "
            f"alternativas. El cliente ya aceptó ver otras marcas."
        )

    @staticmethod
    def _bloque_exclusiones(mensaje: str) -> str | None:
        marcas = DetectorMarcaExcluida.detectar(mensaje)
        if not marcas:
            return None
        return (
            f"EXCLUSIONES DEL CLIENTE — marcas a NO mostrar: {', '.join(m.upper() for m in marcas)}. "
            f"Al llamar buscar_productos NO incluyas nada de estas marcas en los resultados. "
            f"Si solo hay esas marcas, decilo honesto."
        )

    @staticmethod
    def _bloque_prioridades(mensaje: str) -> str | None:
        slots = DetectorPrioridadesJerarquicas.detectar(mensaje)
        if not slots:
            return None
        return DetectorPrioridadesJerarquicas.formatear(slots)

    _RX_TRES_OPCIONES_A = re.compile(
        r"\b(?:opci[oó]n\s+)?(?:econ[oó]mica|barata)\b.{0,60}\bpremium\b",
        re.IGNORECASE | re.DOTALL,
    )
    _RX_TRES_OPCIONES_B = re.compile(
        r"\b(?:tres?|3)\s*(?:opciones?|modelos?|alternativas?)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _bloque_formato_solicitado(mensaje: str) -> str | None:
        """Inyecta directiva al LLM cuando el cliente pide un formato
        explicito ('comprar/evitar', 'segura/barata', 'maximo N', 'una frase').
        Independiente del bloque de tres-opciones existente — pueden coexistir
        si el cliente combina formatos."""
        fmt = DetectorFormatoSolicitado.detectar(mensaje)
        return BloqueFormatoSolicitado.renderizar(fmt)

    @classmethod
    def _bloque_formato_tres_opciones(cls, mensaje: str) -> str | None:
        if not (cls._RX_TRES_OPCIONES_A.search(mensaje) or cls._RX_TRES_OPCIONES_B.search(mensaje)):
            return None
        pide_eleccion = bool(
            re.search(r"\bcompr[aá]r[ií]as?\b|\bpara\s+tu\s+casa\b", mensaje, re.IGNORECASE)
            or re.search(r"\btu\s+elecci[oó]n\b|\bsi\s+fuera\s+(?:para\s+)?tuyo?\b", mensaje, re.IGNORECASE)
        )
        bloque = (
            "FORMATO ESTE TURNO: usar exactamente 3 secciones:\n"
            "**Opción económica — Nombre — Bs precio [SKU]** | specs: valor/N/D | razón\n"
            "**Opción equilibrada — Nombre — Bs precio [SKU]** | specs: valor/N/D | razón\n"
            "**Opción premium — Nombre — Bs precio [SKU]** | specs: valor/N/D | razón\n"
            "Atributos no confirmados en ficha = N/D obligatorio."
        )
        if pide_eleccion:
            bloque += (
                "\nAl final, responder en 1ª persona: "
                "'Para mi casa elegiría la [opción] porque [razón concreta].'"
            )
        return bloque

    _RX_NO_HUMO_A = re.compile(
        r"\bno\s+me\s+vendas?\s+humo\b|\bquiero\s+honestidad\b|\bla\s+verdad\b",
        re.IGNORECASE,
    )
    _RX_NO_HUMO_B = re.compile(
        r"\brealmente\s+(?:sirve|vale|conviene|es\s+buena?)\b|\bde\s+verdad\s+(?:sirve|vale)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _bloque_no_humo(cls, mensaje: str) -> str | None:
        if not (cls._RX_NO_HUMO_A.search(mensaje) or cls._RX_NO_HUMO_B.search(mensaje)):
            return None
        return (
            "MODO HONESTIDAD ACTIVADO: separar explícitamente para cada producto:\n"
            "✓ Dato confirmado en ficha | ⚠ Inferido/probable | ✗ No disponible/N/D\n"
            "Mencionar la desventaja real del producto recomendado.\n"
            "No usar términos de catálogo sin datos: 'ideal', 'perfecto', 'potente'.\n"
            "Si Hz/HDMI/GPU/inverter no están en ficha → decirlo, no suponerlo."
        )

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
        if perfil.ram_gb_min:
            partes.append(f"- RAM mínima requerida: {perfil.ram_gb_min} GB")
        if perfil.gpu_dedicada:
            partes.append("- GPU dedicada requerida: SÍ (solo mostrar laptops con GPU confirmada en ficha)")
        if perfil.pulgadas:
            partes.append(f"- Pulgadas: {perfil.pulgadas:g}\"")
        if perfil.tipo_panel:
            partes.append(f"- Tipo de panel: {perfil.tipo_panel}")
        if perfil.resolucion:
            partes.append(f"- Resolucion: {perfil.resolucion}")
        ciudad = getattr(perfil, "ciudad_sesion", None)
        if ciudad:
            partes.append(f"- Ciudad: {ciudad}")
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
                "del CONTEXTO de arriba. Lista TODAS las características disponibles: procesador, "
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
        # Caps de formato: el path follow-up se saltaba la cadena de
        # post-procesadores; aplicamos limpieza+cap aqui para que
        # 'maximo 3', 'una frase', etc tambien funcionen en follow-ups.
        texto_post = LimpiadorSeccionesVacias.limpiar(follow_up.texto)
        fmt = DetectorFormatoSolicitado.detectar(mensaje_usuario)
        texto_post = AjustadorRespuestaFormato.ajustar(texto_post, fmt)
        follow_up = RespuestaFollowUp(
            texto=texto_post,
            productos=follow_up.productos[: fmt.max_productos] if fmt.max_productos else follow_up.productos,
            skus=follow_up.skus[: fmt.max_productos] if fmt.max_productos else follow_up.skus,
            ruta=follow_up.ruta,
        )
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

    def _responder_intencion_vaga(
        self,
        sesion_id: UUID,
        inp: ChatInput,
        t0: float,
    ) -> ChatOutput:
        texto = DetectorIntentionVaga.RESPUESTA
        self._registrar.ejecutar(
            RegistrarMensajeCommand(
                sesion_id=sesion_id, rol=RolMensaje.ASSISTANT, contenido=texto
            )
        )
        self._registrar_metrica.ejecutar(
            RegistrarMetricaTurnoCommand(
                sesion_id=sesion_id,
                mensaje_usuario_len=len(inp.mensaje),
                respuesta_len=len(texto),
                tool_calls=0,
                mentiras_detectadas=0,
                productos_citados=0,
                ruta="intencion_vaga",
                tiempo_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return ChatOutput(sesion_id=sesion_id, respuesta=texto)

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

    def _hidratar_perfil_historico_si_aplica(self, sesion_id: UUID, mensaje: str) -> None:
        """Si el cliente menciona email o telefono y existe perfil historico,
        precarga categoria/marca preferidas + frustracion_count acumulado en
        el perfil de la sesion actual.

        Esto es la pieza central de cross-session memory: cuando el cliente
        vuelve y se identifica, recupera el contexto que tenia antes."""
        if self._obtener_perfil_historico is None:
            return
        from ..commands.actualizar_perfil_sesion import ActualizarPerfilSesionCommand
        from .detector_contacto_cliente import DetectorContactoCliente
        from .hasher_contacto import HasherContacto
        contacto = DetectorContactoCliente.detectar(mensaje)
        if not (contacto.email or contacto.telefono):
            return
        contacto_hash = (
            HasherContacto.email(contacto.email) if contacto.email
            else HasherContacto.telefono(contacto.telefono)
        )
        try:
            res = self._obtener_perfil_historico.ejecutar(
                ObtenerPerfilHistoricoQuery(contacto_hash=contacto_hash)
            )
            if not res.encontrado:
                return
            snapshot = res.perfil_snapshot or {}
            # Sembramos frustracion_count del snapshot histórico — si el
            # cliente venia frustrado, esta sesion arranca consciente de eso.
            frust_historico = snapshot.get("frustracion_count")
            self._actualizar_perfil.ejecutar(ActualizarPerfilSesionCommand(
                sesion_id=sesion_id,
                categoria_foco=res.ultima_categoria,
                marca_preferida=res.ultima_marca,
                uso_declarado=snapshot.get("uso_declarado"),
                presupuesto_max=snapshot.get("presupuesto_max"),
                ram_gb_min=snapshot.get("ram_gb_min"),
                ssd_gb_min=snapshot.get("ssd_gb_min"),
                gpu_dedicada=snapshot.get("gpu_dedicada"),
                frustracion_delta=frust_historico,
            ))
        except Exception:
            pass

    def _evaluar_avance_turno(
        self,
        respuesta: str,
        productos: list,
        sesion_id: UUID,
        trace: list,
    ) -> bool:
        """Verifica si el turno aportó valor (tool transaccional, SKU nuevo
        citado, o dato concreto). Devuelve True si hubo avance."""
        try:
            perfil = self._obtener_perfil.ejecutar(
                ObtenerPerfilSesionQuery(sesion_id=sesion_id)
            )
            historicos_str = perfil.ultimos_skus_mostrados or ""
            historicos = [s.strip() for s in historicos_str.split(",") if s.strip()]
        except Exception:
            historicos = []
        skus_actuales = [str(p.get("sku")) for p in (productos or []) if p.get("sku")]
        return VerificadorAvanceTurno.hubo_avance(
            respuesta=respuesta,
            skus_citados_actuales=skus_actuales,
            skus_historicos_mostrados=historicos,
            trace=trace,
        )

    def _incrementar_frustracion_si_aplica(self, sesion_id: UUID, mensaje: str) -> None:
        """Si el mensaje tiene cualquier señal de frustración (alto/medio/bajo)
        y NO va a derivar (eso lo decide el short-circuit más abajo), suma 1
        al contador acumulado del perfil. NO se incrementa cuando se deriva
        porque ese turno se cierra antes y la sesión termina."""
        nivel = DetectorFrustracion.nivel(mensaje)
        if nivel in ("ninguno",):
            return
        # Si va a derivar el short-circuit, no acumulamos (la sesión cierra).
        if DetectorFrustracion.debe_derivar(mensaje):
            return
        try:
            from ..commands.actualizar_perfil_sesion import ActualizarPerfilSesionCommand
            self._actualizar_perfil.ejecutar(ActualizarPerfilSesionCommand(
                sesion_id=sesion_id,
                frustracion_delta=1,
            ))
        except Exception:
            pass

    def _persistir_perfil_historico_si_compra(
        self, sesion_id: UUID, mensaje_usuario: str, trace: list, productos: list
    ) -> None:
        """Si el turno cerro con confirmar_orden y hay email/telefono, guarda
        snapshot del perfil para futuras visitas del mismo cliente."""
        if self._guardar_perfil_historico is None:
            return
        confirmados = [
            p for p in trace
            if p.tool == "confirmar_orden" and not (p.result or {}).get("error")
        ]
        if not confirmados:
            return
        args_confirm = confirmados[-1].args or {}
        email = args_confirm.get("email") or args_confirm.get("cliente_email")
        telefono = args_confirm.get("telefono") or args_confirm.get("cliente_telefono")
        if not (email or telefono):
            from .detector_contacto_cliente import DetectorContactoCliente
            contacto = DetectorContactoCliente.detectar(mensaje_usuario)
            email = contacto.email
            telefono = contacto.telefono
        if not (email or telefono):
            return
        from .hasher_contacto import HasherContacto
        contacto_hash = HasherContacto.email(email) if email else HasherContacto.telefono(telefono)
        perfil = self._obtener_perfil.ejecutar(
            ObtenerPerfilSesionQuery(sesion_id=sesion_id)
        )
        primer_sku = (productos[0].get("sku") if productos else None)
        try:
            self._guardar_perfil_historico.ejecutar(GuardarPerfilHistoricoCommand(
                contacto_hash=contacto_hash,
                perfil_snapshot={
                    "categoria_foco": perfil.categoria_foco,
                    "marca_preferida": perfil.marca_preferida,
                    "uso_declarado": perfil.uso_declarado,
                    "presupuesto_max": perfil.presupuesto_max,
                    "ram_gb_min": perfil.ram_gb_min,
                    "ssd_gb_min": perfil.ssd_gb_min,
                    "gpu_dedicada": perfil.gpu_dedicada,
                    # Persistir contador de frustracion para que cross-session
                    # arranque consciente del estado emocional historico.
                    "frustracion_count": perfil.frustracion_count,
                },
                ultima_categoria=perfil.categoria_foco,
                ultima_marca=perfil.marca_preferida,
                ultima_compra_sku=primer_sku,
            ))
        except Exception:
            pass

    def _registrar_synonym_candidato_si_no_resuelve(
        self, mensaje_usuario: str, productos: list, trace: list
    ) -> None:
        """Si el turno termino sin productos citados Y NO se invoco
        comparar/ver_carrito (no es follow-up), registramos el termino
        principal del mensaje como candidato a sinonimo."""
        if self._registrar_synonym is None or productos:
            return
        tools_relevantes = {p.tool for p in trace if p.tool == "buscar_productos"}
        if not tools_relevantes:
            return
        from .extractor_termino_no_resuelto import ExtractorTerminoNoResuelto
        termino = ExtractorTerminoNoResuelto.extraer(mensaje_usuario)
        if not termino:
            return
        try:
            self._registrar_synonym.ejecutar(
                RegistrarSynonymCandidatoCommand(termino=termino, categoria_inferida=None)
            )
        except Exception:
            pass

    def _auto_curar_si_exitoso(
        self,
        sesion_id: UUID,
        mensaje_usuario: str,
        respuesta: str,
        productos: list,
        ruta: str,
        tiempo_ms: int,
        mentiras_detectadas: int,
    ) -> None:
        """Si el turno cumple criterios de exito, lo persiste como
        ConversacionCurada con flag auto_curada para futuro few-shot."""
        if self._auto_curar is None:
            return
        from .clasificador_turno_exitoso import ClasificadorTurnoExitoso
        clasif = ClasificadorTurnoExitoso.evaluar(
            mensaje_usuario=mensaje_usuario,
            respuesta=respuesta,
            productos_citados=productos,
            ruta=ruta,
            tiempo_ms=tiempo_ms,
            mentiras_detectadas=mentiras_detectadas,
        )
        if not clasif.es_exitoso:
            return
        try:
            perfil = self._obtener_perfil.ejecutar(
                ObtenerPerfilSesionQuery(sesion_id=sesion_id)
            )
            perfil_dict = {
                "categoria_foco": perfil.categoria_foco,
                "subcategoria_foco": perfil.subcategoria_foco,
                "marca_preferida": perfil.marca_preferida,
                "uso_declarado": perfil.uso_declarado,
                "presupuesto_max": perfil.presupuesto_max,
                "ram_gb_min": perfil.ram_gb_min,
                "ssd_gb_min": perfil.ssd_gb_min,
                "gpu_dedicada": perfil.gpu_dedicada,
                "nombre_excluye_acum": perfil.nombre_excluye_acum,
            }
            self._auto_curar.ejecutar(AutoCurarConversacionCommand(
                sesion_id=sesion_id,
                cliente_texto=mensaje_usuario,
                asistente_texto=respuesta,
                score=clasif.score,
                etiqueta="auto_curada",
                productos_citados=productos,
                perfil_estado=perfil_dict,
            ))
        except Exception:
            pass

    # Tipos de producto incompatibles con una búsqueda de refrigeradora.
    # Si el LLM devuelve productos con estas palabras en el nombre cuando el
    # cliente pedía una refrigeradora, es un mismatch de categoría.
    _INCOMPAT_REFRI = frozenset({
        "hermetico", "hermético", "tupper", "recipiente", "organizador",
        "envase", "contenedor", "taper",
    })

    def _productos_violan_requisitos_duros(
        self, trace: list[PasoAgente], mensaje: str
    ) -> bool:
        """True si algún producto devuelto por el LLM viola un requisito duro
        del mensaje: exclusiones de nombre (celeron, pentium, chromebook),
        RAM mínima, capacidad mínima o mismatch de categoría (hermético cuando
        se buscó refrigeradora).

        Cuando retorna True, _debe_forzar_busqueda lanzará _forzar_busqueda
        con los filtros duros correctamente aplicados."""
        productos_llm: list[dict] = []
        for p in trace:
            if p.tool == "buscar_productos" and not p.result.get("error"):
                raw = p.result.get("productos") or []
                if raw:
                    productos_llm = list(raw)
                    break
        if not productos_llm:
            return False

        excluidos = [e.lower() for e in (DetectorExclusionesMensaje.detectar(mensaje) or [])]
        ram_min = self._extraer_ram_gb_mensaje(mensaje)
        kg_min = self._extraer_capacidad_kg_mensaje(mensaje)
        norm_msg = NormalizadorTexto.normalizar(mensaje)
        msg_tokens = set(norm_msg.split())
        busca_refri = bool(
            msg_tokens & {"refrigeradora", "refrigerador", "refri", "heladera"}
        )

        for prod in productos_llm:
            nombre = (prod.get("nombre") or "").lower()
            attrs: dict = prod.get("atributos") or {}

            # Exclusiones explícitas de nombre (celeron, pentium, chromebook…)
            for exc in excluidos:
                if exc and exc in nombre:
                    return True

            # Mismatch categoría: buscaba refrigeradora pero llegó un hermético
            if busca_refri and any(incompat in nombre for incompat in self._INCOMPAT_REFRI):
                return True

            # RAM mínima (atributo estructurado)
            if ram_min:
                ram_prod = attrs.get("ram_gb") or 0
                if ram_prod and int(ram_prod) < ram_min:
                    return True

            # Capacidad kg mínima (lavadora)
            if kg_min:
                cap_kg = attrs.get("capacidad_kg") or 0
                if cap_kg and float(cap_kg) < kg_min:
                    return True

        return False

    def _debe_forzar_busqueda(
        self, respuesta: str, trace: list[PasoAgente], mensaje: str
    ) -> bool:
        """Casos en los que el LLM no busco bien y lo corregimos:
          a) respondio listando productos sin haber llamado buscar_productos
             con resultados (alucina productos).
          b) no llamo buscar_productos en absoluto y el mensaje menciona una
             categoria reconocida (sinonimo en BD).
          c) el LLM busco con resultados pero los productos violan requisitos
             duros del mensaje (celeron excluido, RAM insuficiente, mismatch
             de categoria como hermeticos para una busqueda de refrigeradora).

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
            # Aunque el LLM ya buscó, si los productos violan requisitos duros
            # del mensaje, forzamos una nueva búsqueda con filtros correctos.
            if self._productos_violan_requisitos_duros(trace, mensaje):
                return True
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
        # Acumulamos exclusiones nuevas con las ya guardadas en el perfil
        # ('chromebook', 'celeron', 'pentium' detectadas antes). Garantiza que
        # las alternativas del fallback respeten lo que el cliente dijo en
        # turnos previos, no solo lo que dijo en este mensaje.
        nombre_excluye = self._unir_exclusiones(nombre_excluye, perfil.nombre_excluye_acum)
        tipo_producto_excluye = tuple(DetectorExclusionesMensaje.tipos_a_excluir(mensaje)) or None
        marca_excluye = tuple(DetectorMarcaExcluida.detectar(mensaje)) or None
        duros = FiltrosDurosBusqueda(
            precio_max=precio_max_efectivo,
            precio_min=piso_tier,
            nombre_excluye=nombre_excluye,
            tipo_producto_excluye=tipo_producto_excluye,
            marca_excluye=marca_excluye,
            pulgadas=perfil.pulgadas or None,
            ram_gb_min=perfil.ram_gb_min or None,
            capacidad_gb_min=perfil.ssd_gb_min or None,
            gpu_dedicada=perfil.gpu_dedicada or None,
        )
        res = await self._manejador_ausente.manejar(
            mensaje,
            contexto,
            categoria_activa=perfil.categoria_efectiva() or None,
            subcategoria_activa=perfil.subcategoria_efectiva() or None,
            refinamiento=DetectorRefinamientoShown.detectar(mensaje),
            marca_preferida=perfil.marca_preferida or None,
            duros=duros,
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

    @staticmethod
    def _unir_exclusiones(
        nuevas: tuple[str, ...] | None, acumuladas_csv: str | None,
    ) -> tuple[str, ...] | None:
        """Une exclusiones del turno actual con las acumuladas en el perfil
        ('chromebook,celeron,pentium' detectadas en turnos previos), sin
        duplicados y preservando orden — turno actual primero."""
        salida: list[str] = []
        for k in (nuevas or ()):
            kn = (k or "").strip().lower()
            if kn and kn not in salida:
                salida.append(kn)
        for k in (acumuladas_csv or "").split(","):
            kn = (k or "").strip().lower()
            if kn and kn not in salida:
                salida.append(kn)
        return tuple(salida) or None

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
        tier_msg = DetectorTierDeseado.detectar(mensaje)
        tier_ef = perfil.desired_tier or tier_msg
        contradiccion = DetectorContradiccionPresupuesto.detectar(
            tier=tier_ef,
            presupuesto_max=perfil.presupuesto_max,
            subcategoria=perfil.subcategoria_efectiva() or None,
        )
        productos, genero_sin_resultados, aviso_fallback = self._ejecutar_query_con_fallbacks(query)
        # Solo rerankeamos cuando no hay tier explícito: si el cliente pidió
        # "tope de gama" o "lo más barato", el orden por precio del SQL ya es
        # correcto y el reranker no debe alterar esa intención.
        if not tier_ef:
            marca_indif = DetectorIntencionAsesoria.marca_es_indiferente(mensaje)
            productos = ReRankerPorPerfil().reordenar(productos, perfil, marca_indiferente=marca_indif)
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
            productos_efectivos, genero_sin_resultados, query, aviso_fallback,
            perfil=perfil,
            formato=DetectorFormatoSolicitado.detectar(mensaje),
        )
        if contradiccion:
            texto = f"{contradiccion.mensaje}\n\n{texto}"
        return (texto, trace, [str(p.sku) for p in productos_efectivos[:3]])

    def _construir_query_forzado(
        self,
        mensaje: str,
        sesion_id: UUID,
        excluir_skus: tuple[str, ...] | None,
    ):
        """Construye el BuscarProductosQuery para _forzar_busqueda."""
        perfil = self._obtener_perfil.ejecutar(ObtenerPerfilSesionQuery(sesion_id=sesion_id))
        mensaje_limpio = SanitizadorQueryBusqueda.sanitizar(mensaje)
        # Si el sanitizador rechaza la frase entera (típico en frases
        # conversacionales: "Hola Dismi, necesito una laptop para X"), uso
        # el resolvedor de sinónimos como fallback: si matchea una palabra
        # de producto del catálogo, esa es la query.
        if mensaje_limpio is None:
            cercana = self._resolvedor_categoria.resolver(mensaje)
            if cercana is not None and cercana.fuente == "sinonimo":
                mensaje_limpio = cercana.palabra_clave or None
        mensaje_norm = NormalizadorTexto.normalizar(mensaje_limpio or "")
        tiene_terminos = bool(mensaje_limpio) and TokensConsulta.hay_terminos(mensaje_norm)
        cat_ef = perfil.categoria_efectiva() or None
        subcat_ef = perfil.subcategoria_efectiva() or None
        es_accesorio = DetectorConsultaAccesorio.es_consulta_accesorio(
            mensaje_limpio if tiene_terminos else None, cat_ef, subcat_ef
        )
        precio_min, precio_max_final = self._precio_sin_contradiccion(perfil, subcat_ef)
        tier_ef = perfil.desired_tier or DetectorTierDeseado.detectar(mensaje)
        pref_blanda = DetectorPreferenciaBlanda.detectar(mensaje)
        marca_query = (
            None if pref_blanda else
            (perfil.marca_preferida or DetectorMarcaMensaje.extraer(mensaje) or None)
        )
        query = BuscarProductosQuery(
            query=mensaje_limpio if tiene_terminos else None,
            categoria=cat_ef,
            subcategoria=subcat_ef,
            marca=marca_query,
            precio_min=precio_min,
            precio_max=precio_max_final,
            pulgadas=perfil.pulgadas,
            tipo_panel=perfil.tipo_panel,
            resolucion=perfil.resolucion,
            ram_gb_min=self._extraer_ram_gb_mensaje(mensaje) or perfil.ram_gb_min,
            capacidad_kg_min=self._extraer_capacidad_kg_mensaje(mensaje),
            capacidad_litros_min=self._extraer_capacidad_litros_mensaje(mensaje),
            gpu_dedicada=self._gpu_ef(mensaje, perfil.gpu_dedicada),
            limite=12,
            excluir_accesorios=not es_accesorio,
            genero=perfil.genero_declarado or None,
            excluir_skus=excluir_skus,
            nombre_excluye=tuple(DetectorExclusionesMensaje.detectar(mensaje)) or None,
            tipo_producto_excluye=self._tipos_excluir(mensaje, mensaje_limpio if tiene_terminos else None, cat_ef, subcat_ef),
            marca_excluye=tuple(DetectorMarcaExcluida.detectar(mensaje)) or None,
            orden_precio="desc" if tier_ef in ("flagship", "alto") else "asc",
        )
        return query, es_accesorio, perfil

    def _precio_sin_contradiccion(self, perfil, subcat_ef: str | None) -> tuple:
        """Rango precio con tier; si piso > presupuesto, anula el piso."""
        precio_min, precio_max = self._rango_precio_tier(perfil, subcat_ef)
        if precio_min and precio_max and precio_min > precio_max:
            precio_min = None
        return precio_min, precio_max

    @staticmethod
    def _tipos_excluir(
        mensaje: str,
        mensaje_limpio: str | None,
        cat_ef: str | None,
        subcat_ef: str | None,
    ) -> tuple | None:
        tipos = list(DetectorExclusionesMensaje.tipos_a_excluir(mensaje))
        if ExcluidorJuguetesDefault.debe_excluir(mensaje_limpio, cat_ef, subcat_ef, mensaje):
            if "juguete" not in tipos:
                tipos.append("juguete")
        return tuple(tipos) or None

    @staticmethod
    def _gpu_ef(mensaje: str, gpu_perfil: bool | None) -> bool | None:
        """True si el mensaje o el perfil persistido requiere GPU dedicada."""
        return True if DetectorGpuDedicada.requiere_gpu(mensaje) else gpu_perfil

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

    @staticmethod
    def _extraer_capacidad_kg_mensaje(mensaje: str) -> float | None:
        """Extrae capacidad_kg_min del mensaje: 'mínimo 18 kg', '18 kilos mínimo'."""
        import re
        m = re.search(
            r'\bm[ií]nimo\s+(\d+)\s*(?:kg|kgs?|kilos?)\b'
            r'|\b(\d+)\s*(?:kg|kgs?|kilos?)\s+(?:m[ií]nimo|como\s+m[ií]nimo)\b'
            r'|\bal\s+menos\s+(\d+)\s*(?:kg|kgs?|kilos?)\b',
            mensaje, re.IGNORECASE
        )
        if m:
            val = float(next(g for g in m.groups() if g is not None))
            return val if 5 <= val <= 100 else None
        return None

    @staticmethod
    def _extraer_capacidad_litros_mensaje(mensaje: str) -> float | None:
        """Extrae capacidad_litros_min del mensaje: 'mínimo 300 litros', '300 lts mínimo'."""
        import re
        m = re.search(
            r'\bm[ií]nimo\s+(\d+)\s*(?:litros?|lts?)\b'
            r'|\b(\d+)\s*(?:litros?|lts?)\s+(?:m[ií]nimo|como\s+m[ií]nimo)\b'
            r'|\bal\s+menos\s+(\d+)\s*(?:litros?)\b',
            mensaje, re.IGNORECASE
        )
        if m:
            val = float(next(g for g in m.groups() if g is not None))
            return val if 50 <= val <= 1000 else None
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
    ) -> tuple[list, bool, str | None]:
        """Ejecuta query con fallbacks en cascada. Devuelve (productos, genero_sin_resultados, aviso)."""
        from dataclasses import replace
        productos = self._buscar.ejecutar(query)
        genero_sin_resultados = bool(query.genero) and not productos
        if genero_sin_resultados:
            productos = self._buscar.ejecutar(replace(query, genero=None))
        aviso: str | None = None
        if not productos and query.gpu_dedicada:
            productos, aviso = self._fallback_gpu_dedicada(query)
        if not productos and query.marca and not aviso:
            productos, aviso = self._fallback_marca(query)
        if not productos and query.query and (query.categoria or query.subcategoria):
            productos = self._buscar.ejecutar(replace(query, query=None))
        # Cuando el LLM metió términos de análisis (Hz, HDMI, PS5…) en el query
        # y no pasó categoria, caemos aquí: usamos solo los filtros estructurados.
        if not productos and query.query and self._tiene_filtros_estructurados(query):
            productos = self._buscar.ejecutar(replace(query, query=None))
        if not productos and query.tipo_panel:
            productos = self._buscar.ejecutar(replace(query, tipo_panel=None))
        if not productos and query.refresh_hz_min:
            productos = self._buscar.ejecutar(replace(query, refresh_hz_min=None))
        productos = ValidadorSkuResultado.filtrar(productos)
        return productos, genero_sin_resultados, aviso

    @staticmethod
    def _tiene_filtros_estructurados(query: BuscarProductosQuery) -> bool:
        return bool(
            query.pulgadas or query.pulgadas_min or query.pulgadas_max
            or query.resolucion or query.ram_gb_min or query.capacidad_gb_min
            or query.capacidad_litros_min or query.capacidad_kg_min
            or query.refresh_hz_min
        )

    def _fallback_gpu_dedicada(
        self, query: BuscarProductosQuery
    ) -> tuple[list, str | None]:
        """Fallback GPU en orden de prioridad:
        1) quitar precio_max pero mantener GPU → muestra laptops GPU sobre presupuesto
        2) quitar gpu_dedicada → último recurso, laptops sin GPU dentro del precio"""
        from dataclasses import replace
        if query.precio_max:
            con_gpu = self._buscar.ejecutar(replace(query, precio_max=None))
            if con_gpu:
                return con_gpu, f"gpu_sobre_presupuesto:{query.precio_max:.0f}"
        sin_gpu = self._buscar.ejecutar(replace(query, gpu_dedicada=None))
        return (sin_gpu, "gpu_dedicada_no_confirmada") if sin_gpu else ([], None)

    def _fallback_marca(
        self, query: BuscarProductosQuery
    ) -> tuple[list, str | None]:
        """Fallback marca: re-busca sin restricción de marca cuando no hay stock."""
        from dataclasses import replace
        sin_marca = self._buscar.ejecutar(replace(query, marca=None))
        return (sin_marca, f"marca_no_encontrada:{query.marca}") if sin_marca else ([], None)

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
        from ..chat.tool_dispatcher import ToolDispatcher
        resultado = {
            "productos": [ToolDispatcher._proyectar(p, perfil) for p in productos_efectivos],
            "total": len(productos_efectivos),
            "sugeridos": [ToolDispatcher._proyectar(p, perfil) for p in sugeridos],
        }
        resultado.update(ToolDispatcher._inteligencia_turno(productos_efectivos, perfil))
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
        aviso_fallback: str | None = None,
        perfil=None,
        formato: FormatoSolicitado | None = None,
    ) -> str:
        if not productos_efectivos:
            return (
                "Ups, no encontre nada exacto con eso en el catalogo. "
                "Me das mas pistas? Marca preferida, presupuesto o tamanio me ayudarian un monton."
            )
        # Si el cliente pidio un formato estructural (comprar/evitar, segura/barata),
        # el path determinista renderiza con esa forma — no la lista clasica.
        if formato is not None and not formato.vacio() and formato.forma:
            forzado = RenderizadorFormatoForzado.renderizar(
                formato, productos_efectivos[:3], perfil,
            )
            if forzado:
                return forzado
        aviso = ""
        if genero_sin_resultados:
            aviso = (
                f"En esta categoria no diferenciamos por genero '{query.genero}', "
                f"son modelos unisex. Igual te muestro los disponibles:\n"
            )
        elif aviso_fallback == "gpu_dedicada_no_confirmada":
            aviso = (
                "No encontre laptops con GPU dedicada confirmada en ficha. "
                "Te muestro las opciones con mejores especificaciones disponibles "
                "(sin GPU dedicada confirmada en catalogo):\n"
            )
        elif aviso_fallback and aviso_fallback.startswith("gpu_sobre_presupuesto:"):
            presupuesto = aviso_fallback.split(":", 1)[1]
            aviso = (
                f"Las laptops con GPU dedicada superan tu presupuesto de Bs {presupuesto}. "
                f"Estas son las opciones disponibles con GPU confirmada:\n"
            )
        elif aviso_fallback and aviso_fallback.startswith("marca_no_encontrada:"):
            marca = aviso_fallback.split(":", 1)[1]
            aviso = (
                f"No encontre stock de {marca} en este momento. "
                f"Te muestro alternativas similares disponibles:\n"
            )
        lineas = [f"{aviso}Estas son las opciones que te puedo ofrecer:"]
        for p in productos_efectivos[:3]:
            extra = f" (antes Bs {p.precio_anterior.monto:.0f})" if p.precio_anterior else ""
            lineas.append(f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]")
        cierre = GeneradorCierreContextual.generar(aviso_fallback, perfil)
        if cierre:
            lineas.append(cierre)
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
