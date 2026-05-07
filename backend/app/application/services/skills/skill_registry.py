from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import Optional

from .base_skill import BaseSkill
from .contexto_skill import ContextoSkill

log = logging.getLogger("skill_registry")


class SkillRegistry:
    """Descubre y mantiene registro de skills custom.

    Al construirse, escanea recursivamente el paquete configurado
    (default `app.skills`) y carga toda subclase concreta de BaseSkill
    que encuentre. Las skills inválidas (errores de import, sin nombre,
    aplica=falla) son ignoradas con WARNING — nunca rompen el startup.

    Uso desde el orquestador:
        registry.bloques_contexto(ctx)        → list[str] activos
        registry.short_circuit_respuesta(ctx) → (skill_nombre, texto) | None
        registry.descubiertos()                → list[BaseSkill]

    Para agregar un skill nuevo: archivo en backend/app/skills/ + rebuild."""

    def __init__(self, paquete: str = "app.skills") -> None:
        self._paquete = paquete
        self._skills: list[BaseSkill] = []
        self._cargar()

    # ===== API publica =====================================================

    def descubiertos(self) -> list[BaseSkill]:
        """Lista de skills cargados (ordenados por prioridad descendente)."""
        return list(self._skills)

    def cuenta(self) -> int:
        return len(self._skills)

    def bloques_contexto(self, ctx: ContextoSkill) -> list[tuple[str, str]]:
        """Devuelve [(nombre_skill, bloque)] de los skills activos para
        este turno. Orquestador los concatena al system prompt."""
        salida: list[tuple[str, str]] = []
        for skill in self._skills:
            if not self._aplica_safe(skill, ctx):
                continue
            try:
                bloque = skill.bloque_contexto(ctx)
            except Exception:
                log.warning("skill %s.bloque_contexto fallo", skill.nombre, exc_info=True)
                continue
            if bloque:
                salida.append((skill.nombre, bloque))
        return salida

    def short_circuit_respuesta(self, ctx: ContextoSkill) -> Optional[tuple[str, str]]:
        """Si algún skill activo retorna texto en short_circuit_respuesta(),
        devuelve (nombre, texto) del primero (mayor prioridad). None si
        ningún skill quiere cortar el flujo."""
        for skill in self._skills:
            if not self._aplica_safe(skill, ctx):
                continue
            try:
                respuesta = skill.short_circuit_respuesta(ctx)
            except Exception:
                log.warning("skill %s.short_circuit fallo", skill.nombre, exc_info=True)
                continue
            if respuesta:
                return skill.nombre, respuesta
        return None

    # ===== Internos ========================================================

    def _aplica_safe(self, skill: BaseSkill, ctx: ContextoSkill) -> bool:
        """Llama a aplica() capturando excepciones para no tirar el turno."""
        try:
            return bool(skill.aplica(ctx))
        except Exception:
            log.warning("skill %s.aplica fallo", skill.nombre, exc_info=True)
            return False

    def _cargar(self) -> None:
        """Importa el paquete de skills y registra subclases concretas
        de BaseSkill encontradas."""
        try:
            paquete = importlib.import_module(self._paquete)
        except ModuleNotFoundError:
            log.info("paquete de skills %r no existe — agente sin skills", self._paquete)
            return

        encontrados: list[BaseSkill] = []
        for _, modname, _ in pkgutil.walk_packages(paquete.__path__, paquete.__name__ + "."):
            try:
                modulo = importlib.import_module(modname)
            except Exception:
                log.warning("falla cargando skill modulo %s", modname, exc_info=True)
                continue
            encontrados.extend(self._instanciar_skills_del_modulo(modulo))

        encontrados.sort(key=lambda s: -s.prioridad)
        self._skills = encontrados
        nombres = [s.nombre for s in self._skills]
        log.info("skills cargados: %d -> %s", len(self._skills), nombres)

    @staticmethod
    def _instanciar_skills_del_modulo(modulo) -> list[BaseSkill]:
        """Encuentra subclases concretas de BaseSkill en el módulo y
        devuelve instancias."""
        instancias: list[BaseSkill] = []
        for _, clase in inspect.getmembers(modulo, inspect.isclass):
            if clase is BaseSkill:
                continue
            if not issubclass(clase, BaseSkill):
                continue
            if inspect.isabstract(clase):
                continue
            # Solo instancia clases definidas en el módulo (no las importadas).
            if clase.__module__ != modulo.__name__:
                continue
            try:
                instancias.append(clase())
            except Exception:
                log.warning("no se pudo instanciar skill %s", clase.__name__, exc_info=True)
        return instancias
