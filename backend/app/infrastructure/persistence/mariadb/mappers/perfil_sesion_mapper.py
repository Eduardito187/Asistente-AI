from __future__ import annotations

from uuid import UUID

from .....domain.perfiles_sesion import PerfilSesion


class PerfilSesionMapper:
    """Materializa un PerfilSesion desde un row crudo de MariaDB."""

    @staticmethod
    def from_row(r: dict) -> PerfilSesion:
        pmax = r.get("presupuesto_max")
        pulg = r.get("pulgadas")
        pmin_mostrado = r.get("precio_min_mostrado")
        pmax_mostrado = r.get("precio_max_mostrado")
        ram = r.get("ram_gb_min")
        gpu = r.get("gpu_dedicada")
        return PerfilSesion(
            sesion_id=UUID(r["sesion_id"]),
            presupuesto_max=float(pmax) if pmax is not None else None,
            marca_preferida=r.get("marca_preferida"),
            categoria_foco=r.get("categoria_foco"),
            uso_declarado=r.get("uso_declarado"),
            pulgadas=float(pulg) if pulg is not None else None,
            tipo_panel=r.get("tipo_panel"),
            resolucion=r.get("resolucion"),
            updated_at=r["updated_at"],
            ultimos_skus_mostrados=r.get("ultimos_skus_mostrados"),
            precio_min_mostrado=float(pmin_mostrado) if pmin_mostrado is not None else None,
            precio_max_mostrado=float(pmax_mostrado) if pmax_mostrado is not None else None,
            alternativa_ofrecida=r.get("alternativa_ofrecida"),
            subcategoria_foco=r.get("subcategoria_foco"),
            genero_declarado=r.get("genero_declarado"),
            sku_foco=r.get("sku_foco"),
            desired_tier=r.get("desired_tier"),
            ram_gb_min=int(ram) if ram is not None else None,
            gpu_dedicada=bool(gpu) if gpu is not None else None,
        )
