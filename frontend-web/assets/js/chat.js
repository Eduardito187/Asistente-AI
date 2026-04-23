(() => {
  const API_BASE = "/api";
  const STORAGE_KEY = "dismi_chat_state";
  const TTL_MS = 60 * 60 * 1000; // 1 hora de inactividad

  const toggleBtn = document.getElementById("chat-toggle");
  const widget = document.getElementById("chat-widget");
  const closeBtn = document.getElementById("chat-close");
  const endBtn = document.getElementById("chat-end");
  const messagesEl = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = form.querySelector(".chat-send");
  const badge = document.getElementById("chat-badge");

  const SALUDO_INICIAL =
    "¡Hola! Soy Dismi 👋 Te ayudo a elegir productos, comparar precios o armar tu carrito. ¿Qué estás buscando?";

  let sesionId = null;
  let historia = []; // [{tipo, texto, productos, sugeridos}]

  // ========== Persistencia ==========
  function cargarEstado() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const state = JSON.parse(raw);
      if (!state || typeof state !== "object") return null;
      if (Date.now() - (state.ultimaActividad || 0) > TTL_MS) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }
      return state;
    } catch {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
  }

  function guardarEstado() {
    const state = {
      sesionId,
      historia,
      ultimaActividad: Date.now(),
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // localStorage lleno / bloqueado → ignorar silencioso
    }
  }

  function finalizarConversacion() {
    localStorage.removeItem(STORAGE_KEY);
    sesionId = null;
    historia = [];
    messagesEl.innerHTML = "";
    agregarMensaje("bot", SALUDO_INICIAL, [], [], { persistir: true });
    cerrarChat();
  }

  // ========== Render ==========
  function limpiarTextoConProductos(texto, tieneProductos) {
    if (!tieneProductos || !texto) return texto;
    const lineas = texto.split(/\n/);
    const limpio = lineas.filter(l => !/^\s*(\d+[.)]|\*|-|\*\*?\d+[.)])\s?.*\[[A-Za-z0-9][\w\-./#()]+\]/.test(l));
    const resultado = limpio.join("\n").replace(/\n{3,}/g, "\n\n").trim();
    return resultado || texto;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function formatoMoneda(n) {
    if (n == null) return "";
    return "Bs " + Math.round(Number(n)).toLocaleString("es-BO");
  }

  function emojiPorCategoria(cat) {
    const m = {
      "Smartphones": "📱", "Celulares": "📱", "Laptops": "💻", "Notebooks": "💻",
      "Smart TV": "📺", "Televisores": "📺", "Smartwatch": "⌚", "Relojes": "⌚",
      "Audio": "🎧", "Audífonos": "🎧", "Parlantes": "🔊",
      "Freidoras": "🍳", "Licuadoras": "🥤", "Cafeteras": "☕",
      "Refrigeradores": "❄️", "Lavadoras": "🫧", "Microondas": "🍲",
      "Impresoras": "🖨️", "Gaming": "🎮", "Tablets": "📱",
    };
    return m[cat] || "🛍️";
  }

  function imagenProducto(p) {
    if (p.imagen_url && p.imagen_url.startsWith("http") && !p.imagen_url.includes("example")) {
      return `<img src="${escapeHtml(p.imagen_url)}" alt="" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"/><span style="display:none">${emojiPorCategoria(p.subcategoria || p.categoria)}</span>`;
    }
    return `<span>${emojiPorCategoria(p.subcategoria || p.categoria)}</span>`;
  }

  function renderCard(p) {
    const px = `<strong>${formatoMoneda(p.precio_bob)}</strong>` +
      (p.precio_anterior_bob && p.precio_anterior_bob > p.precio_bob
        ? ` <s>${formatoMoneda(p.precio_anterior_bob)}</s>` : "");
    return `
      <div class="chat-card" data-sku="${escapeHtml(p.sku)}">
        <div class="chat-card-thumb">${imagenProducto(p)}</div>
        <div class="chat-card-info">
          <div class="nm">${escapeHtml(p.nombre)}</div>
          <div class="px">${px}</div>
        </div>
      </div>`;
  }

  function dibujarMensaje(tipo, texto, productos = [], sugeridos = []) {
    const wrapper = document.createElement("div");
    wrapper.className = `msg ${tipo}`;
    wrapper.innerHTML = escapeHtml(texto || "").replace(/\n/g, "<br>");
    messagesEl.appendChild(wrapper);

    if (productos && productos.length) {
      const cards = document.createElement("div");
      cards.className = "chat-products";
      cards.innerHTML = productos.map(renderCard).join("");
      messagesEl.appendChild(cards);
    }
    if (sugeridos && sugeridos.length) {
      const titulo = document.createElement("div");
      titulo.className = "chat-sugeridos-title";
      titulo.textContent = "También podría interesarte";
      messagesEl.appendChild(titulo);
      const cards = document.createElement("div");
      cards.className = "chat-products";
      cards.innerHTML = sugeridos.map(renderCard).join("");
      messagesEl.appendChild(cards);
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function agregarMensaje(tipo, texto, productos = [], sugeridos = [], opts = {}) {
    dibujarMensaje(tipo, texto, productos, sugeridos);
    historia.push({ tipo, texto, productos, sugeridos });
    if (opts.persistir !== false) guardarEstado();
  }

  function restaurarHistoria(items) {
    messagesEl.innerHTML = "";
    for (const m of items) {
      dibujarMensaje(m.tipo, m.texto, m.productos || [], m.sugeridos || []);
    }
  }

  function mostrarTyping() {
    const el = document.createElement("div");
    el.className = "msg bot typing";
    el.id = "typing-indicator";
    el.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function quitarTyping() {
    const t = document.getElementById("typing-indicator");
    if (t) t.remove();
  }

  // ========== Flujo ==========
  async function enviarMensaje(mensaje) {
    agregarMensaje("user", mensaje);
    mostrarTyping();
    sendBtn.disabled = true;

    try {
      const r = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje, sesion_id: sesionId }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      if (d.sesion_id) sesionId = d.sesion_id;
      quitarTyping();
      const tieneProductos = (d.productos_citados || []).length > 0;
      const texto = limpiarTextoConProductos(d.respuesta || "", tieneProductos);
      agregarMensaje("bot", texto, d.productos_citados || [], d.productos_sugeridos || []);
    } catch (err) {
      quitarTyping();
      agregarMensaje(
        "bot",
        "Uy, se me complicó la conexión un segundo 🙈 ¿Me lo repetís? Ya vuelvo a estar listo para ayudarte."
      );
      console.error(err);
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  const abrirChat = () => {
    widget.classList.add("open");
    widget.setAttribute("aria-hidden", "false");
    badge.classList.add("hidden");
    input.focus();
  };

  const cerrarChat = () => {
    widget.classList.remove("open");
    widget.setAttribute("aria-hidden", "true");
  };

  // ========== Init ==========
  const estadoPrevio = cargarEstado();
  if (estadoPrevio && estadoPrevio.historia && estadoPrevio.historia.length) {
    sesionId = estadoPrevio.sesionId || null;
    historia = estadoPrevio.historia;
    restaurarHistoria(historia);
  } else {
    agregarMensaje("bot", SALUDO_INICIAL, [], [], { persistir: true });
  }

  toggleBtn.addEventListener("click", () => {
    widget.classList.contains("open") ? cerrarChat() : abrirChat();
  });
  closeBtn.addEventListener("click", cerrarChat);
  endBtn?.addEventListener("click", () => {
    if (confirm("¿Finalizar esta conversación? Se borrarán los mensajes.")) {
      finalizarConversacion();
    }
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    enviarMensaje(msg);
  });
})();
