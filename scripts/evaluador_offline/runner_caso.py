from __future__ import annotations

from .cliente_chat import ClienteChat
from .resultado_caso import ResultadoCaso
from .verificador_turno import VerificadorTurno


class RunnerCaso:
    """SRP: ejecutar un caso dorado (multi-turno) contra el backend vivo."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def correr(self, caso: dict) -> ResultadoCaso:
        cliente = ClienteChat(self._base_url)
        resultado = ResultadoCaso(nombre=caso["nombre"])
        for idx, turno in enumerate(caso.get("turnos") or []):
            respuesta = cliente.enviar(turno["mensaje"])
            asertos = VerificadorTurno.verificar(turno, respuesta)
            for a in asertos:
                resultado.asertos.append(
                    a.__class__(nombre=f"turno{idx+1}.{a.nombre}", ok=a.ok, detalle=a.detalle)
                )
        return resultado
