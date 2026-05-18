/* =====================================================
   ADMIN DASHBOARD — logic
   ===================================================== */

const API = "/api";
const REFRESH_INTERVAL = 30; // segundos

let dias = 7;
let refreshTimer = null;
let countdown = REFRESH_INTERVAL;
let charts = {};

// ---- Utilidades ----

async function fetchJSON(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

function fmt(n, decimals = 0) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return Number(n).toLocaleString("es-BO", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function pct(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return fmt(n, 1) + "%";
}

function ms(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
  return fmt(n) + " ms";
}

function colorClass(value, warnThreshold, errThreshold) {
  if (value === null || value === undefined) return "";
  if (value >= errThreshold) return "text-err";
  if (value >= warnThreshold) return "text-warn";
  return "text-ok";
}

// ---- Tab management ----

function switchTab(tabId) {
  document.querySelectorAll(".admin-tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });
  document.querySelectorAll(".admin-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === `panel-${tabId}`);
  });
  // Resize charts when tab becomes visible (Chart.js needs visible canvas)
  setTimeout(() => {
    Object.values(charts).forEach(c => c?.resize?.());
  }, 50);
}

// ---- Days selector ----

function setDias(d) {
  dias = d;
  document.querySelectorAll(".admin-day-btn").forEach(btn => {
    btn.classList.toggle("active", Number(btn.dataset.dias) === d);
  });
  loadAll();
}

// ---- Auto-refresh ----

function startRefreshTimer() {
  clearInterval(refreshTimer);
  countdown = REFRESH_INTERVAL;
  updateCountdown();
  refreshTimer = setInterval(() => {
    countdown--;
    updateCountdown();
    if (countdown <= 0) {
      countdown = REFRESH_INTERVAL;
      loadAll();
    }
  }, 1000);
}

function updateCountdown() {
  const el = document.getElementById("refresh-countdown");
  if (el) el.textContent = `${countdown}s`;
}

// ---- Chart helpers ----

const PALETTE = [
  "#e11d48", "#3b82f6", "#10b981", "#f59e0b",
  "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
];

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

function barChart(id, labels, data, opts = {}) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  charts[id] = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: opts.colors || PALETTE.slice(0, data.length),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      indexAxis: opts.horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ${fmt(ctx.raw)}` } },
      },
      scales: {
        x: { grid: { color: "rgba(0,0,0,.06)" }, ticks: { font: { size: 12 } } },
        y: { grid: { color: "rgba(0,0,0,.06)" }, ticks: { font: { size: 12 } } },
      },
    },
  });
}

function donutChart(id, labels, data) {
  destroyChart(id);
  const ctx = document.getElementById(id);
  if (!ctx) return;
  charts[id] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data, backgroundColor: PALETTE, borderWidth: 2, borderColor: "#fff" }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 12 }, boxWidth: 12, padding: 12 } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${fmt(ctx.raw)}` } },
      },
    },
  });
}

// ---- PANEL: Métricas ----

