"""Tests del AsignadorVarianteAB. Mocks del UoW para no depender de BD."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4

from app.application.services.asignador_variante_ab import AsignadorVarianteAB


@dataclass
class FakeVariant:
    variant_name: str
    prompt_extra: str
    weight: int
    activa: bool = True
    id: Optional[int] = None
    descripcion: Optional[str] = None


class FakeRepo:
    def __init__(self, variantes):
        self._v = variantes

    def listar_activas(self):
        return self._v


class FakeUoW:
    def __init__(self, variantes):
        self.prompt_variants = FakeRepo(variantes)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def factory_para(variantes):
    def _f():
        return FakeUoW(variantes)
    return _f


def test_sin_variantes_devuelve_control():
    a = AsignadorVarianteAB(factory_para([]))
    out = a.asignar_runtime(uuid4())
    assert out.name == "control"
    assert out.prompt_extra == ""


def test_una_sola_variante_siempre_la_misma():
    v = FakeVariant("alpha", "extra prompt", 100)
    a = AsignadorVarianteAB(factory_para([v]))
    out = a.asignar_runtime(uuid4())
    assert out.name == "alpha"
    assert out.prompt_extra == "extra prompt"


def test_misma_sesion_misma_variante_determinista():
    v1 = FakeVariant("control", "", 50)
    v2 = FakeVariant("alpha", "x", 50)
    a = AsignadorVarianteAB(factory_para([v1, v2]))
    sid = uuid4()
    asignacion_1 = a.asignar_runtime(sid)
    asignacion_2 = a.asignar_runtime(sid)
    assert asignacion_1.name == asignacion_2.name


def test_distribucion_aproximada_50_50():
    v1 = FakeVariant("control", "", 50)
    v2 = FakeVariant("alpha", "x", 50)
    a = AsignadorVarianteAB(factory_para([v1, v2]))
    sids = [uuid4() for _ in range(200)]
    asignaciones = [a.asignar_runtime(s).name for s in sids]
    n_control = asignaciones.count("control")
    # 50/50 +/- 15% de tolerancia con 200 muestras
    assert 70 <= n_control <= 130


def test_weight_cero_se_ignora():
    v1 = FakeVariant("dead", "old", 0)
    v2 = FakeVariant("alpha", "x", 100)
    a = AsignadorVarianteAB(factory_para([v1, v2]))
    out = a.asignar_runtime(uuid4())
    assert out.name == "alpha"


def test_api_legacy_estatica_sigue_funcionando():
    sid = UUID("00000000-0000-0000-0000-000000000001")
    out = AsignadorVarianteAB.variante(sid, ("a", "b"))
    assert out in ("a", "b")
    # Determinista: misma sid, mismas opciones, mismo resultado
    assert AsignadorVarianteAB.variante(sid, ("a", "b")) == out
