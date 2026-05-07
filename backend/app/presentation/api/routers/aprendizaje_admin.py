from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from ....application.commands.registrar_feedback_turno import (
    RegistrarFeedbackTurnoCommand,
    RegistrarFeedbackTurnoHandler,
)
from ....domain.conversaciones_curadas import ConversacionCurada
from ....domain.golden_conversations import GoldenConversation
from ....domain.negative_patterns import NegativePattern
from ..deps import uow_factory

router = APIRouter(prefix="/admin/aprendizaje", tags=["aprendizaje"])


class FeedbackInput(BaseModel):
    sesion_id: str
    turno_index: int = 0
    voto: str  # "up" | "down"
    mensaje_usuario: str | None = None
    respuesta_agente: str | None = None
    comentario: str | None = None


class CuracionManualInput(BaseModel):
    sesion_id: str
    cliente_texto: str
    asistente_texto: str
    etiqueta: str | None = "manual"
    score: int = 90


class GoldenInput(BaseModel):
    caso_que_cubre: str
    categoria: str | None = None
    intencion: str | None = "recomendacion"
    uso: str | None = None
    cliente_texto: str
    asistente_texto: str
    prioridad: int = 100
    errores_que_previene: list[str] = []


class NegativePatternInput(BaseModel):
    patron: str
    reason_code: str | None = None
    descripcion: str | None = None
    activo: bool = True


class DesactivarFewshotInput(BaseModel):
    motivo: str
    reason_code: str | None = None


@router.get("/fallos")
def listar_fallos(limite: int = Query(50, ge=1, le=500)) -> dict:
    """Lista los ultimos turnos donde el agente cayo al fallback. Sirve para
    descubrir patrones que requieren mejora del prompt o del codigo."""
    with uow_factory() as uow:
        items = uow.conversaciones_fallidas.listar_recientes(limite=limite)
        contadores = uow.conversaciones_fallidas.contar_por_razon()
    return {
        "total_por_razon": contadores,
        "items": [
            {
                "id": x.id,
                "sesion_id": str(x.sesion_id) if x.sesion_id else None,
                "mensaje": x.mensaje_usuario,
                "razon": x.razon_fallo,
                "trace": x.trace_resumen,
                "perfil": x.perfil_estado,
                "creado_en": x.creado_en.isoformat() if x.creado_en else None,
            }
            for x in items
        ],
    }


@router.get("/synonyms_candidatos")
def listar_synonyms(
    limite: int = Query(50, ge=1, le=500),
    solo_no_promovidos: bool = Query(True),
) -> dict:
    """Lista terminos que aparecieron repetidamente sin resolver. Cuanto mas
    arriba, mas urgente registrarlos como sinonimos en el catalogo."""
    with uow_factory() as uow:
        items = uow.synonyms_candidatos.listar_top(
            limite=limite, solo_no_promovidos=solo_no_promovidos
        )
    return {
        "items": [
            {
                "id": x.id,
                "termino": x.termino,
                "categoria_inferida": x.categoria_inferida,
                "ocurrencias": x.ocurrencias,
                "primera_vez": x.primera_vez.isoformat(),
                "ultima_vez": x.ultima_vez.isoformat(),
                "promovido": x.promovido,
            }
            for x in items
        ],
    }


@router.post("/synonyms_candidatos/{id_}/promover")
def promover_synonym(id_: int) -> dict:
    """Marca un candidato como promovido (lo registraste manualmente en
    categorias_sinonimos)."""
    with uow_factory() as uow:
        uow.synonyms_candidatos.marcar_promovido(id_)
        uow.commit()
    return {"ok": True, "id": id_}


@router.post("/feedback")
def registrar_feedback(inp: FeedbackInput) -> dict:
    """Voto thumbs up/down sobre un turno especifico. Aplica efectos:
    - up: si el turno no estaba curado, se promueve a ConversacionCurada
    - down (>=2 sobre la misma sesion): desactiva su few-shot"""
    handler = RegistrarFeedbackTurnoHandler(uow_factory)
    fb_id = handler.ejecutar(RegistrarFeedbackTurnoCommand(
        sesion_id=UUID(inp.sesion_id),
        turno_index=inp.turno_index,
        voto=inp.voto,
        mensaje_usuario=inp.mensaje_usuario,
        respuesta_agente=inp.respuesta_agente,
        comentario=inp.comentario,
    ))
    if fb_id == 0:
        raise HTTPException(status_code=400, detail="voto invalido o error al persistir")
    return {"ok": True, "id": fb_id}


