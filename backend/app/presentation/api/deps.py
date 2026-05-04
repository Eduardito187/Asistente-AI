from __future__ import annotations

from functools import lru_cache

from ...application.chat.agente_service import AgenteService
from ...application.chat.tool_dispatcher import ToolDispatcher
from ...application.commands.activar_conversacion_curada import (
    ActivarConversacionCuradaHandler,
)
from ...application.commands.actualizar_perfil_sesion import (
    ActualizarPerfilSesionHandler,
)
from ...application.commands.agregar_al_carrito import AgregarAlCarritoHandler
from ...application.commands.confirmar_orden import ConfirmarOrdenHandler
from ...application.commands.crear_sesion import CrearSesionHandler
from ...application.commands.curar_conversacion import CurarConversacionHandler
from ...application.commands.marcar_carritos_abandonados import MarcarCarritosAbandonadosHandler
from ...application.commands.quitar_del_carrito import QuitarDelCarritoHandler
from ...application.commands.registrar_alternativa_ofrecida import (
    RegistrarAlternativaOfrecidaHandler,
)
from ...application.commands.registrar_feedback_orden import (
    RegistrarFeedbackOrdenHandler,
)
from ...application.commands.registrar_mensaje import RegistrarMensajeHandler
from ...application.commands.registrar_metrica_turno import RegistrarMetricaTurnoHandler
from ...application.commands.registrar_sugerencia_catalogo import (
    RegistrarSugerenciaCatalogoHandler,
)
from ...application.commands.registrar_turno_mostrado import (
    RegistrarTurnoMostradoHandler,
)
from ...application.commands.vaciar_carrito import VaciarCarritoHandler
from ...application.queries.buscar_orden_sin_feedback import (
    BuscarOrdenSinFeedbackHandler,
)
from ...application.queries.buscar_productos import BuscarProductosHandler
from ...application.queries.comparar_productos import CompararProductosHandler
from ...application.queries.dashboard_metricas import DashboardMetricasHandler
from ...application.queries.historial_chat import HistorialChatHandler
from ...application.queries.listar_carritos import ListarCarritosHandler
from ...application.queries.listar_categorias import ListarCategoriasHandler
from ...application.queries.listar_conversaciones_curadas import (
    ListarConversacionesCuradasHandler,
)
from ...application.queries.listar_ordenes import ListarOrdenesHandler
from ...application.queries.obtener_ejemplos_fewshot import ObtenerEjemplosFewShotHandler
from ...application.queries.obtener_orden import ObtenerOrdenHandler
from ...application.queries.obtener_perfil_sesion import ObtenerPerfilSesionHandler
from ...application.queries.resolver_categoria_sinonimo import (
    ResolverCategoriaSinonimoHandler,
)
from ...application.queries.ver_carrito import VerCarritoHandler
from ...application.queries.ver_ordenes_sesion import VerOrdenesSesionHandler
from ...application.queries.ver_producto import VerProductoHandler
from ...application.services.aplicador_cross_sell import AplicadorCrossSell
from ...application.services.atajo_ordinal_carrito import AtajoOrdinalCarrito
from ...application.services.atajo_sku_directo import AtajoSkuDirecto
from ...application.services.buscador_semantico import BuscadorSemantico
from ...application.services.clasificador_intencion import ClasificadorIntencion
from ...application.services.curador_conversaciones import CuradorConversaciones
from ...application.services.detector_feedback_respuesta import DetectorFeedbackRespuesta
from ...application.services.detector_mentiras import DetectorMentiras
from ...application.services.detector_sku_mensaje import DetectorSkuMensaje
from ...application.services.evaluador_conversacion import EvaluadorConversacion
from ...application.services.extractor_perfil_mensaje import ExtractorPerfilMensaje
from ...application.services.gestor_feedback_post_orden import GestorFeedbackPostOrden
from ...application.services.gestor_follow_ups_contextuales import (
    GestorFollowUpsContextuales,
)
from ...application.services.inyector_fewshot import InyectorFewShot
from ...application.services.manejador_producto_ausente import ManejadorProductoAusente
from ...application.services.procesar_chat_service import ProcesarChatService
from ...application.services.reindexador_embeddings import ReindexadorEmbeddings
from ...application.services.resolvedor_categoria_cercana import (
    ResolvedorCategoriaCercana,
)
from ...application.services.responder_comparacion_explicita import (
    ResponderComparacionExplicita,
)
from ...application.services.responder_consulta_disponibilidad import (
    ResponderConsultaDisponibilidad,
)
from ...application.services.responder_productos_similares import (
    ResponderProductosSimilares,
)
from ...application.services.reranker_por_perfil import ReRankerPorPerfil
from ...application.services.responder_comparacion_mostrados import (
    ResponderComparacionMostrados,
)
from ...application.services.responder_mas_barato import ResponderMasBarato
from ...application.services.responder_mas_caro import ResponderMasCaro
from ...application.services.responder_otra_opcion import ResponderOtraOpcion
from ...application.services.responder_recomendacion_shown import (
    ResponderRecomendacionShown,
)
from ...application.services.responder_refinamiento_shown import (
    ResponderRefinamientoShown,
)
from ...application.services.sugeridor_cross_sell import SugeridorCrossSell
from ...application.services.sugeridor_productos_alternativos import (
    SugeridorProductosAlternativos,
)
from ...application.services.validador_producto_real import ValidadorProductoReal
from ...application.ports import Cache
from ...infrastructure.cache import CacheNulo, RedisCache
from ...infrastructure.config import settings
from ...infrastructure.llm.ollama_adapter import OllamaAdapter
from ...infrastructure.llm.ollama_embedder_adapter import OllamaEmbedderAdapter
from ...infrastructure.persistence.mariadb.carrito_read_model import MariaDbCarritoReadModel
from ...infrastructure.persistence.mariadb.dashboard_metricas_read_model import (
    MariaDbDashboardMetricasReadModel,
)
from ...infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork()


