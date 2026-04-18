from __future__ import annotations

import re

from .regla_mentira import ReglaMentira

REGLAS_MENTIRA: list[ReglaMentira] = [
    ReglaMentira(
        tool="agregar_al_carrito",
        patron=re.compile(
            r"\b(agregu[ée]|agreg(?:ado|ada|ados|adas)|añad[íi]|añadid[oa]s?|"
            r"sum[ée]|sumad[oa]s?|"
            r"se (?:ha|han) (?:agregad|añadid|sumad)[oa]s?|"
            r"(?:ha|han) sido (?:agregad|añadid|sumad)[oa]s?|"
            r"se agregar(?:on|á))",
            re.IGNORECASE,
        ),
    ),
    ReglaMentira(
        tool="quitar_del_carrito",
        patron=re.compile(
            r"\b(quit[ée]|quitad[oa]s?|saqu[ée]|sacad[oa]s?|"
            r"elimin[ée]|eliminad[oa]s?|retir[ée]|retirad[oa]s?|remov[íi]|removid[oa]s?|"
            r"se (?:ha|han) (?:quitad|sacad|eliminad|retirad|removid)[oa]s?|"
            r"(?:ha|han) sido (?:quitad|sacad|eliminad|retirad|removid)[oa]s?)",
            re.IGNORECASE,
        ),
    ),
    ReglaMentira(
        tool="vaciar_carrito",
        patron=re.compile(
            r"\b(vaci[ée]|vaciad[oa]|bo?rr[ée] (?:todo )?el carrito|"
            r"se (?:ha|han) vaciad[oa]|(?:ha|han) sido vaciad[oa]|"
            r"carrito (?:vacío|quedó vacío|está vacío))",
            re.IGNORECASE,
        ),
    ),
]
