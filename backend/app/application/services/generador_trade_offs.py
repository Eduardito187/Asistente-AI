from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TradeOff:
    gana: list[str]
    pierde: list[str]
    resumen: str


class GeneradorTradeOffs:
    """SRP: para cada producto principal recomendado, listar QUE GANA vs
    los demas candidatos y QUE PIERDE.

    Esto convierte 'estas son tus opciones' (LLM aburrido) en
    'esta gana en GPU/RAM pero pierde en precio' (asesor real)."""

    @classmethod
    def comparar(cls, principal, alternativas: list) -> TradeOff:
        gana: list[str] = []
        pierde: list[str] = []
        if not alternativas:
            return TradeOff(gana=[], pierde=[], resumen="opcion unica disponible")

        precio_p = float(principal.precio.monto)
        ram_p = getattr(principal, "ram_gb", None) or 0
        ssd_p = getattr(principal, "capacidad_gb", None) or 0
        gpu_p = getattr(principal, "gpu", None)

        max_precio_alt = max(float(a.precio.monto) for a in alternativas)
        min_precio_alt = min(float(a.precio.monto) for a in alternativas)
        max_ram_alt = max((getattr(a, "ram_gb", None) or 0) for a in alternativas)
        max_ssd_alt = max((getattr(a, "capacidad_gb", None) or 0) for a in alternativas)
        alguien_con_gpu = any(getattr(a, "gpu", None) for a in alternativas)

        if precio_p < min_precio_alt:
            gana.append(f"mas barato (Bs {int(min_precio_alt - precio_p)} menos)")
        elif precio_p > max_precio_alt:
            pierde.append(f"mas caro (Bs {int(precio_p - max_precio_alt)} mas)")

        if ram_p > max_ram_alt:
            gana.append(f"mas RAM (+{ram_p - max_ram_alt}GB)")
        elif ram_p < max_ram_alt:
            pierde.append(f"menos RAM (-{max_ram_alt - ram_p}GB vs alternativa)")

        if ssd_p > max_ssd_alt:
            gana.append(f"mas almacenamiento (+{ssd_p - max_ssd_alt}GB)")
        elif ssd_p < max_ssd_alt:
            pierde.append(f"menos almacenamiento (-{max_ssd_alt - ssd_p}GB)")

        if gpu_p and not alguien_con_gpu:
            gana.append("unica con GPU dedicada confirmada")
        elif not gpu_p and alguien_con_gpu:
            pierde.append("sin GPU dedicada confirmada")

        if gana and pierde:
            resumen = f"gana en {gana[0]}; pierde en {pierde[0]}"
        elif gana:
            resumen = f"gana en {gana[0]}"
        elif pierde:
            resumen = f"pierde en {pierde[0]}"
        else:
            resumen = "trade-off neutro vs alternativas"

        return TradeOff(gana=gana, pierde=pierde, resumen=resumen)
