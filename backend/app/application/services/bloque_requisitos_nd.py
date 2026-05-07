from __future__ import annotations

from .detector_requisitos_nd_obligatorios import DetectorRequisitosNDObligatorios


class BloqueRequisitosND:
    """SRP: si el cliente declaro requisitos cuya ausencia en ficha es comun
    (HDMI 2.1, 120Hz, inverter, GPU dedicada, etc), inyecta una directiva
    al LLM forzando el formato 'X: No tengo ese dato en la ficha tecnica'
    por cada producto citado."""

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        requisitos = DetectorRequisitosNDObligatorios.requisitos(mensaje)
        if not requisitos:
            return None
        listado = "; ".join(requisitos)
        return (
            "REQUISITOS DECLARADOS POR EL CLIENTE QUE PUEDEN FALTAR EN FICHA: "
            f"{listado}.\n"
            "Por CADA producto citado, indica explicitamente:\n"
            "  - si la ficha tecnica confirma el requisito -> dato real\n"
            "  - si la ficha NO lo confirma -> 'No tengo ese dato en la ficha tecnica'\n"
            "NO inferir desde el nombre comercial, descripcion de marketing o precio. "
            "Por ejemplo: 'gamer' en el titulo NO confirma 120Hz/HDMI 2.1; "
            "'i7' NO confirma GPU dedicada; precio alto NO confirma OIS o ANC."
        )
