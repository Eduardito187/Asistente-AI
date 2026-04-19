from __future__ import annotations

from uuid import UUID

from .....domain.feedback_ordenes import FeedbackOrden


class FeedbackOrdenMapper:
    """Materializa un FeedbackOrden desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> FeedbackOrden:
        return FeedbackOrden(
            id=int(r["id"]),
            orden_id=UUID(r["orden_id"]),
            sesion_id=UUID(r["sesion_id"]),
            rating=int(r["rating"]) if r.get("rating") is not None else None,
            comentario=r.get("comentario"),
            created_at=r["created_at"],
        )
