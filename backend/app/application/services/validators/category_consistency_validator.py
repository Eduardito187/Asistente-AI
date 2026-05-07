from __future__ import annotations

from dataclasses import dataclass

from ....domain.aprendizaje import ReasonCode


@dataclass(frozen=True)
class ResultadoValidacion:
    paso: bool
    reason_code: ReasonCode
    detalle: str


class CategoryConsistencyValidator:
    """SRP: verifica que los productos citados pertenezcan a la categoria
    bloqueada en el perfil. Si el perfil dice categoria_foco='Laptops' y
    los productos citados son celulares, FALLA con CATEGORY_MISMATCH."""

    @classmethod
    def validar(cls, perfil_estado: dict, productos: list[dict]) -> ResultadoValidacion:
        cat_lock = (perfil_estado.get("categoria_foco") or "").strip().lower()
        if not cat_lock or not productos:
            return ResultadoValidacion(True, ReasonCode.OK, "no aplica")
        for prod in productos:
            cat_p = (prod.get("categoria") or "").strip().lower()
            if cat_p and cat_lock not in cat_p and cat_p not in cat_lock:
                return ResultadoValidacion(
                    False, ReasonCode.CATEGORY_MISMATCH,
                    f"perfil={cat_lock} producto={cat_p} sku={prod.get('sku')}",
                )
        return ResultadoValidacion(True, ReasonCode.OK, "categorias coherentes")
