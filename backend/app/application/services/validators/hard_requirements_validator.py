from __future__ import annotations

from .category_consistency_validator import ResultadoValidacion
from ....domain.aprendizaje import ReasonCode


class HardRequirementsValidator:
    """SRP: verifica que productos citados respeten ram_min, ssd_min,
    gpu_dedicada y exclusiones del perfil. Si alguno los viola, FALLA
    con HARD_FILTER_IGNORED."""

    @classmethod
    def validar(cls, perfil_estado: dict, productos: list[dict]) -> ResultadoValidacion:
        if not productos:
            return ResultadoValidacion(True, ReasonCode.OK, "sin productos")
        ram_min = perfil_estado.get("ram_gb_min")
        ssd_min = perfil_estado.get("ssd_gb_min")
        gpu_req = perfil_estado.get("gpu_dedicada")
        exc = (perfil_estado.get("nombre_excluye_acum") or "").lower()
        excluidos = [t.strip() for t in exc.split(",") if t.strip()]
        for p in productos:
            nombre = (p.get("nombre") or "").lower()
            ram = p.get("ram_gb") or 0
            ssd = p.get("capacidad_gb") or 0
            gpu = p.get("gpu")
            if ram_min and ram < ram_min:
                return ResultadoValidacion(
                    False, ReasonCode.HARD_FILTER_IGNORED,
                    f"ram {ram}<{ram_min} sku={p.get('sku')}",
                )
            if ssd_min and ssd < ssd_min:
                return ResultadoValidacion(
                    False, ReasonCode.HARD_FILTER_IGNORED,
                    f"ssd {ssd}<{ssd_min} sku={p.get('sku')}",
                )
            if gpu_req and not gpu:
                return ResultadoValidacion(
                    False, ReasonCode.HARD_FILTER_IGNORED,
                    f"gpu_dedicada exigida pero no confirmada sku={p.get('sku')}",
                )
            for kw in excluidos:
                if kw and kw in nombre:
                    return ResultadoValidacion(
                        False, ReasonCode.HARD_FILTER_IGNORED,
                        f"contiene exclusion '{kw}' sku={p.get('sku')}",
                    )
        return ResultadoValidacion(True, ReasonCode.OK, "requisitos respetados")
