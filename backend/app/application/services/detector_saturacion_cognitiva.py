from __future__ import annotations


class DetectorSaturacionCognitiva:
    """Detecta cuando el cliente lleva demasiados productos vistos sin tomar
    una decisión: paradoja de la elección.

    Tres niveles escalados:
    - MEDIO  (≥ 6 SKUs vistos sin items en carrito) — bloque de contexto al
      LLM que le pide recomendar UNO o hacer pregunta para reducir.
    - ALTO   (≥ 10 SKUs sin items) — bloque más enfático: prohibe abrir
      búsqueda nueva, fuerza recomendación entre los ya vistos.
    - CRITICO (≥ 15 SKUs sin items) — short-circuit que ofrece atajo a
      contacto humano para que un asesor termine de cerrar.

    Lee del PerfilSesion (que ya almacena ultimos_skus_mostrados acumulados)
    y del estado del carrito — no necesita schema nuevo."""

    _UMBRAL_MEDIO = 6
    _UMBRAL_ALTO = 10
    _UMBRAL_CRITICO = 15

    NIVEL_NINGUNO = "ninguno"
    NIVEL_MEDIO = "medio"
    NIVEL_ALTO = "alto"
    NIVEL_CRITICO = "critico"

    @classmethod
    def nivel(cls, skus_acumulados: int, items_carrito: int) -> str:
        """Devuelve nivel de saturación. Si hay items en carrito, no hay
        saturación (el cliente ya decidió algo)."""
        if items_carrito > 0:
            return cls.NIVEL_NINGUNO
        if skus_acumulados >= cls._UMBRAL_CRITICO:
            return cls.NIVEL_CRITICO
        if skus_acumulados >= cls._UMBRAL_ALTO:
            return cls.NIVEL_ALTO
        if skus_acumulados >= cls._UMBRAL_MEDIO:
            return cls.NIVEL_MEDIO
        return cls.NIVEL_NINGUNO

    @classmethod
    def esta_saturado(cls, skus_acumulados: int, items_carrito: int) -> bool:
        """True si el cliente vio muchos productos y aún no decidió nada.
        Equivalente a nivel != 'ninguno'."""
        return cls.nivel(skus_acumulados, items_carrito) != cls.NIVEL_NINGUNO

    @classmethod
    def es_critico(cls, skus_acumulados: int, items_carrito: int) -> bool:
        """True si el nivel cruzó el umbral crítico (derivar a humano)."""
        return cls.nivel(skus_acumulados, items_carrito) == cls.NIVEL_CRITICO

    @classmethod
    def umbral(cls) -> int:
        return cls._UMBRAL_MEDIO

    @classmethod
    def umbrales(cls) -> tuple[int, int, int]:
        """Devuelve (medio, alto, critico) para mostrar en el bloque al LLM."""
        return cls._UMBRAL_MEDIO, cls._UMBRAL_ALTO, cls._UMBRAL_CRITICO

    @classmethod
    def contar_skus_acumulados(cls, skus_str: str | None) -> int:
        """Helper: cuenta SKUs distintos en el campo ultimos_skus_mostrados
        del perfil (formato comma-separated)."""
        if not skus_str:
            return 0
        skus = [s.strip() for s in skus_str.split(",") if s.strip()]
        return len(set(skus))
