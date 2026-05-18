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

  // Plantillas de mensaje para acciones que van al chat.
  // "agregar" e "info" NO van al chat — se manejan localmente.
  const MENSAJE_ACCION = {
    similares: (sku, nombre) => `Mostrame opciones similares al ${nombre} [${sku}], distintas a esa.`,
  };

  // ═══════════════════════════════════════════════════════
  //  POPUP DETALLE DE PRODUCTO
  // ═══════════════════════════════════════════════════════
  const pdpOverlay   = document.getElementById("pdp-overlay");
  const pdpClose     = document.getElementById("pdp-close");
  const pdpBtnCart   = document.getElementById("pdp-btn-cart");
  const pdpBtnSim    = document.getElementById("pdp-btn-similares");
  const pdpCartLbl   = document.getElementById("pdp-btn-cart-lbl");
  let   pdpSkuActual = null;

  // ── Mapa de atributos → {label, icon, sufijo} ──────────────────────────
  const SPEC_MAP = [
    { key: "pantalla_pulgadas",  label: "Pantalla",       icon: "📐", suf: '"' },
    { key: "pulgadas",           label: "Pantalla",       icon: "📐", suf: '"' },
    { key: "refresh_hz",         label: "Refresh",        icon: "🔄", suf: " Hz" },
    { key: "procesador",         label: "Procesador",     icon: "⚡", suf: "" },
    { key: "ram_gb",             label: "RAM",            icon: "🧠", suf: " GB" },
    { key: "almacenamiento_gb",  label: "Almacenamiento", icon: "💾", suf: " GB" },
    { key: "bateria_mah",        label: "Batería",        icon: "🔋", suf: " mAh", fmt: "num" },
    { key: "camara_mp",          label: "Cámara",         icon: "📷", suf: " MP" },
    { key: "camara_frontal_mp",  label: "Cam. frontal",   icon: "🤳", suf: " MP" },
    { key: "sistema_operativo",  label: "Sistema",        icon: "📱", suf: "" },
    { key: "resolucion",         label: "Resolución",     icon: "🖥️", suf: "" },
    { key: "capacidad_litros",   label: "Capacidad",      icon: "📦", suf: " L" },
    { key: "capacidad_kg",       label: "Carga",          icon: "⚖️", suf: " kg" },
    { key: "potencia_w",         label: "Potencia",       icon: "⚡", suf: " W" },
    { key: "tipo_panel",         label: "Panel",          icon: "🖥️", suf: "" },
    { key: "conectividad",       label: "Conectividad",   icon: "📶", suf: "" },
    { key: "color",              label: "Color",          icon: "🎨", suf: "" },
    { key: "peso_g",             label: "Peso",           icon: "⚖️", suf: " g" },
  ];

  const _VACIO = new Set(["", "N/D", "—", "n/d", "nd"]);

  function _formatSpecVal(entry, rawVal) {
    const v = entry.fmt === "num"
      ? Number(rawVal).toLocaleString("es-BO")
      : String(rawVal);
    return v + entry.suf;
  }

  function buildSpecs(p) {
    const usadas = new Set();
    const specs  = [];
    for (const s of SPEC_MAP) {
      const raw = p[s.key];
      if (raw == null || _VACIO.has(String(raw))) continue;
      if (usadas.has(s.label)) continue;
      usadas.add(s.label);
      specs.push({ label: s.label, icon: s.icon, val: _formatSpecVal(s, raw) });
    }
    return specs;
  }

  // ── Sub-renderers (mantienen pdpAbrir dentro del límite de complejidad) ─
  function _pdpHero(p) {
    document.getElementById("pdp-badge").textContent  = p.subcategoria || p.categoria || "Producto";
    document.getElementById("pdp-nombre").textContent = p.nombre || "—";
    document.getElementById("pdp-precio").textContent = p.precio_bob ? formatoMoneda(p.precio_bob) : "—";

    const viejoEl = document.getElementById("pdp-precio-old");
    const descEl  = document.getElementById("pdp-descuento");
    const tieneAnterior = p.precio_anterior_bob && p.precio_anterior_bob > p.precio_bob;
    viejoEl.hidden = !tieneAnterior;
    descEl.hidden  = !tieneAnterior;
    if (tieneAnterior) {
      viejoEl.textContent = formatoMoneda(p.precio_anterior_bob);
      descEl.textContent  = `-${Math.round((1 - p.precio_bob / p.precio_anterior_bob) * 100)}%`;
    }

    const imgWrap = document.getElementById("pdp-img-wrap");
    imgWrap.innerHTML = "";
    const fallbackSp = () => {
      const sp = document.createElement("span");
      sp.style.fontSize = "52px";
      sp.textContent = emojiPorCategoria(p.subcategoria || p.categoria);
      imgWrap.appendChild(sp);
    };
    if (p.imagen_url?.startsWith("http") && !p.imagen_url.includes("example")) {
      const img = document.createElement("img");
      img.src = p.imagen_url;
      img.alt = p.nombre || "";
      img.onerror = fallbackSp;
      imgWrap.appendChild(img);
    } else {
      fallbackSp();
    }
  }

  function _pdpSpecs(p) {
    const specsEl = document.getElementById("pdp-specs");
    const specs   = buildSpecs(p);
    specsEl.innerHTML = specs.length
      ? specs.map(s =>
          `<div class="pdp-spec">
            <span class="pdp-spec-icon">${s.icon}</span>
            <div class="pdp-spec-detail">
              <div class="pdp-spec-label">${escapeHtml(s.label)}</div>
              <div class="pdp-spec-val">${escapeHtml(s.val)}</div>
            </div>
          </div>`).join("")
      : `<div class="pdp-spec" style="grid-column:1/-1">
           <span class="pdp-spec-icon">📋</span>
           <div class="pdp-spec-detail">
             <div class="pdp-spec-label">Descripción</div>
             <div class="pdp-spec-val" style="white-space:normal">${escapeHtml(p.descripcion || p.nombre || "—")}</div>
           </div>
         </div>`;
  }

  function _pdpTags(p) {
    const tagsWrap = document.getElementById("pdp-tags-wrap");
    const tagsEl   = document.getElementById("pdp-tags");
    const tags = [
      p.marca    && { icon: "🏷️", txt: p.marca },
      p.modelo   && { icon: "🔢", txt: p.modelo },
      p.garantia && { icon: "🛡️", txt: p.garantia },
      p.sku      && { icon: "📌", txt: `SKU: ${p.sku}` },
    ].filter(Boolean);
    tagsEl.innerHTML = tags.map(t =>
      `<span class="pdp-tag"><span class="ticon">${t.icon}</span>${escapeHtml(t.txt)}</span>`
    ).join("");
    tagsWrap.hidden = !tags.length;
  }

  function _aiHtml(texto) {
    const lineas = texto.split(/\n/);
    let html = "";
    let enLista = false;
    for (const l of lineas) {
      const m = l.match(/^\s*[-•*]\s+(.+)$/);
      if (m) {
        if (!enLista) { html += "<ul>"; enLista = true; }
        html += `<li>${escapeHtml(m[1])}</li>`;
      } else {
        if (enLista) { html += "</ul>"; enLista = false; }
        if (l.trim()) html += `<p>${escapeHtml(l)}</p>`;
      }
    }
    return enLista ? html + "</ul>" : html;
  }

  function _pdpAi(aiTexto) {
    const aiWrap  = document.getElementById("pdp-ai-wrap");
    if (!aiTexto) { aiWrap.hidden = true; return; }
    const aiBlock = document.getElementById("pdp-ai-block");
    const esWarn  = /contra|desventaja|cuidado|sin embargo|limitac/i.test(aiTexto);
    aiBlock.className = "pdp-ai-block" + (esWarn ? " pdp-ai-warn" : "");
    document.getElementById("pdp-ai-chip").textContent =
      esWarn ? "Puntos a considerar" : "Beneficios destacados";
    document.getElementById("pdp-ai-text").innerHTML = _aiHtml(aiTexto);
    aiWrap.hidden = false;
  }

  // Extrae párrafos relevantes del último mensaje bot que mencione el SKU.
  function _aiTextoParaSku(sku) {
    const skuLow = String(sku).toLowerCase();
    for (let i = historia.length - 1; i >= 0; i--) {
      const m = historia[i];
      if (m.tipo !== "bot" || !m.texto) continue;
      const tLow = m.texto.toLowerCase();
      if (!tLow.includes(skuLow) && !tLow.includes("[" + skuLow + "]")) continue;
      const parrafos = m.texto.split(/\n{2,}/).filter(p =>
        p.trim() &&
        !p.includes("[" + sku + "]") &&
        (p.includes("✅") || p.includes("•") ||
         /beneficio|ventaja|ideal|perfecto|recomend|contra|límite|pero/i.test(p))
      );
      if (parrafos.length) return parrafos.join("\n");
    }
    return null;
  }

  function pdpAbrir(p) {
    if (!pdpOverlay) return;
    pdpSkuActual = p.sku;
    _pdpHero(p);
    _pdpSpecs(p);
    _pdpTags(p);
    _pdpAi(_aiTextoParaSku(p.sku));
    pdpBtnCart.classList.remove("pdp-added");
    pdpCartLbl.textContent = "Agregar al carrito";
    pdpBtnCart.disabled = false;
    pdpOverlay.showModal();
    requestAnimationFrame(() => pdpOverlay.classList.add("pdp-visible"));
  }

  function pdpCerrar() {
    pdpOverlay.classList.remove("pdp-visible");
    setTimeout(() => pdpOverlay.close(), 220);
  }

  pdpClose?.addEventListener("click", pdpCerrar);
  pdpOverlay?.addEventListener("click", e => { if (e.target === pdpOverlay) pdpCerrar(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && pdpOverlay?.open) pdpCerrar(); });

  pdpBtnCart?.addEventListener("click", async () => {
    if (!pdpSkuActual || !sesionId) return;
    pdpBtnCart.disabled = true;
    pdpCartLbl.textContent = "...";
    try {
      const r = await fetch(`${API_BASE}/carrito/${sesionId}/agregar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sku: pdpSkuActual }),
      });
      if (r.ok) {
        pdpBtnCart.classList.add("pdp-added");
        pdpCartLbl.textContent = "Agregado ✓";
        setTimeout(() => {
          pdpBtnCart.classList.remove("pdp-added");
          pdpCartLbl.textContent = "Agregar al carrito";
          pdpBtnCart.disabled = false;
        }, 2000);
      } else {
        pdpCartLbl.textContent = "Agregar al carrito";
        pdpBtnCart.disabled = false;
      }
    } catch {
      pdpCartLbl.textContent = "Agregar al carrito";
      pdpBtnCart.disabled = false;
    }
  });

  pdpBtnSim?.addEventListener("click", () => {
    if (!pdpSkuActual) return;
    const nombre = nombrePorSku(pdpSkuActual);
    pdpCerrar();
    setTimeout(() => enviarMensaje(MENSAJE_ACCION.similares(pdpSkuActual, nombre)), 250);
  });

  // Devuelve el objeto producto completo desde la historia por SKU.
  function productoPorSku(sku) {
    for (let i = historia.length - 1; i >= 0; i--) {
      const m = historia[i];
      const match = (m.productos || []).concat(m.sugeridos || []).find(p => p.sku === sku);
      if (match) return match;
    }
    return null;
  }

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
  // En vez de inline, genera un boton "Ver tabla" que abre la tabla en
  // popup — evita scroll dentro del chat.
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
    // Filtrar filas donde TODOS los valores son '—' o 'No disponible' o vacios.
    const filasConDatos = filas.filter(f => {
      const valores = f.slice(1);
      return valores.some(v => v && v !== '—' && v !== 'No disponible' && v !== 'N/D');
    });
    if (!filasConDatos.length) return null;
    const ths = cabeceras.map(h => `<th>${h}</th>`).join('');
    const trs = filasConDatos.map(f => {
      const tds = f.map((c, i) => `<td${i === 0 ? ' class="row-header"' : ''}>${c || '—'}</td>`).join('');
      return `<tr>${tds}</tr>`;
    }).join('');
    const tablaHtml = `<table class="chat-table"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
    const id = `tabla-${Math.random().toString(36).slice(2, 10)}`;
    // Guardamos la tabla en un atributo data para el handler global del modal.
    return (
      `<button type="button" class="chat-table-launcher" data-tabla-id="${id}">` +
      `📊 Ver tabla comparativa (${filasConDatos.length} atributos · ${cabeceras.length - 1} productos)` +
      `</button>` +
      `<template id="${id}" class="chat-table-source">${tablaHtml}</template>`
    );
  }

  function abrirModalTabla(launcher) {
    const id = launcher.dataset.tablaId;
    const tpl = document.getElementById(id);
    if (!tpl) return;
    const overlay = document.createElement('div');
    overlay.className = 'chat-modal-overlay';
    overlay.innerHTML = (
      '<div class="chat-modal" role="dialog" aria-modal="true">' +
      '<button type="button" class="chat-modal-close" aria-label="Cerrar">×</button>' +
      '<div class="chat-modal-header">Tabla comparativa</div>' +
      `<div class="chat-modal-body">${tpl.innerHTML}</div>` +
      '</div>'
    );
    const cerrar = () => overlay.remove();
    overlay.addEventListener('click', e => { if (e.target === overlay) cerrar(); });
    overlay.querySelector('.chat-modal-close').addEventListener('click', cerrar);
    document.addEventListener('keydown', function escListener(e) {
      if (e.key === 'Escape') { cerrar(); document.removeEventListener('keydown', escListener); }
    });
    document.body.appendChild(overlay);
  }

  // Listener delegado para botones que abren tabla comparativa en modal.
  // Funciona para botones renderizados ahora y en futuros mensajes.
  document.addEventListener('click', e => {
    const launcher = e.target.closest('.chat-table-launcher');
    if (launcher) abrirModalTabla(launcher);
  });

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
  // Timeout amplio — turnos con tool-calling y LLM local pueden tardar
  // 30-90s especialmente cuando el modelo encadena varias tools (buscar +
  // ver_producto + comparar). 120s evita cortes prematuros.
  const TIMEOUT_MS = 120000;

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
          const hayOrden = (data.pasos || []).some(
            p => p.tool === "confirmar_orden" && !p.result?.error
          );
          if (hayOrden) setTimeout(mostrarFeedbackPopup, 1500);
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
      let mensaje;
      if (err.name === "AbortError") {
        mensaje = "Tuve una demora consultando el catálogo. " +
                  "Volvé a intentarlo en un momento — guardé tu consulta.";
      } else if (err.message === "error de red") {
        mensaje = "Tuve un problema temporal consultando el catálogo. " +
                  "Probemos otra vez en un momento.";
      } else {
        mensaje = "Tuve un problema temporal. Volvé a intentarlo en un momento.";
      }
      agregarMensaje("bot", mensaje);
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
  const confirmOverlay   = document.getElementById("chat-confirm-overlay");
  const confirmOkBtn     = document.getElementById("chat-confirm-ok");
  const confirmCancelBtn = document.getElementById("chat-confirm-cancel");

  function mostrarConfirm() {
    // Si hubo conversación real, mostrar feedback antes de confirmar cierre
    if (historia.length > 1) {
      mostrarFeedbackPopup(() => {
        confirmOverlay.removeAttribute("aria-hidden");
        confirmOkBtn.focus();
      });
    } else {
      confirmOverlay.removeAttribute("aria-hidden");
      confirmOkBtn.focus();
    }
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

  // ── Feedback popup ──────────────────────────────────────────────────────
  const fbOverlay   = document.getElementById("chat-feedback-overlay");
  const fbSendBtn   = document.getElementById("chat-feedback-send");
  const fbSkipBtn   = document.getElementById("chat-feedback-skip");
  const fbStarsCont = document.getElementById("chat-feedback-stars");
  const starBtns    = fbStarsCont ? [...fbStarsCont.querySelectorAll(".star-btn")] : [];

  let fbStarSelected  = 0;
  let fbVisible       = false;
  let fbAfterClose    = null;

  function mostrarFeedbackPopup(afterClose = null) {
    if (!fbOverlay || fbVisible) return;
    fbVisible    = true;
    fbAfterClose = afterClose;
    fbStarSelected = 0;
    starBtns.forEach(b => b.classList.remove("lit"));
    fbSendBtn?.setAttribute("disabled", "");
    fbSendBtn && (fbSendBtn.textContent = "Enviar calificación");
    fbSendBtn?.classList.remove("fb-sent");
    fbOverlay.removeAttribute("aria-hidden");
  }

  function ocultarFeedbackPopup() {
    fbOverlay?.setAttribute("aria-hidden", "true");
    fbVisible = false;
    const cb  = fbAfterClose;
    fbAfterClose = null;
    if (cb) cb();
  }

  starBtns.forEach((btn, i) => {
    btn.addEventListener("mouseenter", () => {
      starBtns.forEach((b, j) => b.classList.toggle("lit", j <= i));
    });
    btn.addEventListener("mouseleave", () => {
      starBtns.forEach((b, j) => b.classList.toggle("lit", j < fbStarSelected));
    });
    btn.addEventListener("click", () => {
      fbStarSelected = i + 1;
      starBtns.forEach((b, j) => b.classList.toggle("lit", j < fbStarSelected));
      fbSendBtn?.removeAttribute("disabled");
    });
  });

  fbSendBtn?.addEventListener("click", async () => {
    if (!fbStarSelected) { ocultarFeedbackPopup(); return; }
    const sidSnap = sesionId;
    const voto    = fbStarSelected >= 4 ? "up" : "down";
    try {
      await fetch(`${API_BASE}/admin/aprendizaje/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sesion_id:       sidSnap,
          turno_index:     historia.length,
          voto,
          respuesta_agente: historia.findLast(h => h.tipo === "bot")?.texto || "",
        }),
      });
    } catch { /* silencioso */ }
    fbSendBtn.textContent = "¡Gracias! 🎉";
    fbSendBtn.classList.add("fb-sent");
    setTimeout(ocultarFeedbackPopup, 1500);
  });

  fbSkipBtn?.addEventListener("click", ocultarFeedbackPopup);

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
    const sku    = btn.dataset.sku;
    if (!sku) return;
    if (accion === "agregar") { agregarAlCarrito(btn, sku); return; }
    if (accion === "info") {
      const p = productoPorSku(sku);
      if (p) pdpAbrir(p);
      return;
    }
    const builder = MENSAJE_ACCION[accion];
    if (builder) enviarMensaje(builder(sku, nombrePorSku(sku)));
  });
})();
