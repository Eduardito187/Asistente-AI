"""Tests del merge incremental de PerfilSesion (caso multi-turno).

Verifica el escenario tipico del backlog: cliente declara categoria, despues
uso, despues specs, despues presupuesto. Cada turno debe ACUMULAR, no
reemplazar."""
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.perfiles_sesion import PerfilSesion


def _p(**kw):
    base = dict(
        sesion_id=uuid4(),
        presupuesto_max=None,
        marca_preferida=None,
        categoria_foco=None,
        uso_declarado=None,
        pulgadas=None,
        tipo_panel=None,
        resolucion=None,
        updated_at=datetime.now(timezone.utc),
    )
    base.update(kw)
    return PerfilSesion(**base)


def test_multi_turno_acumula_specs():
    sid = uuid4()
    t1 = _p(sesion_id=sid, categoria_foco="Laptops")
    t2 = _p(sesion_id=sid, uso_declarado="ingenieria")
    t3 = _p(sesion_id=sid, ram_gb_min=16, ssd_gb_min=512)
    t4 = _p(sesion_id=sid, presupuesto_max=11000.0, presupuesto_ideal=8500.0)
    t5 = _p(sesion_id=sid, gpu_dedicada=True)

    fusion = t1.fusionar(t2).fusionar(t3).fusionar(t4).fusionar(t5)

    assert fusion.categoria_foco == "Laptops"
    assert fusion.uso_declarado == "ingenieria"
    assert fusion.ram_gb_min == 16
    assert fusion.ssd_gb_min == 512
    assert fusion.presupuesto_max == 11000.0
    assert fusion.presupuesto_ideal == 8500.0
    assert fusion.gpu_dedicada is True


def test_actualizar_presupuesto_no_borra_categoria():
    sid = uuid4()
    base = _p(sesion_id=sid, categoria_foco="Laptops", uso_declarado="ingenieria")
    nuevo = _p(sesion_id=sid, presupuesto_max=12000.0)
    fusion = base.fusionar(nuevo)

    assert fusion.categoria_foco == "Laptops"
    assert fusion.uso_declarado == "ingenieria"
    assert fusion.presupuesto_max == 12000.0


def test_campo_no_nulo_no_se_pisa_con_none():
    sid = uuid4()
    base = _p(sesion_id=sid, ram_gb_min=16)
    nada = _p(sesion_id=sid)
    assert base.fusionar(nada).ram_gb_min == 16
