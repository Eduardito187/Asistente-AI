from __future__ import annotations

import re
from dataclasses import dataclass


_EXCLUIR_LOW_END: tuple[str, ...] = ("celeron", "pentium", "chromebook", "emmc")


@dataclass(frozen=True)
class EspecificacionesUso:
    ram_gb_min: int | None = None
    ssd_gb_min: int | None = None
    gpu_recomendada: bool = False
    gpu_requerida: bool = False
    excluir_nombres: tuple[str, ...] = ()
    nivel: str = "intermedio"


_MAPA_USO: list[tuple[re.Pattern, EspecificacionesUso]] = [
    (
        re.compile(
            r"\b(?:ingenier[íi]a|ingeniero|autocad|civil[\s_]?3d|solidworks|revit|"
            r"archicad|catia|ansys|comsol|abaqus|planos?|modelado[\s_]?3d|"
            r"dise[ñn]o[\s_](?:estructural|civil|mec[áa]nico|industrial))\b",
            re.IGNORECASE,
        ),
        EspecificacionesUso(
            ram_gb_min=16, ssd_gb_min=512,
            gpu_recomendada=True,
            excluir_nombres=_EXCLUIR_LOW_END,
            nivel="profesional",
        ),
    ),
    (
        re.compile(
            r"\b(?:render(?:izado)?|blender|cinema[\s_]?4d|3ds[\s_]?max|maya|"
            r"unreal[\s_]?engine|unity[\s_]?3d|keyshot|v[\s-]?ray|lumion|twinmotion)\b",
            re.IGNORECASE,
        ),
        EspecificacionesUso(
            ram_gb_min=16, ssd_gb_min=512,
            gpu_recomendada=True, gpu_requerida=True,
            excluir_nombres=_EXCLUIR_LOW_END,
            nivel="profesional",
        ),
    ),
    (
        re.compile(
            r"\b(?:dise[ñn]o[\s_]gr[áa]fico|photoshop|illustrator|premiere|"
            r"davinci[\s_]?resolve|after[\s_]?effects|indesign|figma|"
            r"edici[óo]n[\s_]de[\s_]video|edici[óo]n[\s_]fotogr[áa]fica|"
            r"lightroom|capture[\s_]?one)\b",
            re.IGNORECASE,
        ),
        EspecificacionesUso(
            ram_gb_min=16, ssd_gb_min=512,
            gpu_recomendada=True,
            excluir_nombres=_EXCLUIR_LOW_END,
            nivel="alto",
        ),
    ),
    (
        re.compile(
            r"\b(?:docker|kubernetes|m[áa]quinas?[\s_]virtuales?|virtualbox|vmware|"
            r"machine[\s_]?learning|inteligencia[\s_]?artificial|deep[\s_]?learning|"
            r"modelos?[\s_](?:ia|ai|llm|ml)|compilaci[óo]n|backend[\s_]?pesado)\b",
            re.IGNORECASE,
        ),
        EspecificacionesUso(
            ram_gb_min=16, ssd_gb_min=512,
            excluir_nombres=_EXCLUIR_LOW_END,
            nivel="alto",
        ),
    ),
    (
        re.compile(
            r"\b(?:arquitectura|sketchup|sketch[\s_]?up|enscape|rhinoceros|rhino|"
            r"dise[ñn]o[\s_]arquitect[óo]nico|bim|revit)\b",
            re.IGNORECASE,
        ),
        EspecificacionesUso(
            ram_gb_min=16, ssd_gb_min=512,
            gpu_recomendada=True,
            excluir_nombres=_EXCLUIR_LOW_END,
            nivel="profesional",
        ),
    ),
]

_NIVEL_ORDEN = {"basico": 0, "intermedio": 1, "alto": 2, "profesional": 3}


class DetectorUsoTecnico:
    """Mapea usos y software profesional a especificaciones mínimas.

    Cuando el cliente menciona 'ingeniería civil', 'AutoCAD', 'render', etc.,
    este detector eleva los requisitos mínimos y activa exclusiones de gama baja
    sin que el usuario los enumere explícitamente."""

    @classmethod
    def detectar(cls, mensaje: str) -> EspecificacionesUso | None:
        """Retorna el spec más alto encontrado en el mensaje, fusionando si hay varios."""
        mejor: EspecificacionesUso | None = None
        for patron, specs in _MAPA_USO:
            if not patron.search(mensaje):
                continue
            if mejor is None:
                mejor = specs
                continue
            nivel_nuevo = _NIVEL_ORDEN.get(specs.nivel, 1)
            nivel_mejor = _NIVEL_ORDEN.get(mejor.nivel, 1)
            mejor = EspecificacionesUso(
                ram_gb_min=max(
                    filter(None, [mejor.ram_gb_min, specs.ram_gb_min]),
                    default=None,
                ),
                ssd_gb_min=max(
                    filter(None, [mejor.ssd_gb_min, specs.ssd_gb_min]),
                    default=None,
                ),
                gpu_recomendada=mejor.gpu_recomendada or specs.gpu_recomendada,
                gpu_requerida=mejor.gpu_requerida or specs.gpu_requerida,
                excluir_nombres=tuple({*mejor.excluir_nombres, *specs.excluir_nombres}),
                nivel=mejor.nivel if nivel_mejor >= nivel_nuevo else specs.nivel,
            )
        return mejor
