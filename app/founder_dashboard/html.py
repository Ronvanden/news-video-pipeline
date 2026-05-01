"""BA 10.6 — eingebettetes HTML/CSS/JS für GET /founder/dashboard."""


def get_founder_dashboard_html() -> str:
    """Statisches Single-Page-Dashboard; clientseitige fetch-Calls zu /story-engine/*."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Founder Dashboard</title>
<style>
:root {
  --bg: #0f1419;
  --surface: #1a222d;
  --border: #2d3a4d;
  --text: #e7ecf3;
  --muted: #8b9cb3;
  --accent: #3d8bfd;
  --danger: #f87171;
  --ok: #4ade80;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.45;
  font-size: 15px;
}
header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
header h1 { margin: 0; font-size: 1.25rem; font-weight: 600; }
header p { margin: 0.35rem 0 0; color: var(--muted); font-size: 0.85rem; }
main { padding: 1rem 1.25rem 2rem; max-width: 1200px; margin: 0 auto; }
#error-bar {
  display: none;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: rgba(248,113,113,0.12);
  border: 1px solid var(--danger);
  color: #fecaca;
  white-space: pre-wrap;
  word-break: break-word;
}
#error-bar.visible { display: block; }
.grid {
  display: grid;
  gap: 1rem;
}
@media (min-width: 900px) {
  .grid-2 { grid-template-columns: 1fr 1fr; }
}
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem;
}
.panel h2 {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
label { display: block; margin-bottom: 0.35rem; color: var(--muted); font-size: 0.8rem; }
input[type="text"], input[type="number"], textarea, select {
  width: 100%;
  padding: 0.5rem 0.65rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  margin-bottom: 0.75rem;
}
textarea { min-height: 88px; resize: vertical; font-family: ui-monospace, monospace; font-size: 0.8rem; }
.row-check { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.row-check input { width: auto; margin: 0; }
.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
button {
  padding: 0.55rem 0.85rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  font-size: 0.85rem;
}
button.primary {
  background: var(--accent);
  border-color: #2563eb;
  color: #fff;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
pre.out {
  margin: 0;
  padding: 0.65rem;
  background: var(--bg);
  border-radius: 6px;
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 280px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.muted { color: var(--muted); font-size: 0.8rem; }
.score { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.warn-list { margin: 0; padding-left: 1.1rem; color: #fcd34d; font-size: 0.85rem; }
</style>
</head>
<body>
<header>
  <h1>Founder Dashboard</h1>
  <p>Read-only Cockpit · ruft bestehende Story-Engine-Endpunkte per fetch auf · V1 ohne Auth</p>
</header>
<main>
  <div id="error-bar" role="alert"></div>
  <div class="grid grid-2">
    <section class="panel">
      <h2>Input Panel</h2>
      <label for="fd-title">Titel / Thema (title)</label>
      <input type="text" id="fd-title" placeholder="Titel"/>
      <label for="fd-topic">Topic</label>
      <input type="text" id="fd-topic" placeholder="Kurzes Topic"/>
      <label for="fd-summary">Source summary</label>
      <textarea id="fd-summary" placeholder="Quell-Zusammenfassung"></textarea>
      <label for="fd-template">Template (video_template)</label>
      <select id="fd-template"></select>
      <label for="fd-duration">Duration (Minuten)</label>
      <input type="number" id="fd-duration" min="1" max="180" value="10"/>
      <label for="fd-provider">Provider profile</label>
      <select id="fd-provider">
        <option value="openai">openai</option>
        <option value="leonardo">leonardo</option>
        <option value="kling">kling</option>
      </select>
      <div class="row-check">
        <input type="checkbox" id="fd-lock" checked/>
        <label for="fd-lock" style="margin:0">Continuity lock</label>
      </div>
      <label for="fd-chapters">Kapitel (JSON)</label>
      <textarea id="fd-chapters" spellcheck="false"></textarea>
      <p class="muted">Template-Liste: GET /story-engine/template-selector (beim Laden).</p>
    </section>
    <section class="panel">
      <h2>Actions</h2>
      <p class="muted">POST-Body entspricht ExportPackageRequest (wie BA 10.3–10.5).</p>
      <div class="actions">
        <button type="button" class="primary" id="btn-export">Build Export Package</button>
        <button type="button" id="btn-preview">Preview Founder Metrics</button>
        <button type="button" id="btn-readiness">Provider Readiness</button>
        <button type="button" id="btn-optimize">Optimize Provider Prompts</button>
        <button type="button" id="btn-ctr">Thumbnail CTR</button>
        <button type="button" id="btn-formats">Export Formats</button>
      </div>
    </section>
  </div>
  <div class="grid grid-2" style="margin-top:1rem">
    <section class="panel">
      <h2>Hook Preview</h2>
      <pre class="out" id="out-hook">—</pre>
    </section>
    <section class="panel">
      <h2>Prompt Quality Score</h2>
      <div class="score" id="out-pq-score">—</div>
      <pre class="out" id="out-pq-detail" style="margin-top:0.5rem;max-height:160px">—</pre>
    </section>
    <section class="panel">
      <h2>Provider Readiness Scores</h2>
      <pre class="out" id="out-readiness">—</pre>
    </section>
    <section class="panel">
      <h2>Thumbnail CTR Score</h2>
      <div class="score" id="out-ctr">—</div>
      <h2 style="margin-top:1rem">Thumbnail Variants</h2>
      <pre class="out" id="out-thumb-var">—</pre>
    </section>
    <section class="panel">
      <h2>Leonardo Prompts</h2>
      <pre class="out" id="out-leo">—</pre>
    </section>
    <section class="panel">
      <h2>Kling Motion Prompts</h2>
      <pre class="out" id="out-kling">—</pre>
    </section>
    <section class="panel">
      <h2>CapCut Shotlist</h2>
      <pre class="out" id="out-capcut">—</pre>
    </section>
    <section class="panel">
      <h2>CSV Shotlist</h2>
      <pre class="out" id="out-csv">—</pre>
    </section>
    <section class="panel" style="grid-column:1/-1">
      <h2>Export Formats</h2>
      <pre class="out" id="out-formats" style="max-height:200px">—</pre>
    </section>
    <section class="panel" style="grid-column:1/-1">
      <h2>Warning Center</h2>
      <ul class="warn-list" id="out-warnings"></ul>
    </section>
  </div>
</main>
<script>
(function(){
  const DEFAULT_CHAPTERS = [
    {"title":"Kapitel 1","content":"Inhalt genug für eine Szene. ".repeat(8)},
    {"title":"Kapitel 2","content":"Weiterer Inhalt. ".repeat(10)}
  ];
  const $ = function(id){ return document.getElementById(id); };
  const err = $("error-bar");
  let lastExport = null;
  let lastOptimize = null;
  let warningsAcc = [];

  function showError(msg) {
    err.textContent = msg || "";
    err.classList.toggle("visible", !!msg);
  }
  function parseChapters() {
    const raw = $("fd-chapters").value.trim();
    if (!raw) return DEFAULT_CHAPTERS;
    try { return JSON.parse(raw); } catch (e) {
      throw new Error("Kapitel-JSON ungültig: " + e.message);
    }
  }
  function buildExportBody() {
    return {
      video_template: $("fd-template").value || "generic",
      duration_minutes: Math.min(180, Math.max(1, parseInt($("fd-duration").value, 10) || 10)),
      title: $("fd-title").value || "",
      topic: $("fd-topic").value || "",
      source_summary: $("fd-summary").value || "",
      provider_profile: $("fd-provider").value || "openai",
      continuity_lock: $("fd-lock").checked,
      chapters: parseChapters()
    };
  }
  function mergeWarnings(arr) {
    if (!arr || !arr.length) return;
    arr.forEach(function(w){
      if (w && warningsAcc.indexOf(w) < 0) warningsAcc.push(w);
    });
    renderWarnings();
  }
  function renderWarnings() {
    const ul = $("out-warnings");
    ul.innerHTML = "";
    warningsAcc.forEach(function(w){
      const li = document.createElement("li");
      li.textContent = w;
      ul.appendChild(li);
    });
  }
  function clearWarnings() { warningsAcc = []; renderWarnings(); }

  async function fetchJson(url, opts) {
    showError("");
    const r = await fetch(url, opts);
    const text = await r.text();
    let data;
    try { data = text ? JSON.parse(text) : null; } catch (e) {
      throw new Error(url + " — keine JSON-Antwort: " + text.slice(0, 200));
    }
    if (!r.ok) {
      const detail = data && (data.detail || data.message) ? JSON.stringify(data.detail || data.message) : text;
      throw new Error(r.status + " " + r.statusText + ": " + detail);
    }
    return data;
  }

  function setOut(id, obj) {
    $(id).textContent = obj == null ? "—" : (typeof obj === "string" ? obj : JSON.stringify(obj, null, 2));
  }

  async function loadTemplates() {
    try {
      const data = await fetchJson("/story-engine/template-selector", { method: "GET" });
      const sel = $("fd-template");
      sel.innerHTML = "";
      (data.templates || []).forEach(function(t){
        const o = document.createElement("option");
        o.value = t.template_id;
        o.textContent = (t.label || t.template_id) + " (" + t.template_id + ")";
        sel.appendChild(o);
      });
      if (!sel.options.length) {
        ["generic","true_crime"].forEach(function(id){
          const o = document.createElement("option");
          o.value = id; o.textContent = id; sel.appendChild(o);
        });
      }
    } catch (e) {
      showError(String(e.message || e));
      const sel = $("fd-template");
      sel.innerHTML = "";
      ["generic","true_crime"].forEach(function(id){
        const o = document.createElement("option");
        o.value = id; o.textContent = id; sel.appendChild(o);
      });
    }
  }

  $("fd-chapters").value = JSON.stringify(DEFAULT_CHAPTERS, null, 2);

  $("btn-export").onclick = async function(){
    clearWarnings();
    try {
      const body = buildExportBody();
      const data = await fetchJson("/story-engine/export-package", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      lastExport = data;
      setOut("out-hook", data.hook || null);
      const pq = data.prompt_quality || (data.scene_prompts && data.scene_prompts.prompt_quality);
      if (pq) {
        $("out-pq-score").textContent = "(Report) siehe Detail";
        setOut("out-pq-detail", pq);
      } else { $("out-pq-score").textContent = "—"; setOut("out-pq-detail", null); }
      mergeWarnings(data.warnings || []);
    } catch (e) { showError(String(e.message || e)); }
  };

  $("btn-preview").onclick = async function(){
    clearWarnings();
    try {
      const data = await fetchJson("/story-engine/export-package/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildExportBody())
      });
      setOut("out-hook", {
        hook_type: data.hook_type,
        hook_score: data.hook_score,
        template_id: data.template_id,
        export_ready: data.export_ready,
        readiness_status: data.readiness_status,
        top_warnings: data.top_warnings
      });
      $("out-pq-score").textContent = String(data.prompt_quality_score);
      setOut("out-pq-detail", { prompt_quality_score: data.prompt_quality_score, scene_count: data.scene_count });
      mergeWarnings(data.top_warnings || []);
    } catch (e) { showError(String(e.message || e)); }
  };

  $("btn-readiness").onclick = async function(){
    clearWarnings();
    try {
      const data = await fetchJson("/story-engine/provider-readiness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildExportBody())
      });
      setOut("out-readiness", data);
      mergeWarnings(data.warnings || []);
      mergeWarnings(data.blocking_issues || []);
    } catch (e) { showError(String(e.message || e)); }
  };

  $("btn-optimize").onclick = async function(){
    clearWarnings();
    try {
      const data = await fetchJson("/story-engine/provider-prompts/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildExportBody())
      });
      lastOptimize = data;
      const op = data.optimized_prompts || {};
      setOut("out-leo", op.leonardo || []);
      setOut("out-kling", op.kling || []);
      setOut("out-capcut", data.capcut_shotlist || []);
      setOut("out-csv", data.csv_shotlist || []);
      setOut("out-thumb-var", data.thumbnail_variants || []);
      mergeWarnings(data.warnings || []);
    } catch (e) { showError(String(e.message || e)); }
  };

  $("btn-ctr").onclick = async function(){
    clearWarnings();
    try {
      let hook = "";
      let thumb = "";
      const title = $("fd-title").value || "";
      const vt = $("fd-template").value || "generic";
      if (lastExport && lastExport.hook) hook = lastExport.hook.hook_text || "";
      if (lastExport && lastExport.thumbnail_prompt) thumb = lastExport.thumbnail_prompt;
      const body = {
        title: title,
        hook: hook,
        video_template: vt,
        thumbnail_prompt: thumb,
        chapters: parseChapters()
      };
      const data = await fetchJson("/story-engine/thumbnail-ctr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      $("out-ctr").textContent = String(data.ctr_score);
      setOut("out-thumb-var", data.thumbnail_variants || []);
      mergeWarnings(data.warnings || []);
    } catch (e) { showError(String(e.message || e)); }
  };

  $("btn-formats").onclick = async function(){
    clearWarnings();
    try {
      const data = await fetchJson("/story-engine/export-formats", { method: "GET" });
      setOut("out-formats", data);
      mergeWarnings(data.warnings || []);
    } catch (e) { showError(String(e.message || e)); }
  };

  loadTemplates();
})();
</script>
</body>
</html>"""
