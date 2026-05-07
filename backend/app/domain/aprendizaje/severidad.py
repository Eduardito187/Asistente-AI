from __future__ import annotations

from enum import Enum


class Severidad(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