@router.post("/curacion_manual")
def curar_manual(inp: CuracionManualInput) -> dict:
    """Convierte una conversacion en ConversacionCurada manualmente. Util
    cuando vos viste un turno bueno y queres usarlo como few-shot. Si ya
    existia para esa sesion, la actualiza."""
    ahora = datetime.now(timezone.utc)
    sid = UUID(inp.sesion_id)
    with uow_factory() as uow:
        existente = uow.conversaciones_curadas.por_sesion(sid)
        conv = ConversacionCurada(
            id=existente.id if existente else None,
            sesion_id=sid,
            etiqueta=inp.etiqueta or "manual",
            cliente_texto=inp.cliente_texto[:1000],
            asistente_texto=inp.asistente_texto[:2000],
            score=int(inp.score),
            turnos=1,
            llevo_a_orden=False,
            activa=True,
            created_at=existente.created_at if existente else ahora,
            updated_at=ahora,
        )
        if existente is None:
            uow.conversaciones_curadas.guardar(conv)
        else:
            uow.conversaciones_curadas.actualizar(conv)
        uow.commit()
    return {"ok": True, "sesion_id": inp.sesion_id}


@router.get("/dashboard")
def dashboard() -> dict:
    """Vista unica del estado de aprendizaje. Mostra:
    - cuantos fallos por razon
    - top synonyms candidatos sin promover
    - conteo de feedback up vs down
    - ultimas conversaciones auto-curadas activas"""
    with uow_factory() as uow:
        fallos = uow.conversaciones_fallidas.contar_por_razon()
        top_synonyms = uow.synonyms_candidatos.listar_top(limite=10, solo_no_promovidos=True)
        feedback_stats = uow.feedback_turnos.stats()
        curadas_activas = uow.conversaciones_curadas.top_activas(limite=10)
    return {
        "fallos_por_razon": fallos,
        "top_synonyms_pendientes": [
            {"id": s.id, "termino": s.termino, "ocurrencias": s.ocurrencias}
            for s in top_synonyms
        ],
        "feedback": feedback_stats,
        "ultimas_curadas_activas": [
            {
                "id": c.id, "etiqueta": c.etiqueta, "score": c.score,
                "cliente": (c.cliente_texto or "")[:80],
            }
            for c in curadas_activas
        ],
        "como_entrenar": {
            "1_revisar_fallos": "GET /admin/aprendizaje/fallos",
            "2_promover_synonyms": "POST /admin/aprendizaje/synonyms_candidatos/{id}/promover",
            "3_curar_manual": "POST /admin/aprendizaje/curacion_manual",
            "4_feedback_turno": "POST /admin/aprendizaje/feedback",
            "5_listar_curadas": "GET /admin/conversaciones_curadas",
            "6_desactivar_curada": "POST /admin/conversaciones_curadas/{id}/activar (activa=false)",
        },
    }


@router.get("/feedback")
def listar_feedback(
    voto: str = Query("down", regex="^(up|down)$"),
    limite: int = Query(50, ge=1, le=500),
) -> dict:
    """Lista feedback explicito del usuario para revisar."""
    with uow_factory() as uow:
        if voto == "up":
            items = uow.feedback_turnos.listar_positivos(limite=limite)
        else:
            items = uow.feedback_turnos.listar_negativos(limite=limite)
    return {
        "items": [
            {
                "id": f.id,
                "sesion_id": str(f.sesion_id),
                "voto": f.voto.value,
                "mensaje": f.mensaje_usuario,
                "respuesta": f.respuesta_agente,
                "comentario": f.comentario,
                "creado_en": f.creado_en.isoformat() if f.creado_en else None,
            }
            for f in items
        ],
    }


@router.get("/goldens")
def listar_goldens(limite: int = Query(50, ge=1, le=200)) -> dict:
    """Lista golden conversations activas — ejemplos perfectos curados
    manualmente que tienen prioridad sobre auto-curados (#8 review)."""
    with uow_factory() as uow:
        items = uow.golden_conversations.listar_activas(limite=limite)
    return {
        "items": [
            {
                "id": g.id, "caso_que_cubre": g.caso_que_cubre,
                "categoria": g.categoria, "intencion": g.intencion, "uso": g.uso,
                "prioridad": g.prioridad,
                "errores_que_previene": g.errores_que_previene,
                "cliente_texto": (g.cliente_texto or "")[:200],
                "asistente_texto": (g.asistente_texto or "")[:300],
            }
            for g in items
        ],
    }


@router.post("/goldens")
def crear_golden(inp: GoldenInput) -> dict:
    """Crea o actualiza un golden por caso_que_cubre (clave unica).
    Estos ejemplos siempre tienen prioridad ante auto-curados al inyectarse."""
    g = GoldenConversation(
        id=None,
        caso_que_cubre=inp.caso_que_cubre,
        categoria=inp.categoria,
        intencion=inp.intencion,
        uso=inp.uso,
        cliente_texto=inp.cliente_texto,
        asistente_texto=inp.asistente_texto,
        prioridad=int(inp.prioridad),
        activo=True,
        errores_que_previene=list(inp.errores_que_previene),
    )
    with uow_factory() as uow:
        uow.golden_conversations.upsert(g)
        uow.commit()
    return {"ok": True, "caso_que_cubre": inp.caso_que_cubre}


@router.post("/goldens/{caso_que_cubre}/desactivar")
def desactivar_golden(caso_que_cubre: str) -> dict:
    with uow_factory() as uow:
        uow.golden_conversations.desactivar(caso_que_cubre)
        uow.commit()
    return {"ok": True, "caso_que_cubre": caso_que_cubre}


