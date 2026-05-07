from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from .asignador_variante_ab import AsignadorVarianteAB
from .horario_atencion import HorarioAtencion


class ResponderDerivarVentas:
    """Genera la respuesta de derivación a ventas telefónicas.

    Tres dimensiones que adaptan el mensaje:
    - Variante A/B (testeo): texto empático tradicional vs texto directo
      orientado a acción. Se asigna determinísticamente por sesion_id.
    - Horario: si está fuera de horario, mencionamos cuándo responde el
      equipo y qué pasa si escribe ahora.
    - Motivo de derivación: 'frustracion' (cliente molesto) vs
      'saturacion' (cliente saturado de opciones) vs 'fuera_horario_compra'.
      Cambia el tono pero no los datos de contacto.

    SRP: solo construir el texto. La decisión de cuándo usarlo vive en
    ProcesarChatService."""

    _TELEFONO = "800 10 2000"
    _WHATSAPP_NUMERO = "75010500"
    _WHATSAPP_LINK = "https://wa.me/59175010500"

    # Variantes A/B para el mensaje de derivación por frustración.
    _VARIANTES_FRUSTRACION = ("empatica", "directa")

    # ===== API publica ======================================================

    @classmethod
    def responder(
        cls,
        motivo: str = "frustracion",
        sesion_id: Optional[UUID] = None,
        ahora: Optional[datetime] = None,
    ) -> str:
        """Genera el mensaje. `motivo` selecciona el tono base; `sesion_id`
        determina la variante A/B; `ahora` se usa para detectar si estamos
        en horario laboral (default: ahora UTC)."""
        en_horario = HorarioAtencion.dentro_horario(ahora)
        variante = cls._elegir_variante(motivo, sesion_id)
        cuerpo = cls._cuerpo_segun_motivo(motivo, variante)
        contacto = cls._bloque_contacto(en_horario, ahora)
        return f"{cuerpo}\n\n{contacto}"

    @classmethod
    def variante_asignada(cls, sesion_id: Optional[UUID]) -> str:
        """Devuelve qué variante A/B le toca a esta sesion (para métricas)."""
        if sesion_id is None:
            return cls._VARIANTES_FRUSTRACION[0]
        return AsignadorVarianteAB.variante(sesion_id, cls._VARIANTES_FRUSTRACION)

    @classmethod
    def telefono(cls) -> str:
        return cls._TELEFONO

    @classmethod
    def whatsapp_numero(cls) -> str:
        return cls._WHATSAPP_NUMERO

    @classmethod
    def whatsapp_link(cls) -> str:
        return cls._WHATSAPP_LINK

    # ===== Internos =========================================================

    @classmethod
    def _elegir_variante(cls, motivo: str, sesion_id: Optional[UUID]) -> str:
        if motivo != "frustracion" or sesion_id is None:
            return cls._VARIANTES_FRUSTRACION[0]
        return AsignadorVarianteAB.variante(sesion_id, cls._VARIANTES_FRUSTRACION)

    @classmethod
    def _cuerpo_segun_motivo(cls, motivo: str, variante: str) -> str:
        if motivo == "saturacion":
            return (
                "Veo que llevás varios productos vistos sin terminar de "
                "decidirte — tener un asesor humano que te haga 2 preguntas "
                "y te recomiende UNO concreto te puede destrabar. "
                "Te paso los contactos:"
            )
        if motivo == "fuera_horario_compra":
            return (
                "Para cerrar tu compra puedo conectarte con el equipo de "
                "ventas. Si querés trato directo:"
            )
        # motivo == "frustracion" — usa variante A/B
        if variante == "directa":
            return (
                "Mejor te paso con un asesor humano que te puede atender "
                "ahora mismo:"
            )
        return (
            "Te entiendo, y disculpá si no logré ayudarte por aquí. "
            "Te paso directo con nuestro equipo de ventas — ellos te van "
            "a atender mejor:"
        )

    @classmethod
    def _bloque_contacto(cls, en_horario: bool, ahora: Optional[datetime]) -> str:
        contacto = (
            f"Teléfono: {cls._TELEFONO}\n"
            f"WhatsApp: {cls._WHATSAPP_NUMERO} ({cls._WHATSAPP_LINK})"
        )
        if en_horario:
            return contacto + "\n\nGracias por la paciencia."
        cuando = HorarioAtencion.proxima_apertura(ahora)
        return (
            f"{contacto}\n\n"
            f"Estamos fuera de horario ({HorarioAtencion.descripcion_horario()}). "
            f"Si escribís al WhatsApp ahora te responden {cuando}. "
            "Gracias por la paciencia."
        )
