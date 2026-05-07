# Skills custom del agente Dismi

Esta carpeta contiene **skills** que extienden el comportamiento del agente
sin tocar el código core. El sistema los descubre automáticamente al
startup vía `SkillRegistry`.

## Cómo agregar un skill nuevo

1. Crear un archivo `skill_<nombre>.py` en esta carpeta.
2. Heredar de `BaseSkill` e implementar:
   - `nombre`: identificador único (snake_case).
   - `aplica(ctx) -> bool`: ¿se activa para este turno?
   - **Al menos uno de**:
     - `bloque_contexto(ctx) -> str | None`: texto que se inyecta al system
       prompt del LLM antes de procesar el turno.
     - `short_circuit_respuesta(ctx) -> str | None`: respuesta directa que
       corta el flujo y NO llama al LLM (útil para reglas estrictas).
3. Recompilar el backend:
   ```bash
   docker compose up -d --build backend
   ```
4. Verificar en logs: al startup el registry imprime los skills cargados.

## Plantilla mínima

```python
from app.application.services.skills import BaseSkill, ContextoSkill


class SkillEjemplo(BaseSkill):
    nombre = "ejemplo"
    prioridad = 0  # mayor = se evalúa primero

    def aplica(self, ctx: ContextoSkill) -> bool:
        return "palabra clave" in ctx.mensaje.lower()

    def bloque_contexto(self, ctx: ContextoSkill) -> str | None:
        return (
            "INSTRUCCION ESTE TURNO: hace X cosa especial porque el "
            "cliente mencionó la palabra clave."
        )
```

## Estructura de `ContextoSkill`

```python
ContextoSkill(
    mensaje: str,                            # mensaje actual del cliente
    sesion_id: UUID,                         # ID de sesión
    perfil: ResultadoObtenerPerfilSesion,    # perfil persistido (categoría, marca, etc.)
    historial_user: list[str],               # mensajes user previos cronológico
    ahora: datetime,                          # momento del turno (UTC)
)
```

## Reglas y convenciones

- **Idempotencia**: `aplica()` debe ser determinístico — mismas entradas,
  misma salida. No leer estado externo.
- **Performance**: `aplica()` se llama UNA vez por turno por skill.
  Evitar llamadas a BD ahí (usá `ctx.perfil` que ya viene leído).
- **Errores**: si tu skill tira excepción, el registry lo loguea y lo
  ignora ese turno. NO rompe el sistema. Pero igualmente, no metas
  lógica frágil — es código que va a producción.
- **Prioridad**: si dos skills devuelven `short_circuit_respuesta`, gana
  el de mayor `prioridad`. Para skills que solo agregan contexto, todos
  se inyectan (orden ≠ exclusión).
- **Naming**: archivos `skill_<algo>.py`, clases `Skill<Algo>` (CamelCase).
  Múltiples skills por archivo está OK pero no es lo ideal.

## Tipos de skills útiles (ideas)

| Tipo | Uso típico | Implementar |
|---|---|---|
| **Promoción temporal** | "Black Friday", "Día del padre" | `bloque_contexto` |
| **Cliente VIP** | Tono diferente para clientes top | `bloque_contexto` |
| **Categoría restringida** | Bloquear ciertos productos | `short_circuit_respuesta` |
| **Mensaje legal** | Disclaimer obligatorio | `bloque_contexto` |
| **Easter egg** | Respuesta divertida ante palabra-clave | `short_circuit_respuesta` |
| **Modo verano/invierno** | Recomendaciones por estación | `bloque_contexto` |
| **Branding regional** | Saludos/jerga por ciudad | `bloque_contexto` |

## Ejemplos en este repo

- `skill_regalo_navidad.py` — promoción navideña (1 noviembre - 7 enero).
- `skill_black_friday.py` — boost de descuentos en BF / CyberMonday.

## Debugging

Al startup, los logs del backend muestran:
```
INFO skill_registry: skills cargados: 2 -> ['regalo_navidad', 'black_friday']
```

Si tu skill no aparece, revisar:
1. ¿El archivo está en `backend/app/skills/`? (no en otra carpeta)
2. ¿La clase hereda de `BaseSkill` directa o transitiva?
3. ¿El import en el archivo funciona? (errores se loguean a WARNING)
4. ¿`aplica()` está implementado? (es `@abstractmethod`)