async function loadMetricas() {
  const panel = document.getElementById("panel-metricas");
  panel.innerHTML = `<div class="skeleton" style="height:120px;margin-bottom:16px"></div>
    <div class="skeleton" style="height:120px;margin-bottom:16px"></div>
    <div class="skeleton" style="height:280px"></div>`;

  const data = await fetchJSON(`/metricas/dashboard?dias=${dias}`);
  // Normalizar por_ruta: puede ser array [{ruta,turnos}] o dict {ruta:n}
  const porRutaNorm = Array.isArray(data.por_ruta)
    ? Object.fromEntries(data.por_ruta.map(r => [r.ruta, r.turnos ?? r.total ?? 0]))
    : (data.por_ruta || {});

  panel.innerHTML = `
    <p class="admin-section-title">Resumen (últimos ${data.dias} días)</p>
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-icon">💬</span>
        <span class="kpi-value">${fmt(data.turnos)}</span>
        <span class="kpi-label">Turnos totales</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">👥</span>
        <span class="kpi-value">${fmt(data.sesiones)}</span>
        <span class="kpi-label">Sesiones</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">🛒</span>
        <span class="kpi-value text-ok">${fmt(data.sesiones_con_orden)}</span>
        <span class="kpi-label">Con orden</span>
        <span class="kpi-sub">${pct(data.pct_sesiones_cerraron)} conversión</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">⚠️</span>
        <span class="kpi-value ${colorClass(data.pct_turnos_con_mentiras, 5, 15)}">${pct(data.pct_turnos_con_mentiras)}</span>
        <span class="kpi-label">% con alucinaciones</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">⚡</span>
        <span class="kpi-value ${colorClass(data.avg_ms, 5000, 10000)}">${ms(data.avg_ms)}</span>
        <span class="kpi-label">Latencia promedio</span>
        <span class="kpi-sub">P95: ${ms(data.p95_ms)}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">🔍</span>
        <span class="kpi-value ${colorClass(data.pct_sin_resultado, 20, 30)}">${pct(data.pct_sin_resultado)}</span>
        <span class="kpi-label">Sin resultado</span>
        ${data.alerta_sin_resultado ? '<span class="kpi-sub text-err">⚠ alerta activa</span>' : ''}
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">📞</span>
        <span class="kpi-value ${colorClass(data.pct_derivacion, 10, 15)}">${pct(data.pct_derivacion)}</span>
        <span class="kpi-label">Derivación humano</span>
        ${data.alerta_derivacion ? '<span class="kpi-sub text-err">⚠ alerta activa</span>' : ''}
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">📊</span>
        <span class="kpi-value">${ms(data.p50_ms)}</span>
        <span class="kpi-label">Latencia P50</span>
      </div>
    </div>

    <p class="admin-section-title">Distribución por ruta</p>
    <div class="charts-grid">
      <div class="chart-card" style="grid-column: span 2;">
        <div class="chart-card-title">Turnos por ruta</div>
        <div class="chart-wrap-tall"><canvas id="chart-rutas"></canvas></div>
      </div>
    </div>

    <p class="admin-section-title">Categorías y ciudades</p>
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-card-title">Top categorías buscadas</div>
        <div class="chart-wrap-tall"><canvas id="chart-categorias"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-card-title">Top ciudades</div>
        <div class="chart-wrap-tall"><canvas id="chart-ciudades"></canvas></div>
      </div>
    </div>
  `;

  // Rutas chart
  if (porRutaNorm && Object.keys(porRutaNorm).length) {
    const labels = Object.keys(porRutaNorm);
    const values = Object.values(porRutaNorm);
    barChart("chart-rutas", labels, values, { colors: PALETTE });
  }

  // Categorías
  if (data.top_categorias?.length) {
    const labels = data.top_categorias.map(r => r.categoria || r[0] || "?");
    const values = data.top_categorias.map(r => r.turnos ?? r.total ?? r[1] ?? 0);
    barChart("chart-categorias", labels, values, { horizontal: true, colors: ["#3b82f6"] });
  } else {
    document.getElementById("chart-categorias").parentElement.innerHTML =
      '<div class="empty-state"><div class="empty-icon">📂</div><p>Sin datos de categorías</p></div>';
  }

  // Ciudades
  if (data.top_ciudades?.length) {
    const labels = data.top_ciudades.map(r => r.ciudad || r[0] || "?");
    const values = data.top_ciudades.map(r => r.total || r[1] || 0);
    barChart("chart-ciudades", labels, values, { horizontal: true, colors: ["#10b981"] });
  } else {
    document.getElementById("chart-ciudades").parentElement.innerHTML =
      '<div class="empty-state"><div class="empty-icon">🌍</div><p>Sin datos de ciudades</p></div>';
  }
}

// ---- PANEL: Alertas ----

