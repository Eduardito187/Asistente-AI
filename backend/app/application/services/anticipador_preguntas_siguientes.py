from __future__ import annotations


class AnticipadorPreguntasSiguientes:
    """SRP: sugerir 2-3 preguntas que el cliente probablemente quiere hacer
    despues de ver los productos. Reduce friccion y demuestra anticipacion.

    Decide segun lo que YA esta en el perfil:
      - si no hay presupuesto -> '¿Que presupuesto manejas?'
      - si no hay uso        -> '¿Para que la usaras principalmente?'
      - si ya hay todo       -> preguntas de profundizacion (envio, garantia, accesorios)"""

    @classmethod
    def sugerir(cls, perfil) -> list[str]:
        sugerencias: list[str] = []
        cat = (getattr(perfil, "categoria_foco", None) or "").lower()

        if not getattr(perfil, "uso_declarado", None):
            sugerencias.append("¿Para que la vas a usar (estudio, trabajo, gaming, hogar)?")
        if not (getattr(perfil, "presupuesto_max", None) or getattr(perfil, "presupuesto_ideal", None)):
            sugerencias.append("¿Cual es tu presupuesto aproximado?")
        if not getattr(perfil, "marca_preferida", None):
            sugerencias.append("¿Tienes marca preferida o te da igual?")

        if not sugerencias:
            if "laptop" in cat or "computador" in cat:
                sugerencias.extend([
                    "¿Quieres comparar 2 modelos lado a lado?",
                    "¿Te interesa saber cual te durara mas anios para tu uso?",
                    "¿Quieres ver accesorios (mouse, mochila, cooler)?",
                ])
            elif "tv" in cat or "televisor" in cat:
                sugerencias.extend([
                    "¿Es para una sala grande, mediana o cuarto?",
                    "¿La quieres con apps de streaming integradas?",
                    "¿Te interesa que tenga 120Hz para PS5/Xbox?",
                ])
            elif "celular" in cat or "smartphone" in cat:
                sugerencias.extend([
                    "¿Priorizas camara, bateria o rendimiento?",
                    "¿Quieres que tenga 5G?",
                    "¿Cuanta bateria necesitas en mAh?",
                ])
            else:
                sugerencias.extend([
                    "¿Quieres comparar 2 opciones lado a lado?",
                    "¿Te interesa el envio express o tienda fisica?",
                ])

        return sugerencias[:3]