@lru_cache()
def llm_port() -> OllamaAdapter:
    return OllamaAdapter(host=settings.ollama_host, model=settings.ollama_model)


@lru_cache()
def embedder_port() -> OllamaEmbedderAdapter:
    return OllamaEmbedderAdapter(host=settings.ollama_host, model=settings.ollama_embed_model)


@lru_cache()
def carrito_read_model() -> MariaDbCarritoReadModel:
    return MariaDbCarritoReadModel()


@lru_cache()
def dashboard_metricas_read_model() -> MariaDbDashboardMetricasReadModel:
    return MariaDbDashboardMetricasReadModel()


@lru_cache()
def buscador_semantico() -> BuscadorSemantico:
    return BuscadorSemantico(embedder=embedder_port(), uow_factory=uow_factory)


@lru_cache()
def cache_port() -> Cache:
    """Cache compartido del proceso. Usa Redis si REDIS_URL apunta a una
    instancia alcanzable; en el peor caso cae a NoOp (sin cache, mismos
    resultados, solo mas latencia)."""
    try:
        adapter = RedisCache(settings.redis_url)
        adapter.set("cache:boot:probe", "ok", ttl_segundos=5)
        return adapter
    except Exception:
        return CacheNulo()


# -------- Handlers (uow-based, stateless) --------

def agregar_handler() -> AgregarAlCarritoHandler:
    return AgregarAlCarritoHandler(uow_factory)


def quitar_handler() -> QuitarDelCarritoHandler:
    return QuitarDelCarritoHandler(uow_factory)


def vaciar_handler() -> VaciarCarritoHandler:
    return VaciarCarritoHandler(uow_factory)


def confirmar_handler() -> ConfirmarOrdenHandler:
    return ConfirmarOrdenHandler(uow_factory)


def crear_sesion_handler() -> CrearSesionHandler:
    return CrearSesionHandler(uow_factory)


def registrar_mensaje_handler() -> RegistrarMensajeHandler:
    return RegistrarMensajeHandler(uow_factory)


def registrar_sugerencia_catalogo_handler() -> RegistrarSugerenciaCatalogoHandler:
    return RegistrarSugerenciaCatalogoHandler(uow_factory)


def marcar_abandonados_handler() -> MarcarCarritosAbandonadosHandler:
    return MarcarCarritosAbandonadosHandler(uow_factory)


def buscar_handler() -> BuscarProductosHandler:
    return BuscarProductosHandler(uow_factory, cache=cache_port())


