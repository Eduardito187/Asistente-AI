from __future__ import annotations

from typing import Optional

from ...domain.shared.normalizacion import NormalizadorTexto
from ..chat.serializers import ProductoSerializer
from ..queries.buscar_productos import BuscarProductosHandler, BuscarProductosQuery
from .resolvedor_categoria_cercana import CategoriaCercana
from .respuesta_follow_up import RespuestaFollowUp


class ResponderConsultaDisponibilidad:
    """SRP: dado un match de ResolvedorCategoriaCercana con `fuente='sinonimo'`,
    busca productos reales en esa categoria/subcategoria y devuelve una
    respuesta confirmatoria. Sirve para convertir 'hay motos?' en una lista
    concreta de motocicletas en stock sin pasar por el LLM."""

    LIMITE = 4
    POOL = 20

    def __init__(self, buscar: BuscarProductosHandler) -> None:
        self._buscar = buscar

    LONGITUD_MIN_SINGULARIZAR = 6

    @classmethod
    def _singularizar(cls, palabra: str) -> str:
        """'freidoras' -> 'freidora' para que el FULLTEXT con prefijo
        (+freidora*) tambien matchee el singular en el catalogo."""
        p = palabra.strip()
        for sufijo in ("es", "s"):
            if len(p) > cls.LONGITUD_MIN_SINGULARIZAR and p.endswith(sufijo):
                return p[: -len(sufijo)]
        return p

    TOKENS_CABECERA = 2

    @classmethod
    def _priorizar_nombre_empieza_con(cls, productos: list, palabra_clave: Optional[str]):
        """Reordena: productos cuyo nombre_norm tiene la raiz de la palabra
        dentro de los primeros TOKENS_CABECERA tokens van primero. Asi
        'Telefono celular honor' gana a 'Estuche impermeable para celular'
        cuando el cliente pregunta 'hay celulares?'."""
        if not productos or not palabra_clave:
            return productos
        raiz = cls._singularizar(NormalizadorTexto.normalizar(palabra_clave))
        if not raiz:
            return productos
        matches = [p for p in productos if cls._raiz_en_cabecera(p.nombre, raiz)]
        resto = [p for p in productos if p not in matches]
        return matches + resto

    @classmethod
    def _raiz_en_cabecera(cls, nombre: str, raiz: str) -> bool:
        tokens = NormalizadorTexto.normalizar(nombre).split()
        return any(t.startswith(raiz) for t in tokens[: cls.TOKENS_CABECERA])

    def _seleccionar_productos(
        self, cercana: CategoriaCercana, genero: Optional[str] = None
    ) -> tuple[list, bool]:
        """Pool amplio filtrado por keyword+categoria, re-ranked por cabecera:
        asi 'Telefono celular honor' gana a 'Estuche para celular'. Si el
        pool esta vacio, caemos a categoria pura. Si `genero` se pide pero no
        hay productos marcados en esa subcategoria, re-intenta sin el filtro
        y devuelve (productos, True) para que el caller avise honestidad."""
        if cercana.sku_especifico:
            exacto = self._obtener_y_complementar(cercana, genero)
            if exacto:
                return (exacto, False)
        pool = self._buscar_por_keyword_y_categoria(cercana, genero)
        sin_metadata_genero = bool(genero) and not pool
        if sin_metadata_genero:
            pool = self._buscar_por_keyword_y_categoria(cercana, None)
        if pool:
            return (
                self._priorizar_nombre_empieza_con(pool, cercana.palabra_clave)[: self.LIMITE],
                sin_metadata_genero,
            )
        return (
            self._buscar.ejecutar(
                BuscarProductosQuery(
                    categoria=cercana.categoria,
                    subcategoria=cercana.subcategoria,
                    limite=self.LIMITE,
                )
            ),
            sin_metadata_genero,
        )

    _RATIO_PISO_PREMIUM = 0.5

    def _obtener_y_complementar(
        self, cercana: CategoriaCercana, genero: Optional[str]
    ) -> list:
        """Si el sinónimo apunta a un SKU concreto (ej. 's26 ultra' →
        SM-S948BZKKBVO), traemos ese producto primero y agregamos 1-2
        alternativas de misma subcategoría/gama. No mezclamos con low-end."""
        from ...domain.productos import SKU
        try:
            foco_sku = SKU(cercana.sku_especifico)
        except Exception:
            return []
        with self._buscar._uow_factory() as uow:  # noqa: SLF001
            foco = uow.productos.obtener_por_sku(foco_sku)
        if foco is None:
            return []
        complementos = self._buscar.ejecutar(
            BuscarProductosQuery(
                categoria=cercana.categoria,
                subcategoria=cercana.subcategoria,
                marca=foco.marca,
                genero=genero,
                precio_min=foco.precio.monto * self._RATIO_PISO_PREMIUM,
                excluir_skus=(str(foco.sku),),
                excluir_accesorios=True,
                limite=self.LIMITE - 1,
            )
        )
        return [foco, *complementos[: self.LIMITE - 1]]

    def _buscar_por_keyword_y_categoria(
        self, cercana: CategoriaCercana, genero: Optional[str] = None
    ):
        """Primer intento: usar la palabra clave del sinonimo como query para
        que el FULLTEXT priorice productos cuyo nombre realmente coincide
        (evita devolver utensilios cuando preguntan por freidoras). Trae un
        pool amplio para que el re-ranker por cabecera pueda elegir mejor."""
        if not cercana.palabra_clave:
            return []
        return self._buscar.ejecutar(
            BuscarProductosQuery(
                query=self._singularizar(cercana.palabra_clave),
                categoria=cercana.categoria,
                subcategoria=cercana.subcategoria,
                limite=self.POOL,
                genero=genero,
            )
        )

    def responder(
        self,
        cercana: CategoriaCercana,
        etiqueta_foco: Optional[str] = None,
        genero: Optional[str] = None,
    ) -> RespuestaFollowUp | None:
        productos, sin_metadata_genero = self._seleccionar_productos(cercana, genero)
        if not productos:
            return None
        foco = etiqueta_foco or cercana.palabra_clave or cercana.subcategoria or cercana.categoria
        lineas: list[str] = []
        if sin_metadata_genero:
            lineas.append(
                f"En {foco} no diferenciamos por genero '{genero}' — son modelos "
                f"unisex. Igual te muestro los disponibles:"
            )
        lineas.append(f"Si, tenemos {foco}. Estas son algunas opciones disponibles:")
        for p in productos:
            extra = (
                f" (antes Bs {p.precio_anterior.monto:.0f})"
                if p.precio_anterior and p.precio_anterior.monto > p.precio.monto
                else ""
            )
            lineas.append(
                f"- {p.nombre} — Bs {p.precio.monto:.0f}{extra} [{p.sku}]"
            )
        lineas.append("¿Queres detalles de alguna o prefieres otro modelo?")
        return RespuestaFollowUp(
            texto="\n".join(lineas),
            productos=[ProductoSerializer.resumen(p) for p in productos],
            skus=[str(p.sku) for p in productos],
            ruta="consulta_disponibilidad",
        )
