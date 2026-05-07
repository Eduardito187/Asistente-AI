"""Casos de regresion (#16 review). Cada caso define:

- mensaje_usuario: la frase del cliente
- perfil_estado: snapshot del perfil bloqueado en ese momento
- respuesta_agente: la respuesta a evaluar
- productos_citados: productos que cita la respuesta (con specs)
- expected: validators esperados (paso/falla)

El runner ejecuta los validators determinsticos sobre cada caso y verifica
que el quality gate produzca lo esperado. NO invoca al LLM — esto es
control de calidad sobre la capa deterministica."""

from app.domain.aprendizaje import ReasonCode

CASOS = [
    {
        "id": "ingenieria_civil_no_chromebook",
        "descripcion": "Cliente pide laptop ingenieria; respuesta recomienda Chromebook.",
        "perfil_estado": {
            "categoria_foco": "Laptops",
            "uso_declarado": "ingenieria",
            "ram_gb_min": 16,
            "ssd_gb_min": 512,
            "gpu_dedicada": True,
            "nombre_excluye_acum": "chromebook,celeron,emmc",
        },
        "respuesta_agente": (
            "Te recomiendo este Lenovo Chromebook 4GB RAM 32GB eMMC — Bs 2.500 [LEN-CB1]. "
            "Buena opcion para tu uso de ingenieria civil. Tiene 12 horas de bateria."
        ),
        "productos_citados": [{
            "sku": "LEN-CB1",
            "nombre": "Lenovo Chromebook 4GB",
            "categoria": "Laptops",
            "ram_gb": 4,
            "capacidad_gb": 32,
            "gpu": None,
            "precio_bob": 2500,
        }],
        "expected_apto": False,
        "expected_reason_critico": ReasonCode.HARD_FILTER_IGNORED,
    },
    {
        "id": "presupuesto_8500_categoria_celular",
        "descripcion": "Despues de pedir laptop, presupuesto cambia categoria a celular.",
        "perfil_estado": {
            "categoria_foco": "Laptops",
            "uso_declarado": "ingenieria",
            "presupuesto_max": 8500,
        },
        "respuesta_agente": (
            "Te ofrezco el Realme Note 60 — Bs 1.529 [REL-N60]. "
            "Excelente celular dentro de tu presupuesto."
        ),
        "productos_citados": [{
            "sku": "REL-N60",
            "nombre": "Realme Note 60",
            "categoria": "Celulares",
            "precio_bob": 1529,
        }],
        "expected_apto": False,
        "expected_reason_critico": ReasonCode.CATEGORY_MISMATCH,
    },
    {
        "id": "tv_hdmi21_alucinado",
        "descripcion": "Respuesta afirma HDMI 2.1 cuando la ficha no lo confirma.",
        "perfil_estado": {"categoria_foco": "TV"},
        "respuesta_agente": (
            "Esta TV LG 55 — Bs 5.999 [LG-55]. Tiene HDMI 2.1 confirmado y 120Hz, "
            "ideal para tu PS5."
        ),
        "productos_citados": [{
            "sku": "LG-55",
            "nombre": "LG TV 55",
            "categoria": "TV",
            "descripcion": "TV smart 4K basica",
            "precio_bob": 5999,
        }],
        "expected_apto": False,
        "expected_reason_critico": ReasonCode.TECHNICAL_HALLUCINATION,
    },
    {
        "id": "backend_error_visible",
        "descripcion": "Respuesta expone HTTP 502 al cliente.",
        "perfil_estado": {},
        "respuesta_agente": (
            "Disculpa, hubo HTTP 502 al conectar con el catalogo, intentalo despues."
        ),
        "productos_citados": [],
        "expected_apto": False,
        "expected_reason_critico": ReasonCode.BACKEND_ERROR_VISIBLE,
    },
    {
        "id": "respuesta_buena_ingenieria",
        "descripcion": "Respuesta correcta para ingenieria con todos los requisitos cumplidos.",
        "perfil_estado": {
            "categoria_foco": "Laptops",
            "uso_declarado": "ingenieria",
            "ram_gb_min": 16,
            "ssd_gb_min": 512,
            "gpu_dedicada": True,
            "presupuesto_max": 11000,
        },
        "respuesta_agente": (
            "Te recomiendo el Acer Nitro V — Bs 8.799 [ACE-NV]. Cumple tus requisitos: "
            "16GB RAM, SSD 512GB y RTX 5050 confirmada. Ideal para AutoCAD y Civil 3D."
        ),
        "productos_citados": [{
            "sku": "ACE-NV",
            "nombre": "Acer Nitro V i5-13420H 16GB 512GB RTX 5050",
            "categoria": "Laptops",
            "procesador": "Core i5-13420H",
            "ram_gb": 16,
            "capacidad_gb": 512,
            "gpu": "GeForce RTX 5050",
            "precio_bob": 8799,
        }],
        "expected_apto": True,
        "expected_reason_critico": ReasonCode.OK,
    },
    {
        "id": "ram_min_16_pero_recomienda_8gb",
        "descripcion": "Cliente exigio 16GB; respuesta recomienda 8GB como principal.",
        "perfil_estado": {
            "categoria_foco": "Laptops",
            "ram_gb_min": 16,
        },
        "respuesta_agente": (
            "Te recomiendo el HP Vivobook — Bs 5.999 [HP-VB]. "
            "Tiene 8GB RAM y SSD 512GB, ideal para uso general."
        ),
        "productos_citados": [{
            "sku": "HP-VB",
            "nombre": "HP Vivobook 8GB",
            "categoria": "Laptops",
            "ram_gb": 8,
            "capacidad_gb": 512,
            "precio_bob": 5999,
        }],
        "expected_apto": False,
        "expected_reason_critico": ReasonCode.HARD_FILTER_IGNORED,
    },
    {
        "id": "exclusion_celeron_pero_recomienda_celeron",
        "descripcion": "Cliente excluyo Celeron; respuesta lo recomienda.",
        "perfil_estado": {
            "categoria_foco": "Laptops",
            "nombre_excluye_acum": "celeron,pentium",
        },
        "respuesta_agente": (
            "Te ofrezco el Asus Vivobook Go Celeron — Bs 3.149 [ASU-CEL]. "
            "Buena opcion economica."
        ),
        "productos_citados": [{
            "sku": "ASU-CEL",
            "nombre": "Asus Vivobook Go Celeron N4500",
            "categoria": "Laptops",
            "precio_bob": 3149,
        }],
        "expected_apto": False,
        "expected_reason_critico": ReasonCode.HARD_FILTER_IGNORED,
    },
]