async function loadAlertas() {
  const panel = document.getElementById("panel-alertas");
  panel.innerHTML = `<div class="skeleton" style="height:100px;margin-bottom:12px"></div>
    <div class="skeleton" style="height:80px;margin-bottom:12px"></div>
    <div class="skeleton" style="height:80px"></div>`;

  const [alertasData, cbData] = await Promise.all([
    fetchJSON("/metricas/alertas?dias=1"),
    fetchJSON("/health/circuit-breaker"),
  ]);

  const cbEstado = (cbData.estado || "cerrado").toLowerCase();
  const cbDescriptions = {
    cerrado: "LLM respondiendo con normalidad. Sin fallos recientes.",
    abierto: "LLM con fallos consecutivos. Usando respuesta de fallback.",
    semiabierto: "Probando recuperación del LLM. Un request de prueba activo.",
  };

  let alertasHtml = "";
  if (alertasData.ok) {
    alertasHtml = `
      <div class="alert-card ok">
        <div class="alert-icon">✅</div>
        <div class="alert-body">
          <div class="alert-title">Sin alertas activas</div>
          <div class="alert-desc">Todos los indicadores dentro de umbrales normales.</div>
        </div>
      </div>`;
  } else {
    alertasHtml = (alertasData.alertas || []).map(a => `
      <div class="alert-card ${a.tipo === 'derivacion_alta' ? 'warn' : 'err'}">
        <div class="alert-icon">${a.tipo === 'derivacion_alta' ? '📞' : '🔍'}</div>
        <div class="alert-body">
          <div class="alert-title">${a.tipo === 'derivacion_alta' ? 'Derivación alta' : 'Muchas búsquedas sin resultado'}</div>
          <div class="alert-desc">${a.mensaje}</div>
        </div>
        <div class="alert-value">${fmt(a.valor, 1)}%</div>
      </div>`).join("");
  }

  panel.innerHTML = `
    <p class="admin-section-title">Estado del LLM</p>
    <div class="cb-card">
      <div class="cb-indicator ${cbEstado}"></div>
      <div>
        <div class="cb-label">Circuit Breaker — Ollama</div>
        <div class="cb-estado ${cbEstado}">${cbEstado.toUpperCase()}</div>
      </div>
      <div class="cb-desc">${cbDescriptions[cbEstado] || ""}</div>
    </div>

    <p class="admin-section-title">Alertas (últimas 24h)</p>
    <div class="alerts-grid">${alertasHtml}</div>
  `;
}

// ---- PANEL: Aprendizaje ----

