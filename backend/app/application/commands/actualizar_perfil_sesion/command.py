from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ActualizarPerfilSesionCommand:
    """Comando: fusiona los campos no nulos sobre el perfil existente."""

    sesion_id: UUID
    presupuesto_max: Optional[float] = None
    marca_preferida: Optional[str] = None
    categoria_foco: Optional[str] = None
    subcategoria_foco: Optional[str] = None
    sku_foco: Optional[str] = None
    genero_declarado: Optional[str] = None
    desired_tier: Optional[str] = None
    uso_declarado: Optional[str] = None
    pulgadas: Optional[float] = None
    tipo_panel: Optional[str] = None
    resolucion: Optional[str] = None
    ram_gb_min: Optional[int] = None
    gpu_dedicada: Optional[bool] = None
    ssd_gb_min: Optional[int] = None
    capacidad_litros_min: Optional[float] = None
    nombre_excluye_nuevas: Optional[str] = None  # comma-sep exclusiones de ESTE turno
    presupuesto_ideal: Optional[float] = None
    presupuesto_min_buscado: Optional[float] = None
    # Delta a sumar al contador acumulado de frustración (1 por señal).
    # NULL = sin cambio. El handler hace SUM(viejo, delta).
    frustracion_delta: Optional[int] = None
    ciudad_sesion: Optional[str] = None
    # Hecho que el cliente pidió recordar ("recuerda que tengo 5000 de presupuesto").
    # Se ACUMULA en el perfil (append), nunca pisa los anteriores.
    nota_nueva: Optional[str] = None
    # --- Atributos técnicos sticky (Fase 1) ---
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

    def tiene_datos(self) -> bool:
        return any(
            [
                self.presupuesto_max, self.marca_preferida, self.categoria_foco,
                self.subcategoria_foco, self.sku_foco, self.genero_declarado,
                self.desired_tier, self.uso_declarado, self.pulgadas,
                self.tipo_panel, self.resolucion, self.ram_gb_min, self.gpu_dedicada,
                self.ssd_gb_min, self.capacidad_litros_min, self.nombre_excluye_nuevas,
                self.presupuesto_ideal, self.presupuesto_min_buscado,
                self.frustracion_delta, self.ciudad_sesion, self.nota_nueva,
                self.refresh_hz_min, self.bateria_mah_min, self.camara_mp_min,
                self.soporta_5g, self.sistema_operativo, self.capacidad_kg_min,
                self.potencia_w_min, self.inverter, self.no_frost, self.smart_tv,
                self.bluetooth_incluido, self.nfc, self.usb_c, self.hdmi_2_1,
            ]
        )
