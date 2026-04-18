"""Frontend Streamlit — Asistente de compras Dismac.

- Chat con el asistente.
- Tarjetas de producto clickeables con imagen, precio y botón 'Agregar al carrito'.
- Carrito lateral con subtotales, total y acciones (quitar, vaciar, simular compra).
- Botón 'No me sirve ninguno' para pedir más opciones al asistente.
"""
from __future__ import annotations

import os
from urllib.parse import quote

import httpx
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def api_get(path: str, **kwargs):
    r = httpx.get(f"{BACKEND_URL}{path}", timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()


def api_post(path: str, **kwargs):
    r = httpx.post(f"{BACKEND_URL}{path}", timeout=180, **kwargs)
    r.raise_for_status()
    return r.json()


def api_delete(path: str):
    r = httpx.delete(f"{BACKEND_URL}{path}", timeout=20)
    r.raise_for_status()
    return r.json()


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
            "pasos": data.get("pasos", []),
        }
    )


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
                    f"Bs {float(item['subtotal']):.2f}"
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


def render_pasos(pasos: list[dict]):
    if not pasos:
        return
    with st.expander(f"🔧 Acciones del agente ({len(pasos)} paso{'s' if len(pasos) != 1 else ''})"):
        for i, paso in enumerate(pasos):
            tool = paso.get("tool", "?")
            args = paso.get("args", {}) or {}
            result = paso.get("result", {}) or {}
            args_str = ", ".join(f"{k}={v!r}" for k, v in args.items()) if args else ""
            st.markdown(f"**{i+1}.** `{tool}({args_str})`")
            resumen = _resumen_resultado(tool, result)
            if resumen:
                st.caption(resumen)


def _resumen_resultado(tool: str, result: dict) -> str:
    if "error" in result:
        return f"⚠️ {result['error']}"
    if tool == "buscar_productos":
        n = result.get("total", 0)
        return f"{n} resultado(s): " + ", ".join(
            p["sku"] for p in (result.get("productos") or [])[:5]
        )
    if tool == "listar_categorias":
        cats = result.get("categorias") or []
        return ", ".join(f"{c['categoria']} ({c['cantidad']})" for c in cats[:8])
    if tool == "ver_producto":
        return f"{result.get('sku','?')} — {result.get('nombre','')}"
    if tool == "agregar_al_carrito":
        return f"+{result.get('cantidad_agregada',1)} × {result.get('sku','?')}"
    if tool == "quitar_del_carrito":
        return f"quitado {result.get('sku','?')}"
    if tool == "ver_carrito":
        n = len(result.get("items") or [])
        return f"{n} item(s), total Bs {result.get('total_bob', 0):.2f}"
    if tool == "vaciar_carrito":
        return "carrito vaciado"
    if tool == "confirmar_orden":
        return (
            f"orden {result.get('numero_orden','?')} "
            f"Bs {result.get('total_bob',0):.2f} · "
            f"{result.get('items_cantidad',0)} items"
        )
    if tool == "ver_ordenes_sesion":
        ordenes = result.get("ordenes") or []
        return f"{len(ordenes)} orden(es) en esta sesión"
    return ""


def render_tarjetas(productos: list[dict], key_prefix: str):
    if not productos:
        return
    st.markdown("##### Productos sugeridos")
    cols_por_fila = 3
    for i in range(0, len(productos), cols_por_fila):
        cols = st.columns(cols_por_fila)
        for col, p in zip(cols, productos[i : i + cols_por_fila]):
            with col, st.container(border=True):
                st.image(imagen_url(p), use_column_width=True)
                st.markdown(f"**{p['nombre']}**")
                st.caption(f"SKU `{p['sku']}` · {p.get('marca') or '—'}")
                st.markdown(formato_precio(p), unsafe_allow_html=True)
                if p["stock"] > 0:
                    st.caption(f":green[Stock disponible ({p['stock']} uds)]")
                else:
                    st.caption(":red[Sin stock]")
                b1, b2 = st.columns([2, 1])
                with b1:
                    agregar = st.button(
                        "🛒 Agregar",
                        key=f"{key_prefix}_add_{p['sku']}",
                        use_container_width=True,
                        disabled=p["stock"] <= 0,
                    )
                with b2:
                    mas_info = st.button(
                        "ℹ️",
                        key=f"{key_prefix}_info_{p['sku']}",
                        help="Preguntar más detalles",
                    )
                if agregar:
                    agregar_carrito(p["sku"])
                    st.toast(f"Agregado: {p['nombre']}", icon="✅")
                    st.rerun()
                if mas_info:
                    st.session_state.pending_input = (
                        f"Contame más sobre el producto {p['sku']}, ¿qué ventajas tiene?"
                    )
                    st.rerun()


# Render de historial
for idx, m in enumerate(st.session_state.mensajes):
    with st.chat_message(m["rol"]):
        st.markdown(m["contenido"])
        if m.get("pasos"):
            render_pasos(m["pasos"])
        if m.get("productos"):
            render_tarjetas(m["productos"], key_prefix=f"m{idx}")

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

if pregunta:
    with st.spinner("Consultando catálogo y pensando…"):
        try:
            enviar_chat(pregunta)
            st.rerun()
        except httpx.HTTPError as e:
            st.error(f"Error contactando al backend: {e}")
