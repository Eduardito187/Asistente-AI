"""Sistema de skills custom para el agente.

Para crear un skill nuevo:
1. Crear archivo en `backend/app/skills/skill_<nombre>.py`.
2. Heredar de BaseSkill, implementar `aplica()` + uno de
   (`bloque_contexto`, `short_circuit_respuesta`).
3. Recompilar el backend.

Más detalles en `backend/app/skills/README.md`."""

from .base_skill import BaseSkill
from .contexto_skill import ContextoSkill
from .skill_registry import SkillRegistry

__all__ = ["BaseSkill", "ContextoSkill", "SkillRegistry"]
