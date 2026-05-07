"""Tests del EvaluadorShadow — mockea UoW para verificar logica."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.application.services.evaluador_shadow import EvaluadorShadow


@dataclass
class FakeFallida:
    id: int
    sesion_id: object = None
    mensaje_usuario: str = ""
    perfil_estado: dict = field(default_factory=dict)
    ultimo_buscar_args: Optional[dict] = None
    razon_fallo: str = ""
    trace_resumen: Optional[str] = None
    creado_en: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FakeCurada:
    id: int
    sesion_id: object = None
    etiqueta: str = "manual"
    cliente_texto: str = ""
    asistente_texto: str = ""
    score: int = 80
    turnos: int = 1
    llevo_a_orden: bool = False
    activa: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class _FakeFallidasRepo:
    def __init__(self, items):
        self._items = items

    def listar_recientes(self, limite=50):
        return self._items[:limite]


class _FakeCuradasRepo:
    def __init__(self, items):
        self._items = items

    def top_activas(self, limite):
        return self._items[:limite]


class FakeUoW:
    def __init__(self, fallidas=None, curadas=None):
        self.conversaciones_fallidas = _FakeFallidasRepo(fallidas or [])
        self.conversaciones_curadas = _FakeCuradasRepo(curadas or [])
        self._session = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def commit(self):
        pass


def factory_para(fallidas=None, curadas=None):
    def _f():
        return FakeUoW(fallidas=fallidas, curadas=curadas)
    return _f


def test_evalua_fallidas_extrae_reason_anterior():
    f = FakeFallida(
        id=1,
        sesion_id=uuid4(),
        mensaje_usuario="laptop ingenieria",
        razon_fallo="quality_score=20 violaciones=['cat: CATEGORY_MISMATCH algo']",
    )
    e = EvaluadorShadow(factory_para(fallidas=[f]))
    rs = e.evaluar_fallos_recientes(limite=10)
    assert len(rs) == 1
    assert rs[0].reason_code_anterior == "CATEGORY_MISMATCH"


def test_evalua_curadas_drift_si_validators_fallan():
    # Curada vieja con backend leak — hoy debe ser drift
    c = FakeCurada(
        id=1,
        sesion_id=uuid4(),
        cliente_texto="laptop",
        asistente_texto=(
            "Disculpa hubo HTTP 502 al conectar con el catalogo, intentalo "
            "despues por favor con detalles muy largos para superar minimo."
        ),
    )
    e = EvaluadorShadow(factory_para(curadas=[c]))
    rs = e.evaluar_curadas_activas(limite=10)
    assert len(rs) == 1
    assert rs[0].veredicto == "drift"


def test_evalua_lista_vacia_no_explota():
    e = EvaluadorShadow(factory_para(fallidas=[]))
    rs = e.evaluar_fallos_recientes()
    assert rs == []
