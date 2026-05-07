"""Runner de regresion (#16 review). Cada caso valida que el quality gate
y los validators deterministicos detectan correctamente los fallos del
review historico. Falla si una mejora rompe la deteccion."""
import pytest

from app.application.services.auto_quality_scorer import AutoQualityScorer
from tests.regression_cases import CASOS


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_caso_regresion(caso: dict):
    score = AutoQualityScorer.evaluar(
        respuesta=caso["respuesta_agente"],
        productos=caso["productos_citados"],
        perfil_estado=caso["perfil_estado"],
    )
    assert score.apto_para_fewshot is caso["expected_apto"], (
        f"caso={caso['id']}: apto={score.apto_para_fewshot} expected={caso['expected_apto']} "
        f"violaciones={score.violaciones}"
    )
    if caso["expected_reason_critico"].value != "OK":
        assert score.reason_code == caso["expected_reason_critico"], (
            f"caso={caso['id']}: reason_code={score.reason_code.value} "
            f"expected={caso['expected_reason_critico'].value}"
        )


def test_total_casos_minimo():
    """Garantiza que mantenemos un set minimo de casos del review historico."""
    assert len(CASOS) >= 7
