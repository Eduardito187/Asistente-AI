from __future__ import annotations

from uuid import UUID

from .....domain.perfiles_sesion import PerfilSesion


def _f(v) -> float | None:
    return float(v) if v is not None else None


def _i(v) -> int | None:
    return int(v) if v is not None else None


def _b(v) -> bool | None:
    return bool(v) if v is not None else None


class PerfilSesionMapper:
    """Materializa un PerfilSesion desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> PerfilSesion:
        return PerfilSesion(
            sesion_id=UUID(r["sesion_id"]),
            updated_at=r["updated_at"],
            # Campos de negocio
            presupuesto_max=_f(r.get("presupuesto_max")),
            presupuesto_ideal=_f(r.get("presupuesto_ideal")),
            presupuesto_min_buscado=_f(r.get("presupuesto_min_buscado")),
            marca_preferida=r.get("marca_preferida"),
            categoria_foco=r.get("categoria_foco"),
            subcategoria_foco=r.get("subcategoria_foco"),
            uso_declarado=r.get("uso_declarado"),
            genero_declarado=r.get("genero_declarado"),
            sku_foco=r.get("sku_foco"),
            desired_tier=r.get("desired_tier"),
            alternativa_ofrecida=r.get("alternativa_ofrecida"),
            ciudad_sesion=r.get("ciudad_sesion"),
            nombre_excluye_acum=r.get("nombre_excluye_acum"),
            frustracion_count=_i(r.get("frustracion_count")),
            # Display
            pulgadas=_f(r.get("pulgadas")),
            tipo_panel=r.get("tipo_panel"),
            resolucion=r.get("resolucion"),
            ultimos_skus_mostrados=r.get("ultimos_skus_mostrados"),
            precio_min_mostrado=_f(r.get("precio_min_mostrado")),
            precio_max_mostrado=_f(r.get("precio_max_mostrado")),
            # Atributos técnicos originales
            ram_gb_min=_i(r.get("ram_gb_min")),
            gpu_dedicada=_b(r.get("gpu_dedicada")),
            ssd_gb_min=_i(r.get("ssd_gb_min")),
            capacidad_litros_min=_f(r.get("capacidad_litros_min")),
            notas_usuario=r.get("notas_usuario"),
            # Atributos técnicos sticky (Fase 1)
            refresh_hz_min=_i(r.get("refresh_hz_min")),
            bateria_mah_min=_i(r.get("bateria_mah_min")),
            camara_mp_min=_i(r.get("camara_mp_min")),
            soporta_5g=_b(r.get("soporta_5g")),
            sistema_operativo=r.get("sistema_operativo"),
            capacidad_kg_min=_f(r.get("capacidad_kg_min")),
            potencia_w_min=_i(r.get("potencia_w_min")),
            inverter=_b(r.get("inverter")),
            no_frost=_b(r.get("no_frost")),
            smart_tv=_b(r.get("smart_tv")),
            bluetooth_incluido=_b(r.get("bluetooth_incluido")),
            nfc=_b(r.get("nfc")),
            usb_c=_b(r.get("usb_c")),
            hdmi_2_1=_b(r.get("hdmi_2_1")),
        )