def ver_producto_handler() -> VerProductoHandler:
    return VerProductoHandler(uow_factory)


def listar_categorias_handler() -> ListarCategoriasHandler:
    return ListarCategoriasHandler(uow_factory)


def ver_carrito_handler() -> VerCarritoHandler:
    return VerCarritoHandler(uow_factory)


def ver_ordenes_sesion_handler() -> VerOrdenesSesionHandler:
    return VerOrdenesSesionHandler(uow_factory)


def listar_ordenes_handler() -> ListarOrdenesHandler:
    return ListarOrdenesHandler(uow_factory)


def obtener_orden_handler() -> ObtenerOrdenHandler:
    return ObtenerOrdenHandler(uow_factory)


def historial_chat_handler() -> HistorialChatHandler:
    return HistorialChatHandler(uow_factory)


def listar_carritos_handler() -> ListarCarritosHandler:
    return ListarCarritosHandler(carrito_read_model())


def comparar_productos_handler() -> CompararProductosHandler:
    return CompararProductosHandler(uow_factory)


def obtener_perfil_sesion_handler() -> ObtenerPerfilSesionHandler:
    return ObtenerPerfilSesionHandler(uow_factory)


def actualizar_perfil_sesion_handler() -> ActualizarPerfilSesionHandler:
    return ActualizarPerfilSesionHandler(uow_factory)


def registrar_feedback_orden_handler() -> RegistrarFeedbackOrdenHandler:
    return RegistrarFeedbackOrdenHandler(uow_factory)


def buscar_orden_sin_feedback_handler() -> BuscarOrdenSinFeedbackHandler:
    return BuscarOrdenSinFeedbackHandler(uow_factory)


def dashboard_metricas_handler() -> DashboardMetricasHandler:
    return DashboardMetricasHandler(dashboard_metricas_read_model())


def resolver_categoria_sinonimo_handler() -> ResolverCategoriaSinonimoHandler:
    return ResolverCategoriaSinonimoHandler(uow_factory, cache=cache_port())


def resolvedor_categoria_cercana() -> ResolvedorCategoriaCercana:
    return ResolvedorCategoriaCercana(resolver=resolver_categoria_sinonimo_handler())


def registrar_alternativa_ofrecida_handler() -> RegistrarAlternativaOfrecidaHandler:
    return RegistrarAlternativaOfrecidaHandler(uow_factory)


def manejador_producto_ausente() -> ManejadorProductoAusente:
    return ManejadorProductoAusente(
        validador=ValidadorProductoReal(llm=llm_port()),
        sugeridor=SugeridorProductosAlternativos(buscar=buscar_handler()),
        registrar_sugerencia=registrar_sugerencia_catalogo_handler(),
        resolvedor_categoria=resolvedor_categoria_cercana(),
    )


def curar_conversacion_handler() -> CurarConversacionHandler:
    return CurarConversacionHandler(uow_factory)


def registrar_metrica_turno_handler() -> RegistrarMetricaTurnoHandler:
    return RegistrarMetricaTurnoHandler(uow_factory)


def registrar_turno_mostrado_handler() -> RegistrarTurnoMostradoHandler:
    return RegistrarTurnoMostradoHandler(uow_factory)


def obtener_ejemplos_fewshot_handler() -> ObtenerEjemplosFewShotHandler:
    return ObtenerEjemplosFewShotHandler(uow_factory)


def listar_conversaciones_curadas_handler() -> ListarConversacionesCuradasHandler:
    return ListarConversacionesCuradasHandler(uow_factory)


def activar_conversacion_curada_handler() -> ActivarConversacionCuradaHandler:
    return ActivarConversacionCuradaHandler(uow_factory)


def curador_conversaciones() -> CuradorConversaciones:
    return CuradorConversaciones(
        evaluador=EvaluadorConversacion(),
        curar=curar_conversacion_handler(),
    )


def inyector_fewshot() -> InyectorFewShot:
    return InyectorFewShot(ejemplos=obtener_ejemplos_fewshot_handler())


def reindexador_embeddings() -> ReindexadorEmbeddings:
    return ReindexadorEmbeddings(embedder=embedder_port(), uow_factory=uow_factory)


