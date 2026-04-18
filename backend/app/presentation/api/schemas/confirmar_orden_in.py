from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


class ConfirmarOrdenIn(BaseModel):
    cliente_nombre: str
    cliente_email: Optional[EmailStr] = None
    cliente_telefono: Optional[str] = None
    notas: Optional[str] = None
