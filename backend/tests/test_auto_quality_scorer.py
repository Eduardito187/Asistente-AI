from app.application.services.auto_quality_scorer import AutoQualityScorer
from app.domain.aprendizaje import ReasonCode


def test_score_alto_si_pasa_todo():
    perfil = {"categoria_foco": "Laptops", "ram_gb_min": 16, "gpu_dedicada": True, "presupuesto_max": 11000}
    productos = [
        {"sku": "X1", "nombre": "HP Victus i5",
         "categoria": "Laptops", "ram_gb": 16, "capacidad_gb": 512,
         "gpu": "RTX 5050", "precio_bob": 8799,
         "descripcion": "laptop gamer"},
    ]
    respuesta = (
        "Te recomiendo el HP Victus — Bs 8.799 [X1]. Tiene 16GB RAM y RTX 5050 confirmada. "
        "Cumple tu presupuesto y los requisitos de ingenieria."
    )
    out = AutoQualityScorer.evaluar(respuesta, productos, perfil)
    assert out.score >= 85
    assert out.apto_para_fewshot is True
    assert out.reason_code == ReasonCode.OK


def test_critico_si_categoria_mismatch():
    perfil = {"categoria_foco": "Laptops"}
    productos = [{"sku": "Y1", "nombre": "iphone", "categoria": "Celulares"}]
    respuesta = "Te muestro este iPhone — Bs 8.999 [Y1] como opcion para tu uso, esta perfecto."
    out = AutoQualityScorer.evaluar(respuesta, productos, perfil)
    assert out.apto_para_fewshot is False
    assert out.reason_code == ReasonCode.CATEGORY_MISMATCH


def test_critico_si_backend_leak():
    perfil = {}
    productos = []
    respuesta = "Disculpa hubo HTTP 502 al conectar con el catalogo, intentalo despues por favor."
    out = AutoQualityScorer.evaluar(respuesta, productos, perfil)
    assert out.apto_para_fewshot is False
    assert out.reason_code == ReasonCode.BACKEND_ERROR_VISIBLE


def test_critico_si_hard_filter_violado():
    perfil = {"ram_gb_min": 16}
    productos = [{"sku": "Z", "nombre": "vivobook", "categoria": "Laptops", "ram_gb": 4}]
    respuesta = "Te recomiendo el Asus Vivobook — Bs 3.500 [Z]. Es economico y cumple tus requisitos."
    out = AutoQualityScorer.evaluar(respuesta, productos, perfil)
    assert out.apto_para_fewshot is False
    assert out.reason_code == ReasonCode.HARD_FILTER_IGNORED


def test_critico_si_alucinacion_tecnica():
    perfil = {}
    productos = [{"sku": "T", "nombre": "TV LG", "categoria": "TV", "descripcion": "TV basica"}]
    respuesta = "Esta TV LG — Bs 5.999 [T] tiene HDMI 2.1 y 120Hz confirmados, ideal para PS5."
    out = AutoQualityScorer.evaluar(respuesta, productos, perfil)
    assert out.apto_para_fewshot is False
    assert out.reason_code == ReasonCode.TECHNICAL_HALLUCINATION
