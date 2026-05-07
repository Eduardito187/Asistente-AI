from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .contexto_skill import ContextoSkill


class BaseSkill(ABC):
    """Interfaz que TODO skill custom debe implementar.

    Los skills se descubren automáticamente al startup escaneando
    `app/skills/`. Para crear uno:

    1. Crear archivo `backend/app/skills/skill_<nombre>.py`
    2. Heredar de BaseSkill
    3. Definir `nombre` único (usado para métricas + logs)
    4. Implementar `aplica()` — decide si se activa este turno
    5. Implementar AL MENOS UNO de:
       - `bloque_contexto()`: texto inyectado al system prompt del LLM
       - `short_circuit_respuesta()`: respuesta directa que corta el flujo
    6. Recompilar el backend (`docker compose up -d --build backend`)

    Convenciones:
    - `nombre` debe ser snake_case y único en el sistema.
    - `prioridad` mayor = se procesa primero (default 0).
    - Si dos skills devuelven short_circuit, gana el de mayor prioridad.
    - Si fallan al cargar, el SkillRegistry los ignora con warning (no rompe
      el sistema).
    """

    # Identificador único del skill (snake_case). Debe ser sobreescrito.
    nombre: str = "skill_anonimo"

    # Mayor prioridad = se evalúa primero. Default 0.
    # Sugerido: 100+ para skills críticos (compliance, seguridad),
    # 50 para promociones, 10 para tono/estilo, 0 default.
    prioridad: int = 0

    @abstractmethod
    def aplica(self, ctx: ContextoSkill) -> bool:
        """¿Este skill se activa para este turno? Lógica de matching
        (regex, fecha, perfil, etc.). Debe ser determinístico y rápido."""

    def bloque_contexto(self, ctx: ContextoSkill) -> Optional[str]:
        """Texto a inyectar al system prompt del LLM cuando aplica()=True.
        Default None (skill solo de short-circuit)."""
        return None

    def short_circuit_respuesta(self, ctx: ContextoSkill) -> Optional[str]:
        """Si retorna texto, corta el flujo y responde directo (sin LLM).
        Default None (skill solo de contexto)."""
        return None

    @property
    def nombre_metrica(self) -> str:
        """Etiqueta para métricas. No sobreescribir típicamente."""
        return f"skill_{self.nombre}"