def procesar_chat_service() -> ProcesarChatService:
    dispatcher = ToolDispatcher(
        buscar=buscar_handler(),
        listar_cats=listar_categorias_handler(),
        ver_prod=ver_producto_handler(),
        ver_carrito=ver_carrito_handler(),
        ver_ordenes=ver_ordenes_sesion_handler(),
        agregar=agregar_handler(),
        quitar=quitar_handler(),
        vaciar=vaciar_handler(),
        confirmar=confirmar_handler(),
        comparar=comparar_productos_handler(),
        obtener_perfil=obtener_perfil_sesion_handler(),
        buscador_semantico=buscador_semantico(),
        reranker=ReRankerPorPerfil(),
    )
    agente = AgenteService(
        llm=llm_port(),
        dispatcher=dispatcher,
        inyector_fewshot=inyector_fewshot(),
        max_iter=5,
    )
    atajo_sku = AtajoSkuDirecto(detector=DetectorSkuMensaje(), dispatcher=dispatcher)
    atajo_ordinal = AtajoOrdinalCarrito(
        dispatcher=dispatcher, obtener_perfil=obtener_perfil_sesion_handler()
    )
    cross_sell = AplicadorCrossSell(
        sugeridor=SugeridorCrossSell(buscar=buscar_handler()),
    )
    gestor_feedback = GestorFeedbackPostOrden(
        detector=DetectorFeedbackRespuesta(),
        registrar=registrar_feedback_orden_handler(),
        buscar_pendiente=buscar_orden_sin_feedback_handler(),
    )
    obtener_perfil = obtener_perfil_sesion_handler()
    buscar = buscar_handler()
    gestor_follow_ups = GestorFollowUpsContextuales(
        responder_mas_barato=ResponderMasBarato(
            obtener_perfil=obtener_perfil, buscar_productos=buscar
        ),
        responder_mas_caro=ResponderMasCaro(
            obtener_perfil=obtener_perfil, buscar_productos=buscar
        ),
        responder_otra_opcion=ResponderOtraOpcion(
            obtener_perfil=obtener_perfil, buscar_productos=buscar,
            uow_factory=uow_factory,
        ),
        responder_comparacion=ResponderComparacionMostrados(
            obtener_perfil=obtener_perfil, comparar=comparar_productos_handler()
        ),
        responder_recomendacion=ResponderRecomendacionShown(
            obtener_perfil=obtener_perfil, buscar_productos=buscar
        ),
        responder_refinamiento=ResponderRefinamientoShown(
            obtener_perfil=obtener_perfil,
            comparar=comparar_productos_handler(),
            buscar=buscar,
        ),
    )
    return ProcesarChatService(
        uow_factory=uow_factory,
        crear_sesion=crear_sesion_handler(),
        registrar_mensaje=registrar_mensaje_handler(),
        historial_chat=historial_chat_handler(),
        agente=agente,
        dispatcher=dispatcher,
        buscar_productos=buscar,
        detector=DetectorMentiras(),
        manejador_ausente=manejador_producto_ausente(),
        clasificador=ClasificadorIntencion(),
        curador=curador_conversaciones(),
        registrar_metrica=registrar_metrica_turno_handler(),
        atajo_sku=atajo_sku,
        atajo_ordinal=atajo_ordinal,
        extractor_perfil=ExtractorPerfilMensaje(resolver=resolver_categoria_sinonimo_handler()),
        actualizar_perfil=actualizar_perfil_sesion_handler(),
        obtener_perfil=obtener_perfil,
        cross_sell=cross_sell,
        gestor_feedback=gestor_feedback,
        registrar_turno_mostrado=registrar_turno_mostrado_handler(),
        gestor_follow_ups=gestor_follow_ups,
        registrar_alternativa=registrar_alternativa_ofrecida_handler(),
        resolvedor_categoria=resolvedor_categoria_cercana(),
        responder_comparacion_explicita=ResponderComparacionExplicita(
            resolver=resolver_categoria_sinonimo_handler(),
            comparar=comparar_productos_handler(),
            buscar=buscar,
        ),
        responder_consulta_disponibilidad=ResponderConsultaDisponibilidad(
            buscar=buscar
        ),
        responder_similares=ResponderProductosSimilares(
            uow_factory=uow_factory,
            sugeridor=SugeridorProductosAlternativos(buscar=buscar_handler()),
        ),
    )
