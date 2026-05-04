from app.application.services.simulador_financiamiento import SimuladorFinanciamiento


def test_precio_bajo_no_financia():
    assert SimuladorFinanciamiento.sugerir(800) == []


def test_precio_medio_devuelve_planes():
    planes = SimuladorFinanciamiento.sugerir(8000)
    assert len(planes) >= 2
    # 3 cuotas sin interes
    sin_interes = [p for p in planes if p.interes_total == 0]
    assert len(sin_interes) >= 1


def test_mejor_plan_prefiere_sin_interes():
    plan = SimuladorFinanciamiento.mejor_plan(5000)
    assert plan is not None
    assert plan.interes_total == 0


def test_descripcion_legible():
    plan = SimuladorFinanciamiento.mejor_plan(8000)
    assert plan is not None
    assert "Bs" in plan.descripcion
    assert str(plan.cuotas) in plan.descripcion