async function loadAprendizaje() {
  const panel = document.getElementById("panel-aprendizaje");
  panel.innerHTML = `<div class="skeleton" style="height:120px;margin-bottom:16px"></div>
    <div class="skeleton" style="height:280px"></div>`;

  const data = await fetchJSON("/admin/aprendizaje/dashboard");

  const feedback = data.feedback || {};
  const upVotes = feedback.up || 0;
  const downVotes = feedback.down || 0;
  const totalFb = upVotes + downVotes;
  const satisfaccion = totalFb > 0 ? (upVotes / totalFb * 100) : null;

  const synonyms = data.top_synonyms_pendientes || [];
  const curadas = data.ultimas_curadas_activas || [];
  const fallos = data.fallos_por_razon || {};

  const synonymsRows = synonyms.length
    ? synonyms.map(s => `
        <tr>
          <td>${s.termino}</td>
          <td><span class="badge-pill blue">${s.ocurrencias}</span></td>
          <td style="color:var(--muted);font-size:12px">#${s.id}</td>
        </tr>`).join("")
    : `<tr><td colspan="3" style="text-align:center;color:var(--muted);padding:20px">Sin sinónimos pendientes</td></tr>`;

  const curadasRows = curadas.length
    ? curadas.map(c => `
        <tr>
          <td>${c.etiqueta || "—"}</td>
          <td><span class="badge-pill green">${fmt(c.score, 2)}</span></td>
          <td style="font-size:12px;color:var(--muted);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c.cliente || "—"}</td>
        </tr>`).join("")
    : `<tr><td colspan="3" style="text-align:center;color:var(--muted);padding:20px">Sin conversaciones curadas</td></tr>`;

  const fallosEntries = Object.entries(fallos);
  const fallosRows = fallosEntries.length
    ? [...fallosEntries].toSorted((a, b) => b[1] - a[1]).map(([r, n]) => `
        <tr>
          <td style="font-family:monospace;font-size:12px">${r}</td>
          <td><span class="badge-pill">${n}</span></td>
        </tr>`).join("")
    : `<tr><td colspan="2" style="text-align:center;color:var(--muted);padding:20px">Sin fallos registrados</td></tr>`;

  panel.innerHTML = `
    <p class="admin-section-title">Feedback del usuario</p>
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-icon">👍</span>
        <span class="kpi-value text-ok">${fmt(upVotes)}</span>
        <span class="kpi-label">Votos positivos</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">👎</span>
        <span class="kpi-value text-err">${fmt(downVotes)}</span>
        <span class="kpi-label">Votos negativos</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">😊</span>
        <span class="kpi-value ${satisfaccion == null ? '' : colorClass(100 - satisfaccion, 20, 40)}">${satisfaccion == null ? '—' : pct(satisfaccion)}</span>
        <span class="kpi-label">Satisfacción</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">🔤</span>
        <span class="kpi-value text-warn">${fmt(synonyms.length)}</span>
        <span class="kpi-label">Sinónimos pendientes</span>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px">
      <div class="table-card">
        <div class="table-card-header">Sinónimos candidatos <span style="color:var(--muted);font-weight:400">top 10</span></div>
        <table><thead><tr><th>Término</th><th>Ocurrencias</th><th>ID</th></tr></thead>
        <tbody>${synonymsRows}</tbody></table>
      </div>
      <div class="table-card">
        <div class="table-card-header">Fallos por razón</div>
        <table><thead><tr><th>Razón</th><th>Cuenta</th></tr></thead>
        <tbody>${fallosRows}</tbody></table>
      </div>
    </div>

    <div class="table-card">
      <div class="table-card-header">Conversaciones doradas activas <span style="color:var(--muted);font-weight:400">top 10</span></div>
      <table><thead><tr><th>Etiqueta</th><th>Score</th><th>Muestra</th></tr></thead>
      <tbody>${curadasRows}</tbody></table>
    </div>
  `;
}

// ---- Load all panels ----

async function loadAll() {
  const tasks = [loadMetricas(), loadAlertas(), loadAprendizaje()];
  await Promise.allSettled(tasks);
  document.getElementById("last-updated").textContent =
    new Date().toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// ---- Init ----

document.addEventListener("DOMContentLoaded", () => {
  // Tabs
  document.querySelectorAll(".admin-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Days
  document.querySelectorAll(".admin-day-btn").forEach(btn => {
    btn.addEventListener("click", () => setDias(Number(btn.dataset.dias)));
  });

  // Manual refresh
  document.getElementById("btn-refresh").addEventListener("click", () => {
    countdown = REFRESH_INTERVAL;
    loadAll();
  });

  // Dark mode sync con index.html
  const saved = localStorage.getItem("theme");
  if (saved) document.documentElement.dataset.theme = saved;
  document.getElementById("theme-toggle")?.addEventListener("change", e => {
    const t = e.target.checked ? "dark" : "light";
    document.documentElement.dataset.theme = t;
    localStorage.setItem("theme", t);
  });
  if (saved === "dark") {
    const toggle = document.getElementById("theme-toggle");
    if (toggle) toggle.checked = true;
  }

  // Load initial data
  switchTab("metricas");
  loadAll();
  startRefreshTimer();
});
