from app.domain.aprendizaje import ReasonCode, Severidad, SynonymType


def test_reason_codes_disponibles():
    assert ReasonCode.CATEGORY_MISMATCH.value == "CATEGORY_MISMATCH"
    assert ReasonCode.HARD_FILTER_IGNORED.value == "HARD_FILTER_IGNORED"
    assert ReasonCode.TECHNICAL_HALLUCINATION.value == "TECHNICAL_HALLUCINATION"


def test_reason_critico_set():
    criticos = [
        ReasonCode.CATEGORY_MISMATCH,
        ReasonCode.HARD_FILTER_IGNORED,
        ReasonCode.TECHNICAL_HALLUCINATION,
        ReasonCode.BACKEND_ERROR_VISIBLE,
        ReasonCode.UNSAFE_COMMERCIAL_CLAIM,
    ]
    for c in criticos:
        assert ReasonCode.es_critico(c) is True


def test_reason_no_critico():
    no_criticos = [
        ReasonCode.OK,
        ReasonCode.TOO_MANY_OPTIONS,
        ReasonCode.NO_RESULTS,
        ReasonCode.MAX_ITER_NO_TEXT,
    ]
    for c in no_criticos:
        assert ReasonCode.es_critico(c) is False


def test_severidad_values():
    assert Severidad.CRITICAL.value == "critical"
    assert Severidad.LOW.value == "low"


def test_synonym_types_completos():
    tipos = [t.value for t in SynonymType]
    assert "typo" in tipos
    assert "category_alias" in tipos
    assert "use_case" in tipos
    assert "brand_alias" in tipos
