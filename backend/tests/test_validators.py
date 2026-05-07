from app.application.services.validators import (
    BudgetValidator,
    CategoryConsistencyValidator,
    HardRequirementsValidator,
    NoBackendLeakValidator,
    ResponseFormatValidator,
    TechnicalClaimsValidator,
)
from app.domain.aprendizaje import ReasonCode


def test_category_validator_falla_con_celular_si_perfil_laptop():
    perfil = {"categoria_foco": "Laptops"}
    productos = [{"sku": "X", "categoria": "Celulares", "nombre": "iphone"}]
    r = CategoryConsistencyValidator.validar(perfil, productos)
    assert r.paso is False
    assert r.reason_code == ReasonCode.CATEGORY_MISMATCH


def test_category_validator_pasa_con_misma_cat():
    perfil = {"categoria_foco": "Laptops"}
    productos = [{"sku": "X", "categoria": "Laptops", "nombre": "hp"}]
    assert CategoryConsistencyValidator.validar(perfil, productos).paso is True


def test_hard_requirements_falla_ram_baja():
    perfil = {"ram_gb_min": 16}
    productos = [{"sku": "X", "ram_gb": 8, "nombre": "vivobook"}]
    r = HardRequirementsValidator.validar(perfil, productos)
    assert r.paso is False
    assert r.reason_code == ReasonCode.HARD_FILTER_IGNORED


def test_hard_requirements_falla_gpu_no_confirmada():
    perfil = {"gpu_dedicada": True}
    productos = [{"sku": "X", "ram_gb": 16, "capacidad_gb": 512, "gpu": None, "nombre": "lap"}]
    r = HardRequirementsValidator.validar(perfil, productos)
    assert r.paso is False


def test_hard_requirements_pasa_con_todos_cumplidos():
    perfil = {"ram_gb_min": 16, "ssd_gb_min": 512, "gpu_dedicada": True}
    productos = [{"sku": "X", "ram_gb": 16, "capacidad_gb": 512, "gpu": "RTX 5050", "nombre": "x"}]
    assert HardRequirementsValidator.validar(perfil, productos).paso is True


def test_hard_requirements_falla_si_nombre_excluido():
    perfil = {"nombre_excluye_acum": "celeron,chromebook"}
    productos = [{"sku": "X", "nombre": "Asus Celeron 4GB", "ram_gb": 4, "capacidad_gb": 64}]
    r = HardRequirementsValidator.validar(perfil, productos)
    assert r.paso is False


def test_technical_claims_falla_hdmi21_sin_catalogo():
    productos = [{"sku": "X", "nombre": "TV LG 55", "descripcion": "tv basica"}]
    respuesta = "Tiene HDMI 2.1 confirmado para PS5"
    r = TechnicalClaimsValidator.validar(respuesta, productos)
    assert r.paso is False
    assert r.reason_code == ReasonCode.TECHNICAL_HALLUCINATION


def test_technical_claims_pasa_si_dato_coincide():
    productos = [{"sku": "X", "nombre": "TV", "descripcion": "soporta hdmi 2.1"}]
    r = TechnicalClaimsValidator.validar("HDMI 2.1 confirmado", productos)
    assert r.paso is True


def test_no_backend_leak_falla_con_500():
    r = NoBackendLeakValidator.validar("Hubo HTTP 502 al conectar")
    assert r.paso is False
    assert r.reason_code == ReasonCode.BACKEND_ERROR_VISIBLE


def test_no_backend_leak_pasa_con_respuesta_normal():
    r = NoBackendLeakValidator.validar("Te recomiendo el HP a Bs 7500")
    assert r.paso is True


def test_response_format_falla_si_corto():
    r = ResponseFormatValidator.validar("ok", [])
    assert r.paso is False


def test_budget_validator_falla_si_excede():
    perfil = {"presupuesto_max": 5000}
    productos = [{"sku": "X", "precio_bob": 8000}]
    r = BudgetValidator.validar(perfil, productos)
    assert r.paso is False


def test_budget_validator_tolera_10pct():
    perfil = {"presupuesto_max": 5000}
    productos = [{"sku": "X", "precio_bob": 5400}]  # < 5500
    assert BudgetValidator.validar(perfil, productos).paso is True


def test_reason_code_es_critico():
    assert ReasonCode.es_critico(ReasonCode.CATEGORY_MISMATCH) is True
    assert ReasonCode.es_critico(ReasonCode.TOO_MANY_OPTIONS) is False
