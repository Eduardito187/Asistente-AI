from __future__ import annotations

from typing import Optional


class GeneradorResumenConversacion:
    """Genera un resumen de la conversación para el agente humano al hacer handoff.

    SRP: solo construir texto de resumen. No persiste ni llama APIs."""

    _MAX_MENS = 8    # últimos N mensajes a considerar
    _MAX_CHARS = 120  # máx chars por mensaje resumido

    @classmethod
    def resumir(
        cls,
        historial_user: list[str],
        historial_assistant: list[str],
        perfil_resumen: Optional[str] = None,
    ) -> str:
        """Retorna texto de resumen multi-línea listo para pegar en el mensaje
        de derivación. Máximo ~400 caracteres."""
        partes: list[str] = ["📋 Resumen de la conversación:"]

        if perfil_resumen:
            partes.append(f"• {perfil_resumen}")

        # Últimos mensajes del usuario (los más recientes primero)
        msgs_user = [m for m in (historial_user or []) if m and m.strip()]
        if msgs_user:
            ultimos = msgs_user[-cls._MAX_MENS:]
            for msg in ultimos[-3:]:  # solo los 3 últimos
                recortado = msg.strip()[:cls._MAX_CHARS]
                if len(msg.strip()) > cls._MAX_CHARS:
                    recortado += "…"
                partes.append(f"👤 {recortado}")

        # Último mensaje del assistant (qué ofreció)
        msgs_asst = [m for m in (historial_assistant or []) if m and m.strip()]
        if msgs_asst:
            ultimo_asst = msgs_asst[-1].strip()[:cls._MAX_CHARS]
            if len(msgs_asst[-1].strip()) > cls._MAX_CHARS:
                ultimo_asst += "…"
            partes.append(f"🤖 {ultimo_asst}")

        return "\n".join(partes)

    @classmethod
    def resumen_perfil(
        cls,
        categoria: Optional[str] = None,
        presupuesto: Optional[float] = None,
        marca: Optional[str] = None,
        ciudad: Optional[str] = None,
    ) -> Optional[str]:
        """Construye línea de perfil para incluir en el resumen."""
        partes = []
        if categoria:
            partes.append(f"busca: {categoria}")
        if presupuesto:
            partes.append(f"presupuesto: Bs {presupuesto:.0f}")
        if marca:
            partes.append(f"marca: {marca}")
        if ciudad:
            partes.append(f"ciudad: {ciudad}")
        return " | ".join(partes) if partes else None
