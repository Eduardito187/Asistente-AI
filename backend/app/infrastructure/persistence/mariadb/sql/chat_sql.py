from __future__ import annotations


class ChatSql:
    """Catalogo SQL del agregado Chat (mensajes)."""

    GUARDAR_MENSAJE = (
        "INSERT INTO mensajes (sesion_id, rol, contenido) VALUES (:s, :r, :c)"
    )

    HISTORIAL = (
        "SELECT rol, contenido, created_at FROM mensajes "
        "WHERE sesion_id = :s ORDER BY created_at DESC LIMIT :n"
    )
