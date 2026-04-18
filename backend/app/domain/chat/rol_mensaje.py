from __future__ import annotations

from enum import Enum


class RolMensaje(str, Enum):
    """Rol del emisor de un Mensaje en la conversación."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"
