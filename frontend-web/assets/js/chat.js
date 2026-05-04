/* ── Dark mode ─────────────────────────────────────────────────────────── */
(() => {
  const THEME_KEY = "dismi_theme";
  const html = document.documentElement;
  const toggle = document.getElementById("theme-toggle");

  const apply = (dark) => {
    html.dataset.theme = dark ? "dark" : "light";
    if (toggle) toggle.checked = dark;
  };

  apply(localStorage.getItem(THEME_KEY) === "dark");

  if (toggle) {
    toggle.addEventListener("change", () => {
      const dark = toggle.checked;
      localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
      apply(dark);
    });
  }
})();

/* ── Chat widget ─────────────────────────────────────────────────────────── */
(() => {
  const API_BASE = "/api";
  // Bump la versión cuando cambie el formato de la historia persistida (ej.
  // agregamos campos a los cards). El `v2` invalida cualquier estado viejo
  // que se haya guardado antes de esta versión.
  const STORAGE_KEY = "dismi_chat_state_v2";
  const TTL_MS = 60 * 60 * 1000; // 1 hora de inactividad
  // Limpiar versión anterior si aún existe
  try { localStorage.removeItem("dismi_chat_state"); } catch {}

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
    const resultado = limpio.join("\n").replaceAll(/\n{3,}/g, "\n\n").trim();
    return resultado || texto;
  }

  function escapeHtml(s) {
    return String(s).replaceAll(/[&<>"']/g, c => ({
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
    if (p.imagen_url?.startsWith("http") && !p.imagen_url.includes("example")) {
      return `<img src="${escapeHtml(p.imagen_url)}" alt="" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"/><span style="display:none">${emojiPorCategoria(p.subcategoria || p.categoria)}</span>`;
    }
    return `<span>${emojiPorCategoria(p.subcategoria || p.categoria)}</span>`;
  }

  function renderCard(p) {
    const px = `<strong>${formatoMoneda(p.precio_bob)}</strong>` +
      (p.precio_anterior_bob && p.precio_anterior_bob > p.precio_bob
        ? ` <s>${formatoMoneda(p.precio_anterior_bob)}</s>` : "");
    const skuEsc = escapeHtml(p.sku);
    return `
      <div class="chat-card" data-sku="${skuEsc}">
        <div class="chat-card-top">
          <div class="chat-card-thumb">${imagenProducto(p)}</div>
          <div class="chat-card-info">
            <div class="nm">${escapeHtml(p.nombre)}</div>
            <div class="px">${px}</div>
          </div>
        </div>
        <div class="chat-card-actions">
          <button type="button" class="chat-card-action primary" data-action="agregar" data-sku="${skuEsc}" title="Agregar al carrito">
            <span class="ico">🛒</span><span class="lbl">Agregar</span>
          </button>
          <button type="button" class="chat-card-action" data-action="info" data-sku="${skuEsc}" title="Más información">
            <span class="ico">ℹ️</span><span class="lbl">Detalle</span>
          </button>
          <button type="button" class="chat-card-action" data-action="similares" data-sku="${skuEsc}" title="Opciones similares">
            <span class="ico">🔍</span><span class="lbl">Similares</span>
          </button>
        </div>
      </div>`;
  }

  // Plantillas de mensaje para acciones que van al chat (info, similares).
  // "agregar" NO va al chat — se maneja directamente contra la API del carrito.
  const MENSAJE_ACCION = {
    info:      (sku, nombre) => `Contame más del ${nombre} [${sku}] — specs clave.`,
    similares: (sku, nombre) => `Mostrame opciones similares al ${nombre} [${sku}], distintas a esa.`,
  };

  async function agregarAlCarrito(btn, sku) {
    if (!sesionId) return;
    btn.disabled = true;
    const lblOriginal = btn.querySelector(".lbl")?.textContent || "Agregar";
    const lbl = btn.querySelector(".lbl");
    if (lbl) lbl.textContent = "...";
    try {
      const r = await fetch(`${API_BASE}/carrito/${sesionId}/agregar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sku }),
      });
      if (r.ok) {
        btn.classList.add("agregado");
        if (lbl) lbl.textContent = "Agregado ✓";
        setTimeout(() => {
          btn.classList.remove("agregado");
          btn.disabled = false;
          if (lbl) lbl.textContent = lblOriginal;
        }, 2000);
      } else {
        if (lbl) lbl.textContent = lblOriginal;
        btn.disabled = false;
      }
    } catch {
      if (lbl) lbl.textContent = lblOriginal;
      btn.disabled = false;
    }
  }

  function nombrePorSku(sku) {
    // Busca el último nombre asociado al SKU en la historia renderizada.
    for (let i = historia.length - 1; i >= 0; i--) {
      const m = historia[i];
      const match = (m.productos || []).concat(m.sugeridos || [])
        .find(p => p.sku === sku);
      if (match) return match.nombre;
    }
    return "ese producto";
  }

  // Convierte un grupo de líneas con pipe en tabla HTML.
  // Retorna null si no es una tabla válida (< 2 filas o sin separador).
  function renderTabla(lineas) {
    const parseFila = l => l.trim().replaceAll(/^\||\|$/g, '').split('|').map(c => c.trim());
    const esSep    = l => /^\|[\s|:-]+\|/.test(l.trim());
    const sepIdx   = lineas.findIndex(esSep);
    if (sepIdx < 1) return null;
    const cabeceras = parseFila(lineas[0]);
    const filas = lineas.slice(sepIdx + 1)
      .map(parseFila)
      .filter(f => f.some(Boolean));
    if (!filas.length) return null;
    const ths = cabeceras.map(h => `<th>${h}</th>`).join('');
    const trs = filas.map(f => {
      const tds = f.map((c, i) => `<td${i === 0 ? ' class="row-header"' : ''}>${c || '—'}</td>`).join('');
      return `<tr>${tds}</tr>`;
    }).join('');
    return `<div class="chat-table-wrap"><table class="chat-table"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></div>`;
  }

  // Procesa una línea de bullet o texto plano; devuelve el nuevo estado enLista.
  function _mdBullet(linea, enLista, out) {
    const m = linea.match(/^\s*[-*•]\s+(.*)$/);
    if (m) {
      if (!enLista) out.push('<ul class="chat-bullets">');
      out.push(`<li>${m[1]}</li>`);
      return true;
    }
    if (enLista) out.push('</ul>');
    out.push(linea);
    return false;
  }

  // Renderiza markdown: bold (**), bullets (-) y tablas (|).
  // Entrada: texto ya escapado con escapeHtml.
  function renderMarkdown(textoEscapado) {
    const html      = textoEscapado.replaceAll(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    const lineas    = html.split('\n');
    const out       = [];
    let enLista     = false;
    let grupoTabla  = [];

    for (const linea of lineas) {
      if (linea.trim().startsWith('|')) {
        if (enLista) { out.push('</ul>'); enLista = false; }
        grupoTabla.push(linea);
        continue;
      }
      if (grupoTabla.length) {
        out.push(renderTabla(grupoTabla) ?? grupoTabla.join('\n'));
        grupoTabla = [];
      }
      enLista = _mdBullet(linea, enLista, out);
    }
    if (grupoTabla.length) out.push(renderTabla(grupoTabla) ?? grupoTabla.join('\n'));
    if (enLista) out.push('</ul>');

    return out.join('\n')
      .replaceAll('\n', '<br>')
      .replaceAll(/<br>(<\/?[ut][ldr]>|<div)/g, '$1')
      .replaceAll(/(<\/div>|<\/?[ut][ldr]>)<br>/g, '$1');
  }

  function renderCardsBloque(items, titulo) {
    if (!items?.length) return;
    if (titulo) {
      const h = document.createElement("div");
      h.className = "chat-sugeridos-title";
      h.textContent = titulo;
      messagesEl.appendChild(h);
    }
    const cards = document.createElement("div");
    cards.className = "chat-products";
    cards.innerHTML = items.map(renderCard).join("");
    messagesEl.appendChild(cards);
  }

  function dibujarMensaje(tipo, texto, productos = [], sugeridos = []) {
    const wrapper = document.createElement("div");
    wrapper.className = `msg ${tipo}`;
    wrapper.innerHTML = renderMarkdown(escapeHtml(texto || ""));
    messagesEl.appendChild(wrapper);
    renderCardsBloque(productos);
    renderCardsBloque(sugeridos, "También podría interesarte");
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
  // Timeout amplio — el backend puede tardar 5-15s cuando el modelo piensa
  // una consulta nueva. Abortamos recién después de 60s para no cortar
  // respuestas válidas pero lentas.
  const TIMEOUT_MS = 60000;

  // Parser SSE incremental: devuelve eventos completos y el buffer restante
  // (lo que quedo sin cerrar por el delimitador "\n\n").
  function parsearSSE(buffer) {
    const eventos = [];
    let rest = buffer;
    let idx = rest.indexOf("\n\n");
    while (idx >= 0) {
      const bloque = rest.slice(0, idx);
      rest = rest.slice(idx + 2);
      let evento = "message";
      const dataLines = [];
      for (const linea of bloque.split("\n")) {
        if (linea.startsWith("event:")) evento = linea.slice(6).trim();
        else if (linea.startsWith("data:")) dataLines.push(linea.slice(5).trim());
      }
      if (dataLines.length) {
        try { eventos.push({ evento, data: JSON.parse(dataLines.join("\n")) }); }
        catch { /* ignorar chunks mal formados */ }
      }
      idx = rest.indexOf("\n\n");
    }
    return { eventos, rest };
  }

  async function enviarMensaje(mensaje) {
    agregarMensaje("user", mensaje);
    mostrarTyping();
    sendBtn.disabled = true;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    // Burbuja del bot se crea recien al llegar el primer token — asi el
    // indicador de typing se mantiene mientras el backend piensa.
    let botEl = null;
    let textoAcum = "";
    let productos = [];
    let sugeridos = [];

    const asegurarBurbuja = () => {
      if (botEl) return;
      quitarTyping();
      botEl = document.createElement("div");
      botEl.className = "msg bot";
      messagesEl.appendChild(botEl);
    };

    try {
      const r = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ mensaje, sesion_id: sesionId }),
        signal: controller.signal,
      });
      if (!r.ok || !r.body) {
        await r.text().catch(() => "");
        throw new Error("error de red");
      }

      const manejarEvento = ({ evento, data }) => {
        if (evento === "token") {
          asegurarBurbuja();
          textoAcum += data.texto || "";
          botEl.innerHTML = renderMarkdown(escapeHtml(textoAcum));
          messagesEl.scrollTop = messagesEl.scrollHeight;
        } else if (evento === "meta") {
          if (data.sesion_id) sesionId = data.sesion_id;
          productos = data.productos_citados || [];
          sugeridos = data.productos_sugeridos || [];
        }
      };

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let chunk = await reader.read();
      while (!chunk.done) {
        buffer += decoder.decode(chunk.value, { stream: true });
        const { eventos, rest } = parsearSSE(buffer);
        eventos.forEach(manejarEvento);
        buffer = rest;
        chunk = await reader.read();
      }

      // Fin: render final con limpieza y tarjetas.
      asegurarBurbuja();
      const textoFinal = limpiarTextoConProductos(textoAcum, productos.length > 0);
      botEl.innerHTML = renderMarkdown(escapeHtml(textoFinal));
      renderCardsBloque(productos);
      renderCardsBloque(sugeridos, "También podría interesarte");
      messagesEl.scrollTop = messagesEl.scrollHeight;
      historia.push({ tipo: "bot", texto: textoFinal, productos, sugeridos });
      guardarEstado();
    } catch (err) {
      quitarTyping();
      const causa = err.name === "AbortError"
        ? "tardé mucho (timeout 60s)"
        : (err.message || "error de red");
      agregarMensaje(
        "bot",
        `Uy, se me complicó la conexión 🙈 (${causa}) ¿Me lo repetís?`
      );
      console.error("chat stream error:", err);
    } finally {
      clearTimeout(timer);
      sendBtn.disabled = false;
      input.focus();
    }
  }

  const abrirChat = () => {
    widget.show();
    widget.classList.add("open");
    badge.classList.add("hidden");
    input.focus();
  };

  const cerrarChat = () => {
    widget.classList.remove("open");
    widget.close();
  };

  // ========== Init ==========
  const estadoPrevio = cargarEstado();
  if (estadoPrevio?.historia?.length) {
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
  const confirmOverlay = document.getElementById("chat-confirm-overlay");
  const confirmOkBtn   = document.getElementById("chat-confirm-ok");
  const confirmCancelBtn = document.getElementById("chat-confirm-cancel");

  function mostrarConfirm() {
    confirmOverlay.removeAttribute("aria-hidden");
    confirmOkBtn.focus();
  }
  function ocultarConfirm() {
    confirmOverlay.setAttribute("aria-hidden", "true");
  }
  confirmOkBtn.addEventListener("click", () => {
    ocultarConfirm();
    finalizarConversacion();
  });
  confirmCancelBtn.addEventListener("click", ocultarConfirm);

  endBtn?.addEventListener("click", mostrarConfirm);

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    enviarMensaje(msg);
  });

  // Delegación de click sobre las tarjetas de producto: un solo listener
  // atiende todos los cards (presentes y futuros).
  messagesEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".chat-card-action");
    if (!btn) return;
    const accion = btn.dataset.action;
    const sku = btn.dataset.sku;
    if (!sku) return;
    if (accion === "agregar") {
      agregarAlCarrito(btn, sku);
      return;
    }
    const builder = MENSAJE_ACCION[accion];
    if (!builder) return;
    const nombre = nombrePorSku(sku);
    enviarMensaje(builder(sku, nombre));
  });
})();
