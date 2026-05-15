from fastapi import APIRouter

from ..deps import llm_port

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"ok": True, "servicio": "asistente-dismac"}


@router.get("/health/circuit-breaker")
def circuit_breaker_status() -> dict:
    """Estado del circuit breaker del LLM. Útil para monitoring."""
    cb = llm_port()
    return {
        "estado": cb.estado.value,
        "ok": cb.estado.value == "cerrado",
    }
