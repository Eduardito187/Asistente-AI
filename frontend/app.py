"""Frontend Streamlit — Asistente de compras Dismac.

- Chat con el asistente.
- Tarjetas de producto clickeables con imagen, precio y botón 'Agregar al carrito'.
- Carrito lateral con subtotales, total y acciones (quitar, vaciar, simular compra).
- Botón 'No me sirve ninguno' para pedir más opciones al asistente.
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

import time

import httpx
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")


class BackendNoDisponibleError(httpx.HTTPError):
    """El backend no respondio (caido o reiniciando)."""

    def __init__(self, message: str):
        super().__init__(message)


def _request_con_reintentos(method: str, path: str, *, timeout: int, **kwargs):
    delays = (0.0, 2.0, 4.0, 6.0)
    ultimo_error: Exception | None = None
    for espera in delays:
        if espera:
            time.sleep(espera)
        try:
            r = httpx.request(method, f"{BACKEND_URL}{path}", timeout=timeout, **kwargs)
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError, httpx.TimeoutException) as exc:
            ultimo_error = exc
            continue
        if 500 <= r.status_code < 600:
            ultimo_error = httpx.HTTPStatusError(
                f"{r.status_code} {r.reason_phrase}", request=r.request, response=r
            )
            continue
        r.raise_for_status()
        return r.json()
    raise BackendNoDisponibleError(
        f"El servidor no respondio tras {len(delays)} intentos ({method} {path}). "
        "Probablemente esta reiniciando. Intenta de nuevo en unos segundos."
    ) from ultimo_error


def api_get(path: str, **kwargs):
    return _request_con_reintentos("GET", path, timeout=30, **kwargs)


def api_post(path: str, **kwargs):
    return _request_con_reintentos("POST", path, timeout=180, **kwargs)


def api_delete(path: str):
    return _request_con_reintentos("DELETE", path, timeout=20)


def imagen_url(producto: dict) -> str:
    url = producto.get("imagen_url")
    if url and url.startswith("http") and "dismac.example" not in url:
        return url
    etiqueta = quote(producto["sku"])
    return f"https://placehold.co/400x260/1f2937/f5f5f5?text={etiqueta}"


def formato_precio(p: dict) -> str:
    if p.get("precio_anterior_bob"):
        return (
            f"**Bs {p['precio_bob']:.0f}**  "
            f"<span style='text-decoration:line-through;color:#888'>"
            f"Bs {p['precio_anterior_bob']:.0f}</span>"
        )
    return f"**Bs {p['precio_bob']:.0f}**"


def agregar_carrito(sku: str, cantidad: int = 1):
    if not st.session_state.sesion_id:
        st.session_state.sesion_id = _crear_sesion_vacia()
    api_post(
        f"/carrito/{st.session_state.sesion_id}/agregar",
        json={"sku": sku, "cantidad": cantidad},
    )


def quitar_carrito(sku: str):
    api_delete(f"/carrito/{st.session_state.sesion_id}/{sku}")


def vaciar_carrito():
    if not st.session_state.sesion_id:
        return
    carrito = api_get(f"/carrito/{st.session_state.sesion_id}")
    for item in carrito["items"]:
        quitar_carrito(item["sku"])


def obtener_carrito() -> dict:
    if not st.session_state.sesion_id:
        return {"items": [], "total_bob": 0.0}
    try:
        return api_get(f"/carrito/{st.session_state.sesion_id}")
    except Exception:
        return {"items": [], "total_bob": 0.0}


def _crear_sesion_vacia() -> str:
    """Abre sesión enviando un saludo invisible para obtener sesion_id."""
    data = api_post("/chat", json={"mensaje": "inicio"})
    return data["sesion_id"]


def enviar_chat(mensaje: str):
    data = api_post(
        "/chat",
        json={"mensaje": mensaje, "sesion_id": st.session_state.sesion_id},
    )
    st.session_state.sesion_id = data["sesion_id"]
    st.session_state.mensajes.append({"rol": "user", "contenido": mensaje})
    st.session_state.mensajes.append(
        {
            "rol": "assistant",
            "contenido": data["respuesta"],
            "productos": data.get("productos_citados", []),
            "sugeridos": data.get("productos_sugeridos", []),
            "pasos": data.get("pasos", []),
        }
    )


def _parsear_sse(lineas):
    """Genera pares (evento, data) a partir de un iterable de líneas SSE."""
    evento = None
    for linea in lineas:
        if not linea:
            continue
        if linea.startswith("event:"):
            evento = linea.split(":", 1)[1].strip()
        elif linea.startswith("data:"):
            raw = linea.split(":", 1)[1].strip()
            yield evento, (json.loads(raw) if raw else {})


def stream_chat(mensaje: str):
    """Consume /chat/stream y devuelve (generador_texto, meta_dict).

    El generador solo emite tokens de texto para st.write_stream; el dict con
    productos/pasos/sesion_id se llena por referencia mientras llega el SSE.
    """
    meta: dict = {"respuesta": "", "productos": [], "sugeridos": [], "pasos": [], "sesion_id": None}
    payload = {"mensaje": mensaje, "sesion_id": st.session_state.sesion_id}

    def generador():
        with httpx.stream("POST", f"{BACKEND_URL}/chat/stream", json=payload, timeout=180) as r:
            r.raise_for_status()
            for evento, data in _parsear_sse(r.iter_lines()):
                if evento == "token":
                    texto = data.get("texto", "")
                    meta["respuesta"] += texto
                    yield texto
                elif evento == "meta":
                    meta["productos"] = data.get("productos_citados", [])
                    meta["sugeridos"] = data.get("productos_sugeridos", [])
                    meta["pasos"] = data.get("pasos", [])
                    meta["sesion_id"] = data.get("sesion_id")

    return generador, meta


# ------------------------------------------------------------
# Page config + estado
# ------------------------------------------------------------
st.set_page_config(page_title="Asistente Dismac", page_icon="🛒", layout="wide")

if "sesion_id" not in st.session_state:
    st.session_state.sesion_id = None
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None
if "mostrar_checkout" not in st.session_state:
    st.session_state.mostrar_checkout = False


# ------------------------------------------------------------
# Barra lateral: CARRITO
# ------------------------------------------------------------
with st.sidebar:
    st.title("🛒 Tu carrito")
    carrito = obtener_carrito()
    if not carrito["items"]:
        st.info("Tu carrito está vacío. Pedí recomendaciones al asistente y agregá productos con un clic.")
    else:
        for item in carrito["items"]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"**{item['nombre']}**  \n"
                    f"`{item['sku']}` · x{item['cantidad']}  \n"
                    f"Bs {float(item['subtotal_bob']):.2f}"
                )
            with col2:
                if st.button("🗑", key=f"del_{item['sku']}", help="Quitar del carrito"):
                    quitar_carrito(item["sku"])
                    st.rerun()
            st.divider()

        st.markdown(f"### Total: Bs {carrito['total_bob']:.2f}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Vaciar", use_container_width=True):
                vaciar_carrito()
                st.rerun()
        with c2:
            abrir_checkout = st.button(
                "Confirmar compra", type="primary", use_container_width=True
            )

        if abrir_checkout:
            st.session_state.mostrar_checkout = True

        if st.session_state.get("mostrar_checkout"):
            with st.form("form_checkout", clear_on_submit=False):
                st.markdown("#### Tus datos para la orden")
                nombre = st.text_input("Nombre completo", key="chk_nombre")
                email = st.text_input("Email", key="chk_email")
                telefono = st.text_input("Teléfono (WhatsApp)", key="chk_tel")
                notas = st.text_area("Notas (opcional)", key="chk_notas", height=70)
                enviar = st.form_submit_button("Crear orden", type="primary")
            if enviar:
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    try:
                        orden = api_post(
                            f"/ordenes/{st.session_state.sesion_id}",
                            json={
                                "cliente_nombre": nombre.strip(),
                                "cliente_email": email.strip() or None,
                                "cliente_telefono": telefono.strip() or None,
                                "notas": notas.strip() or None,
                            },
                        )
                        st.success(
                            f"¡Orden {orden['numero_orden']} creada! "
                            f"Total Bs {orden['total_bob']:.2f}. "
                            f"Un asesor Dismac te contacta pronto."
                        )
                        st.session_state.mostrar_checkout = False
                        st.session_state.ultima_orden = orden
                        st.rerun()
                    except httpx.HTTPError as e:
                        st.error(f"No se pudo crear la orden: {e}")

    st.divider()
    st.subheader("Sesión")
    st.caption(f"ID: `{st.session_state.sesion_id or '—'}`")
    if st.button("Nueva conversación", use_container_width=True):
        st.session_state.sesion_id = None
        st.session_state.mensajes = []
        st.rerun()


# ------------------------------------------------------------
# Cuerpo principal: CHAT + TARJETAS
# ------------------------------------------------------------
st.title("Asistente de compras Dismac")
st.caption("Agente IA — busca, compara y arma tu carrito por voz o texto. Precios en Bs.")


def render_dashboard():
    with st.expander("📊 Dashboard de métricas (admin)", expanded=False):
        dias = st.slider("Ventana (días)", min_value=1, max_value=30, value=7, key="dash_dias")
        try:
            data = api_get(f"/metricas/dashboard?dias={dias}")
        except httpx.HTTPError as exc:
            st.error(f"No pude traer métricas: {exc}")
            return
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Turnos", data["turnos"])
        c2.metric("Sesiones", data["sesiones"])
        c3.metric("Cerraron orden", f"{data['pct_sesiones_cerraron']}%")
        c4.metric("Turnos con mentiras", f"{data['pct_turnos_con_mentiras']}%")
        l1, l2, l3 = st.columns(3)
        l1.metric("Latencia avg", f"{data['avg_ms']:.0f} ms")
        l2.metric("Latencia p50", f"{data['p50_ms']} ms")
        l3.metric("Latencia p95", f"{data['p95_ms']} ms")
        if data["por_ruta"]:
            st.markdown("**Por ruta:**")
            st.dataframe(data["por_ruta"], use_container_width=True, hide_index=True)
        if st.button("🔁 Reindexar embeddings", help="Calcula embeddings faltantes para búsqueda semántica"):
            try:
                resp = api_post("/admin/embeddings/reindexar")
                st.success(f"Reindexados {resp.get('reindexados', 0)} productos")
            except httpx.HTTPError as exc:
                st.error(f"Falló la reindexación: {exc}")


render_dashboard()


def render_pasos(pasos: list[dict]):
    if not pasos:
        return
    frases = [_paso_humano(p) for p in pasos]
    frases = [f for f in frases if f]
    if not frases:
        return
    with st.expander(f"🪄 Así lo resolví ({len(frases)})"):
        for frase in frases:
            st.markdown(f"- {frase}")


_STOPWORDS = {
    "muestrame", "muestra", "muéstrame", "opciones", "opcion", "quiero", "dame",
    "necesito", "buscame", "búscame", "algo", "las", "los", "del", "para", "que",
    "más", "mas", "por", "con", "sin", "una", "uno", "esos", "esas", "estas",
    "anteriores", "similares", "disponibles",
}


def _resumir_termino(args: dict) -> str:
    """Extrae un término corto y legible para mostrar al usuario."""
    q = (args.get("query") or "").strip().lower()
    palabras = [p for p in q.split() if p not in _STOPWORDS and len(p) > 2][:3]
    if palabras:
        return " ".join(palabras)
    return args.get("categoria") or args.get("marca") or ""


def _humano_buscar(args: dict, result: dict) -> str:
    termino = _resumir_termino(args)
    n = result.get("total", 0)
    objeto = f"«{termino}»" if termino else "en el catálogo"
    if n == 0:
        return f"Busqué {objeto} — sin coincidencias por ahora."
    if n == 1:
        return f"Busqué {objeto} — encontré 1 opción."
    return f"Busqué {objeto} — encontré {n} opciones."


def _humano_ver_producto(args: dict, result: dict) -> str:
    nombre = result.get("nombre") or ""
    sku = result.get("sku") or args.get("sku") or ""
    if nombre:
        return f"Abrí la ficha de {nombre} [{sku}]."
    return f"Abrí la ficha del producto [{sku}]."


def _humano_agregar(args: dict, result: dict) -> str:
    cant = result.get("cantidad_agregada", 1)
    sku = result.get("sku") or args.get("sku") or ""
    if cant == 1:
        return f"Sumé [{sku}] a tu carrito."
    return f"Sumé {cant} unidades de [{sku}] a tu carrito."


def _humano_quitar(args: dict, result: dict) -> str:
    sku = result.get("sku") or args.get("sku") or ""
    return f"Saqué [{sku}] del carrito."


def _humano_ver_carrito(_args: dict, result: dict) -> str:
    n = len(result.get("items") or [])
    total = result.get("total_bob", 0)
    if n == 0:
        return "Miré tu carrito — todavía está vacío."
    if n == 1:
        return f"Miré tu carrito: 1 producto, total Bs {total:.0f}."
    return f"Miré tu carrito: {n} productos, total Bs {total:.0f}."


def _humano_confirmar(_args: dict, result: dict) -> str:
    numero = result.get("numero_orden", "?")
    total = result.get("total_bob", 0)
    return f"Cerré tu orden #{numero} por Bs {total:.0f}. 🎉"


def _humano_ver_ordenes(_args: dict, result: dict) -> str:
    n = len(result.get("ordenes") or [])
    if n == 0:
        return "Revisé el historial — todavía no tenés órdenes en esta sesión."
    if n == 1:
        return "Revisé el historial — tenés 1 orden previa."
    return f"Revisé el historial — tenés {n} órdenes previas."


def _humano_comparar(args: dict, result: dict) -> str:
    skus = args.get("skus") or []
    n = len(result.get("productos") or skus)
    return f"Comparé {n} productos lado a lado."


def _humano_ausente(_args: dict, result: dict) -> str:
    alt = result.get("alternativas", 0)
    if result.get("sugerencia_registrada"):
        return "No tenemos ese producto exacto — anoté tu pedido y busqué alternativas parecidas."
    if alt == 1:
        return "Busqué alternativas y encontré 1 que se acerca."
    if alt > 1:
        return f"Busqué alternativas y encontré {alt} que se acercan."
    return "Busqué algo parecido, pero no apareció nada claro."


PASO_HUMANIZADORES = {
    "buscar_productos": _humano_buscar,
    "listar_categorias": lambda _a, _r: "Repasé las categorías disponibles.",
    "ver_producto": _humano_ver_producto,
    "agregar_al_carrito": _humano_agregar,
    "quitar_del_carrito": _humano_quitar,
    "ver_carrito": _humano_ver_carrito,
    "vaciar_carrito": lambda _a, _r: "Vacié tu carrito.",
    "confirmar_orden": _humano_confirmar,
    "ver_ordenes_sesion": _humano_ver_ordenes,
    "comparar_productos": _humano_comparar,
    "manejador_producto_ausente": _humano_ausente,
}


def _paso_humano(paso: dict) -> str:
    result = paso.get("result") or {}
    if "error" in result:
        return f"⚠️ No pude completar la acción: {result['error']}"
    fn = PASO_HUMANIZADORES.get(paso.get("tool", ""))
    return fn(paso.get("args") or {}, result) if fn else ""


def _render_tarjeta_producto(p: dict, key_prefix: str):
    st.image(imagen_url(p), use_column_width=True)
    st.markdown(f"**{p['nombre']}**")
    st.caption(f"SKU `{p['sku']}` · {p.get('marca') or '—'}")
    st.markdown(formato_precio(p), unsafe_allow_html=True)
    if p.get("justificacion"):
        st.caption(f"💡 _{p['justificacion']}_")
    b1, b2 = st.columns([2, 1])
    with b1:
        agregar = st.button(
            "🛒 Agregar",
            key=f"{key_prefix}_add_{p['sku']}",
            use_container_width=True,
        )
    with b2:
        mas_info = st.button(
            "ℹ️",
            key=f"{key_prefix}_info_{p['sku']}",
            help="Preguntar más detalles",
        )
    if agregar:
        try:
            agregar_carrito(p["sku"])
        except BackendNoDisponibleError as exc:
            st.error(str(exc))
            st.stop()
        st.toast(f"Agregado: {p['nombre']}", icon="✅")
        st.rerun()
    if mas_info:
        st.session_state.pending_input = (
            f"Contame más sobre el producto {p['sku']}, ¿qué ventajas tiene?"
        )
        st.rerun()


def render_tarjetas(productos: list[dict], key_prefix: str, titulo: str = "Productos sugeridos"):
    if not productos:
        return
    st.markdown(f"##### {titulo}")
    cols_por_fila = 3
    for i in range(0, len(productos), cols_por_fila):
        cols = st.columns(cols_por_fila)
        for col, p in zip(cols, productos[i : i + cols_por_fila]):
            with col, st.container(border=True):
                _render_tarjeta_producto(p, key_prefix)


# Render de historial
for idx, m in enumerate(st.session_state.mensajes):
    with st.chat_message(m["rol"]):
        st.markdown(m["contenido"])
        if m.get("productos"):
            render_tarjetas(m["productos"], key_prefix=f"m{idx}", titulo="Productos recomendados")
        if m.get("sugeridos"):
            render_tarjetas(
                m["sugeridos"], key_prefix=f"m{idx}-cs", titulo="También podría interesarte"
            )

# Atajos contextuales
if st.session_state.mensajes and st.session_state.mensajes[-1]["rol"] == "assistant":
    ultimos_productos = st.session_state.mensajes[-1].get("productos") or []
    if ultimos_productos:
        st.markdown(" ")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("🙅 Ninguno me sirve"):
                st.session_state.pending_input = (
                    "Ninguno de estos me sirve. Contame qué otras opciones hay; "
                    "te puedo dar mi presupuesto, tamaño o marca si lo preferís."
                )
                st.rerun()
        with c2:
            if st.button("💸 Más baratos"):
                st.session_state.pending_input = "Muéstrame opciones más económicas que las anteriores."
                st.rerun()
        with c3:
            if st.button("🔎 Mostrar más opciones"):
                st.session_state.pending_input = "Muéstrame otras opciones distintas a las que ya me diste."
                st.rerun()

# Input de chat
if st.session_state.pending_input:
    pregunta = st.session_state.pending_input
    st.session_state.pending_input = None
else:
    pregunta = st.chat_input("Ej: Busco un televisor 4K de 55 pulgadas hasta Bs 5500…")

INDICADOR_PENSANDO = (
    "<span style='color:#888'>Dismi está escribiendo"
    "<span class='dismi-dots'>…</span></span>"
    "<style>"
    "@keyframes dismi-blink{0%,20%{opacity:.2}50%{opacity:1}100%{opacity:.2}}"
    ".dismi-dots{display:inline-block;animation:dismi-blink 1.2s infinite}"
    "</style>"
)


def render_turno_stream(pregunta: str):
    """Muestra la pregunta y consume /chat/stream para pintar tokens en vivo."""
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(INDICADOR_PENSANDO, unsafe_allow_html=True)
        generador, meta = stream_chat(pregunta)
        texto = ""
        for tok in generador():
            texto += tok
            placeholder.markdown(texto + " ▌")
        placeholder.markdown(texto or meta.get("respuesta", ""))
    if meta.get("sesion_id"):
        st.session_state.sesion_id = meta["sesion_id"]
    st.session_state.mensajes.append(
        {
            "rol": "assistant",
            "contenido": meta["respuesta"],
            "productos": meta["productos"],
            "pasos": meta["pasos"],
        }
    )
    st.rerun()


if pregunta:
    try:
        render_turno_stream(pregunta)
    except httpx.HTTPError as e:
        st.error(f"Error contactando al backend: {e}")
