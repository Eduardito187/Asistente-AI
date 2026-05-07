"""Skill de ejemplo: Black Friday y Cyber Monday.

Activa el último viernes de noviembre y los 4 días siguientes
(BF + sábado + domingo + Cyber Monday). Inyecta una nota al LLM
para enfatizar descuentos."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.application.services.skills import BaseSkill, ContextoSkill


class SkillBlackFriday(BaseSkill):
    nombre = "black_friday"
    prioridad = 60  # mayor que regalo_navidad (puede solapar fin de noviembre)

    def aplica(self, ctx: ContextoSkill) -> bool:
        return self._es_ventana_bf(ctx.ahora)

    def bloque_contexto(self, ctx: ContextoSkill) -> str | None:
        nombre_dia = self._etiqueta_dia(ctx.ahora)
        return (
            f"BLACK FRIDAY ACTIVO ({nombre_dia}): los descuentos son la "
            "estrella esta semana.\n"
            "- Si el cliente busca producto, priorizá `tiene_descuento=True` "
            "  o `descuento_pct_min=15`.\n"
            "- Cuando muestres un producto con precio rebajado, marcá el % "
            "  de descuento explícito en la respuesta.\n"
            "- Si no hay rebaja en lo que pidió, decilo honesto y ofrecé "
            "  algo similar que SÍ esté en oferta.\n"
            "- No inventes descuentos: solo los que vengan en la tool."
        )

    @classmethod
    def _es_ventana_bf(cls, ahora: datetime) -> bool:
        bf = cls._black_friday_de(ahora.year)
        cyber_monday = bf + timedelta(days=3)
        return bf.date() <= ahora.date() <= cyber_monday.date()

    @classmethod
    def _etiqueta_dia(cls, ahora: datetime) -> str:
        bf = cls._black_friday_de(ahora.year)
        delta = (ahora.date() - bf.date()).days
        return {
            0: "Black Friday",
            1: "Sábado de descuentos",
            2: "Domingo de descuentos",
            3: "Cyber Monday",
        }.get(delta, "ventana de descuentos")

    @staticmethod
    def _black_friday_de(anio: int) -> datetime:
        """4to viernes de noviembre."""
        # Día 1 de noviembre
        primero_nov = datetime(anio, 11, 1)
        # weekday(): lunes=0 ... viernes=4 ... domingo=6
        # Buscamos el primer viernes
        offset_primer_viernes = (4 - primero_nov.weekday()) % 7
        primer_viernes = primero_nov + timedelta(days=offset_primer_viernes)
        # 4to viernes = primero + 3 semanas
        return primer_viernes + timedelta(weeks=3)
