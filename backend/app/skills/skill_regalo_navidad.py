"""Skill de ejemplo: temporada navideña.

Activa cuando estamos entre 1 de noviembre y 7 de enero, e inyecta una
nota al LLM para priorizar productos con buen empaque/oferta navideña."""

from __future__ import annotations

from app.application.services.skills import BaseSkill, ContextoSkill


class SkillRegaloNavidad(BaseSkill):
    nombre = "regalo_navidad"
    prioridad = 50  # promoción temporal — mayor que skills de tono

    _MES_INICIO = 11   # noviembre
    _MES_FIN = 1       # enero
    _DIA_FIN = 7

    def aplica(self, ctx: ContextoSkill) -> bool:
        mes = ctx.ahora.month
        dia = ctx.ahora.day
        # Nov-Dic completos, o enero hasta el 7
        return mes >= self._MES_INICIO or (mes == self._MES_FIN and dia <= self._DIA_FIN)

    def bloque_contexto(self, ctx: ContextoSkill) -> str | None:
        return (
            "TEMPORADA NAVIDEÑA: estamos entre noviembre y la primera "
            "semana de enero. Si el cliente menciona 'regalo', 'navidad', "
            "'fin de año' o similar:\n"
            "- Priorizá productos con `empaque_regalo=True` o `para_regalo=True`.\n"
            "- Mencioná promociones navideñas si están en oferta.\n"
            "- Cerrá con tono cálido (sin abusar de emojis).\n"
            "Si NO mencionó nada navideño, ignorá esta nota — no fuerces "
            "el tema."
        )
