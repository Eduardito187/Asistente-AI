from __future__ import annotations

from functools import lru_cache

from ...application.chat.agente_service import AgenteService
from ...application.chat.tool_dispatcher import ToolDispatcher
from ...application.commands.agregar_al_carrito import AgregarAlCarritoHandler
from ...application.commands.confirmar_orden import ConfirmarOrdenHandler
from ...application.commands.crear_sesion import CrearSesionHandler
from ...application.commands.marcar_carritos_abandonados import MarcarCarritosAbandonadosHandler
from ...application.commands.quitar_del_carrito import QuitarDelCarritoHandler
from ...application.commands.registrar_mensaje import RegistrarMensajeHandler
from ...application.commands.vaciar_carrito import VaciarCarritoHandler
from ...application.queries.buscar_productos import BuscarProductosHandler
from ...application.queries.historial_chat import HistorialChatHandler
from ...application.queries.listar_carritos import ListarCarritosHandler
from ...application.queries.listar_categorias import ListarCategoriasHandler
from ...application.queries.listar_ordenes import ListarOrdenesHandler
from ...application.queries.obtener_orden import ObtenerOrdenHandler
from ...application.queries.ver_carrito import VerCarritoHandler
from ...application.queries.ver_ordenes_sesion import VerOrdenesSesionHandler
from ...application.queries.ver_producto import VerProductoHandler
from ...application.services.detector_mentiras import DetectorMentiras
from ...application.services.procesar_chat_service import ProcesarChatService
from ...infrastructure.config import settings
from ...infrastructure.llm.ollama_adapter import OllamaAdapter
from ...infrastructure.persistence.mariadb.carrito_read_model import MariaDbCarritoReadModel
from ...infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork()


@lru_cache()
def llm_port() -> OllamaAdapter:
    return OllamaAdapter(host=settings.ollama_host, model=settings.ollama_model)


@lru_cache()
def carrito_read_model() -> MariaDbCarritoReadModel:
    return MariaDbCarritoReadModel()


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


def marcar_abandonados_handler() -> MarcarCarritosAbandonadosHandler:
    return MarcarCarritosAbandonadosHandler(uow_factory)


def buscar_handler() -> BuscarProductosHandler:
    return BuscarProductosHandler(uow_factory)


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
    )
    agente = AgenteService(llm=llm_port(), dispatcher=dispatcher)
    return ProcesarChatService(
        uow_factory=uow_factory,
        crear_sesion=crear_sesion_handler(),
        registrar_mensaje=registrar_mensaje_handler(),
        historial_chat=historial_chat_handler(),
        agente=agente,
        dispatcher=dispatcher,
        buscar_productos=buscar_handler(),
        detector=DetectorMentiras(),
    )
