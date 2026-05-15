from __future__ import annotations

import re

from .detector_exclusiones_mensaje import DetectorExclusionesMensaje


class BloqueSubcategoriaExcluida:
    """SRP: cuando la categoría del mensaje implica exclusiones claras de
    subcategorías, inyecta una directiva dura al LLM con los valores exactos
    de tipo_producto_excluye que debe pasar a buscar_productos, y las reglas
    de render para datos técnicos no confirmados en ficha.

    Casos cubiertos:
      - refrigeradora → excluir frigobar/minibar/freezer/exhibidor
      - TV para PS5/gaming → 120Hz y HDMI 2.1 deben estar confirmados o decir
        exactamente "No tengo ese dato en la ficha técnica."
      - lavadora automática → no puede aparecer semiautomática como principal
    """

    _KW_REFRI = re.compile(
        r'\b(?:refrigeradora|refrigerador|refri|heladera)\b', re.IGNORECASE
    )
    _KW_QUIERE_FRIGOBAR = re.compile(r'\b(?:frigobar|minibar)\b', re.IGNORECASE)
    _KW_QUIERE_FREEZER = re.compile(r'\b(?:freezer|congeladora)\b', re.IGNORECASE)

    _KW_TV_GAMING = re.compile(
        r'\b(?:ps5|xbox|gamer|gaming|120\s*hz|hdmi\s*2[.,]1)\b',
        re.IGNORECASE,
    )
    _KW_TV_CAT = re.compile(
        r'\b(?:televisor|tv|tele)\b', re.IGNORECASE
    )

    _KW_LAVADORA = re.compile(r'\blavadora\b', re.IGNORECASE)
    _KW_AUTO = re.compile(r'\bautom[aá]tica\b', re.IGNORECASE)
    _KW_SEMIAUTO = re.compile(r'\bsemi[\s-]?autom[aá]tica\b', re.IGNORECASE)

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje:
            return None
        partes: list[str] = []

        if cls._KW_REFRI.search(mensaje):
            quiere_frigobar = bool(cls._KW_QUIERE_FRIGOBAR.search(mensaje))
            quiere_freezer = bool(cls._KW_QUIERE_FREEZER.search(mensaje))
            tipos = DetectorExclusionesMensaje.tipos_a_excluir(mensaje)
            tipos_base = ["frigobar", "minibar", "freezer", "exhibidor", "vitrina"]
            tipos_all = list(dict.fromkeys(tipos_base + list(tipos or [])))[:8]
            tipos_str = ", ".join(f'"{t}"' for t in tipos_all)
            if not quiere_frigobar and not quiere_freezer:
                partes.append(
                    f"EXCLUSIÓN OBLIGATORIA — REFRIGERADORA DOMÉSTICA:\n"
                    f"  Al llamar buscar_productos, pasá "
                    f"tipo_producto_excluye=[{tipos_str}].\n"
                    f"  TAMBIÉN pasá nombre_excluye=[\"hermetico\",\"tupper\",\"recipiente\"].\n"
                    f"  NUNCA muestres frigobares, minibars, exhibidores, vitrinas, "
                    f"freezers horizontales NI herméticos/recipientes/tuppers cuando el "
                    f"cliente pide una refrigeradora doméstica.\n"
                    f"  Si solo hay esas opciones, decí: 'No encontré refrigeradoras "
                    f"domésticas en ese rango — solo frigobares/exhibidores que no son "
                    f"lo que necesitás.'"
                )

        if cls._KW_TV_CAT.search(mensaje) and cls._KW_TV_GAMING.search(mensaje):
            partes.append(
                "DATOS TÉCNICOS CRÍTICOS — TV PARA PS5/GAMING:\n"
                "  Para cada TV que muestres, debés indicar explícitamente:\n"
                "  - 120 Hz: si el campo no está en ficha, escribí EXACTAMENTE "
                "'No tengo ese dato en la ficha técnica.' (NUNCA supongas ni inferás).\n"
                "  - HDMI 2.1: mismo criterio — confirmado o 'No tengo ese dato en la "
                "ficha técnica.'\n"
                "  - REGLA: NO llames a una TV 'ideal para PS5', 'gamer' ni 'gaming' a "
                "menos que tenga 120 Hz Y HDMI 2.1 AMBOS confirmados en ficha. Si falta "
                "uno, llamala 'TV 4K/QLED para sala' y mencioná el dato no confirmado."
            )

        # QLED como preferencia blanda — evita que el LLM bloquee si no hay QLED
        if cls._KW_TV_CAT.search(mensaje) and re.search(
            r'\bqled\b.*\b(?:si\s+(?:se\s+puede|hay|tenés?)|idealmente|preferiblemente|prefer)\b'
            r'|\b(?:idealmente|preferiblemente)\b.*\bqled\b',
            mensaje, re.IGNORECASE
        ):
            partes.append(
                "PREFERENCIA BLANDA — QLED:\n"
                "  QLED es preferencia, NO requisito obligatorio.\n"
                "  Si no hay QLED disponible: NO digas 'no tenemos QLED'. En cambio:\n"
                "  - Buscá la mejor TV LED/Smart TV 65\" 4K dentro del presupuesto.\n"
                "  - Indicá: 'No encontré QLED en esta búsqueda; te muestro la mejor "
                "opción LED 4K disponible.'\n"
                "  Nunca dejes al cliente sin opciones por una preferencia blanda."
            )

        if (
            cls._KW_LAVADORA.search(mensaje)
            and cls._KW_AUTO.search(mensaje)
            and not cls._KW_SEMIAUTO.search(mensaje)
        ):
            partes.append(
                "EXCLUSIÓN — LAVADORA AUTOMÁTICA:\n"
                "  El cliente pidió lavadora automática. NUNCA presentes una "
                "lavadora semiautomática como opción principal ni como alternativa "
                "equivalente — son categorías distintas con operación diferente."
            )

        return "\n\n".join(partes) if partes else None
