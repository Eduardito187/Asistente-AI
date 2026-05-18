from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


@dataclass
class PerfilSesion:
    """Agregado PerfilSesion: preferencias declaradas por el cliente durante
    el chat. Usado para pre-filtrar busquedas y evitar preguntar lo mismo
    en cada turno."""

    sesion_id: UUID
    presupuesto_max: Optional[float]
    marca_preferida: Optional[str]
    categoria_foco: Optional[str]
    uso_declarado: Optional[str]
    pulgadas: Optional[float]
    tipo_panel: Optional[str]
    resolucion: Optional[str]
    updated_at: datetime
    ultimos_skus_mostrados: Optional[str] = None
    precio_min_mostrado: Optional[float] = None
    precio_max_mostrado: Optional[float] = None
    alternativa_ofrecida: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    genero_declarado: Optional[str] = None
    sku_foco: Optional[str] = None
    desired_tier: Optional[str] = None
    ram_gb_min: Optional[int] = None
    gpu_dedicada: Optional[bool] = None
    ssd_gb_min: Optional[int] = None
    capacidad_litros_min: Optional[float] = None
    nombre_excluye_acum: Optional[str] = None  # comma-separated acumulado
    presupuesto_ideal: Optional[float] = None  # techo blando: prefiere no exceder
    presupuesto_min_buscado: Optional[float] = None  # precio más bajo que el cliente ha considerado
    # --- Atributos técnicos sticky (Fase 1) ---
    # Booleanos: guardar True/NULL, nunca False. Un cliente que pidió "con NFC"
    # en turno 2 debe seguir filtrando NFC en turno 5.
    refresh_hz_min: Optional[int] = None
    bateria_mah_min: Optional[int] = None
    camara_mp_min: Optional[int] = None
    soporta_5g: Optional[bool] = None
    sistema_operativo: Optional[str] = None
    capacidad_kg_min: Optional[float] = None
    potencia_w_min: Optional[int] = None
    inverter: Optional[bool] = None
    no_frost: Optional[bool] = None
    smart_tv: Optional[bool] = None
    bluetooth_incluido: Optional[bool] = None
    nfc: Optional[bool] = None
    usb_c: Optional[bool] = None
    hdmi_2_1: Optional[bool] = None
    # Acumula señales de frustración detectadas en la sesión (suma, no pick).
    frustracion_count: Optional[int] = None
    # Ciudad boliviana mencionada por el cliente (solo contexto, no filtra búsquedas).
    ciudad_sesion: Optional[str] = None
    # Hechos que el cliente pidió recordar: "recuerda que tengo 5000 de presupuesto".
    # Líneas separadas por \n. Se muestran al LLM en cada turno para no olvidarlos.
    notas_usuario: Optional[str] = None

    @staticmethod
    def vacio(sesion_id: UUID) -> "PerfilSesion":
        return PerfilSesion(
            sesion_id=sesion_id,
            presupuesto_max=None,
            marca_preferida=None,
            categoria_foco=None,
            uso_declarado=None,
            pulgadas=None,
            tipo_panel=None,
            resolucion=None,
            updated_at=datetime.now(timezone.utc),
        )

    def esta_vacio(self) -> bool:
        return not any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.subcategoria_foco, self.uso_declarado, self.pulgadas,
                self.tipo_panel, self.resolucion,
            ]
        )

    @staticmethod
    def _pick(nuevo, viejo):
        return nuevo or viejo

    @staticmethod
    def _sumar(nuevo, viejo) -> Optional[int]:
        """Para contadores acumulativos (ej. frustracion_count). NULL+NULL = NULL."""
        if nuevo is None and viejo is None:
            return None
        return (nuevo or 0) + (viejo or 0)

    def fusionar(self, otro: "PerfilSesion") -> "PerfilSesion":
        """Devuelve un nuevo perfil: los campos no nulos de `otro` pisan los de self."""
        p = self._pick
        return PerfilSesion(
            sesion_id=self.sesion_id,
            updated_at=datetime.now(timezone.utc),
            presupuesto_max=p(otro.presupuesto_max, self.presupuesto_max),
            marca_preferida=p(otro.marca_preferida, self.marca_preferida),
            categoria_foco=p(otro.categoria_foco, self.categoria_foco),
            uso_declarado=p(otro.uso_declarado, self.uso_declarado),
            pulgadas=p(otro.pulgadas, self.pulgadas),
            tipo_panel=p(otro.tipo_panel, self.tipo_panel),
            resolucion=p(otro.resolucion, self.resolucion),
            ultimos_skus_mostrados=p(otro.ultimos_skus_mostrados, self.ultimos_skus_mostrados),
            precio_min_mostrado=p(otro.precio_min_mostrado, self.precio_min_mostrado),
            precio_max_mostrado=p(otro.precio_max_mostrado, self.precio_max_mostrado),
            alternativa_ofrecida=p(otro.alternativa_ofrecida, self.alternativa_ofrecida),
            subcategoria_foco=p(otro.subcategoria_foco, self.subcategoria_foco),
            genero_declarado=p(otro.genero_declarado, self.genero_declarado),
            sku_foco=p(otro.sku_foco, self.sku_foco),
            desired_tier=p(otro.desired_tier, self.desired_tier),
            ram_gb_min=p(otro.ram_gb_min, self.ram_gb_min),
            gpu_dedicada=p(otro.gpu_dedicada, self.gpu_dedicada),
            ssd_gb_min=p(otro.ssd_gb_min, self.ssd_gb_min),
            capacidad_litros_min=p(otro.capacidad_litros_min, self.capacidad_litros_min),
            nombre_excluye_acum=p(otro.nombre_excluye_acum, self.nombre_excluye_acum),
            presupuesto_ideal=p(otro.presupuesto_ideal, self.presupuesto_ideal),
            presupuesto_min_buscado=p(otro.presupuesto_min_buscado, self.presupuesto_min_buscado),
            frustracion_count=self._sumar(otro.frustracion_count, self.frustracion_count),
            ciudad_sesion=p(otro.ciudad_sesion, self.ciudad_sesion),
            refresh_hz_min=p(otro.refresh_hz_min, self.refresh_hz_min),
            bateria_mah_min=p(otro.bateria_mah_min, self.bateria_mah_min),
            camara_mp_min=p(otro.camara_mp_min, self.camara_mp_min),
            soporta_5g=p(otro.soporta_5g, self.soporta_5g),
            sistema_operativo=p(otro.sistema_operativo, self.sistema_operativo),
            capacidad_kg_min=p(otro.capacidad_kg_min, self.capacidad_kg_min),
            potencia_w_min=p(otro.potencia_w_min, self.potencia_w_min),
            inverter=p(otro.inverter, self.inverter),
            no_frost=p(otro.no_frost, self.no_frost),
            smart_tv=p(otro.smart_tv, self.smart_tv),
            bluetooth_incluido=p(otro.bluetooth_incluido, self.bluetooth_incluido),
            nfc=p(otro.nfc, self.nfc),
            usb_c=p(otro.usb_c, self.usb_c),
            hdmi_2_1=p(otro.hdmi_2_1, self.hdmi_2_1),
            notas_usuario=self._acumular_notas(otro.notas_usuario, self.notas_usuario),
        )

    @staticmethod
    def _acumular_notas(nueva: Optional[str], vieja: Optional[str]) -> Optional[str]:
        """Las notas se acumulan (append), no se pisan. Máx 2000 chars."""
        if not nueva:
            return vieja
        if not vieja:
            return nueva
        combinado = vieja + "\n" + nueva
        return combinado[-2000:] if len(combinado) > 2000 else combinado