@router.get("/negative_patterns")
def listar_negative_patterns() -> dict:
    """Patrones prohibidos: reglas que el agente NUNCA debe violar.
    Ejemplo: 'no recomendar Chromebook si el cliente pidio ingenieria'."""
    with uow_factory() as uow:
        items = uow.negative_patterns.listar_activos()
    return {
        "items": [
            {
                "id": n.id, "patron": n.patron,
                "reason_code": n.reason_code,
                "descripcion": n.descripcion,
                "ocurrencias_observadas": n.ocurrencias_observadas,
            }
            for n in items
        ],
    }


@router.post("/negative_patterns")
def crear_negative_pattern(inp: NegativePatternInput) -> dict:
    np = NegativePattern(
        id=None,
        patron=inp.patron,
        reason_code=inp.reason_code,
        descripcion=inp.descripcion,
        activo=bool(inp.activo),
        ocurrencias_observadas=0,
    )
    with uow_factory() as uow:
        uow.negative_patterns.upsert(np)
        uow.commit()
    return {"ok": True, "patron": inp.patron}


@router.post("/fewshots/{id_}/desactivar")
def desactivar_fewshot(id_: int, inp: DesactivarFewshotInput) -> dict:
    """Desactivar manual un few-shot con motivo + reason_code para auditoria
    (#13 del review)."""
    with uow_factory() as uow:
        uow.conversaciones_curadas.set_activa(id_, False)
        uow.commit()
    return {"ok": True, "id": id_, "motivo": inp.motivo, "reason_code": inp.reason_code}


@router.get("/metricas")
def metricas_calidad() -> dict:
    """Dashboard de RATES (no conteos crudos) — #10 del review.

    Reporta % violaciones criticas, % fallback, % category_mismatch, etc.,
    sobre las ultimas 500 metricas registradas."""
    with uow_factory() as uow:
        sess = uow._session  # acceso directo solo para esta agregacion
        rows = sess.execute(__import__("sqlalchemy").text(
            "SELECT ruta, reason_code, quality_score, prompt_version, productos_citados "
            "FROM metricas_turno ORDER BY id DESC LIMIT 500"
        )).mappings().all()
    total = max(len(rows), 1)
    fallback = sum(1 for r in rows if (r.get("ruta") or "").endswith("sin_avance"))
    sin_productos = sum(1 for r in rows if (r.get("productos_citados") or 0) == 0)
    quality_avg = (
        sum(r.get("quality_score") or 0 for r in rows if r.get("quality_score"))
        / max(sum(1 for r in rows if r.get("quality_score")), 1)
    )
    reasons: dict = {}
    for r in rows:
        rc = r.get("reason_code") or "OK"
        reasons[rc] = reasons.get(rc, 0) + 1
    versiones = {}
    for r in rows:
        v = r.get("prompt_version") or "unversioned"
        versiones[v] = versiones.get(v, 0) + 1
    return {
        "total_metricas_evaluadas": total,
        "rate_fallback": round(fallback / total * 100, 2),
        "rate_sin_productos": round(sin_productos / total * 100, 2),
        "quality_score_promedio": round(quality_avg, 1),
        "distribucion_reason_codes": reasons,
        "distribucion_prompt_versions": versiones,
        "interpretacion": (
            "rate_fallback debe tender a 0%; rate_sin_productos < 30%; "
            "quality_score_promedio > 80; reason_codes criticos (CATEGORY_MISMATCH, "
            "HARD_FILTER_IGNORED, TECHNICAL_HALLUCINATION) deben ser ~0."
        ),
    }


@router.get("/fewshot_candidatos")
def fewshot_candidatos(
    score_min: int = Query(85, ge=0, le=100),
    limite: int = Query(20, ge=1, le=100),
) -> dict:
    """Conversaciones curadas activas con score>=N — candidatos a promoverse
    como golden si vos validas el contenido (#12 del review)."""
    with uow_factory() as uow:
        rows = uow.conversaciones_curadas.top_activas(limite=limite * 3)
        items = [c for c in rows if (c.score or 0) >= score_min][:limite]
    return {
        "items": [
            {
                "id": c.id, "etiqueta": c.etiqueta, "score": c.score,
                "sesion_id": str(c.sesion_id) if c.sesion_id else None,
                "cliente": (c.cliente_texto or "")[:160],
                "asistente": (c.asistente_texto or "")[:240],
            }
            for c in items
        ],
    }


@router.post("/synonyms_candidatos/{id_}/rechazar")
def rechazar_synonym(id_: int) -> dict:
    """Marca un candidato como rechazado: no es sinonimo valido. Quedara
    en la tabla con estado=rechazado para que no aparezca de nuevo en el
    top de pendientes (#22 del review)."""
    with uow_factory() as uow:
        sess = uow._session
        sess.execute(
            __import__("sqlalchemy").text(
                "UPDATE synonyms_candidatos SET estado='rechazado', "
                "rejected_at=CURRENT_TIMESTAMP WHERE id=:id_"
            ),
            {"id_": int(id_)},
        )
        uow.commit()
    return {"ok": True, "id": id_}
