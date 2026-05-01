"""BA 10.6/10.7 — eingebettetes HTML/CSS/JS für GET /founder/dashboard."""


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
  --warn: #fbbf24;
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
.grid { display: grid; gap: 1rem; }
@media (min-width: 900px) {
  .grid-2 { grid-template-columns: 1fr 1fr; }
}
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem;
}
.panel h2, .subh {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.subh { margin-top: 1rem; }
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
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  font-size: 0.8rem;
}
button.primary {
  background: var(--accent);
  border-color: #2563eb;
  color: #fff;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }
button.sm { padding: 0.3rem 0.5rem; font-size: 0.72rem; }
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
.out-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.4rem;
}
.muted { color: var(--muted); font-size: 0.8rem; }
.score { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.warn-list { margin: 0; padding-left: 1.1rem; color: #fcd34d; font-size: 0.85rem; }
details.fd-coll {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 0.75rem;
  padding: 0.35rem 0.75rem 0.75rem;
}
details.fd-coll > summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--text);
  padding: 0.35rem 0;
  list-style-position: outside;
}
details.fd-coll .coll-body { margin-top: 0.5rem; }
.pq-badge {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  vertical-align: middle;
}
.pq-badge.green { background: rgba(74,222,128,0.2); color: var(--ok); }
.pq-badge.yellow { background: rgba(251,191,36,0.2); color: var(--warn); }
.pq-badge.red { background: rgba(248,113,113,0.2); color: var(--danger); }
.pq-badge.neutral { background: rgba(139,156,179,0.2); color: var(--muted); }
table.data {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
table.data th, table.data td {
  border: 1px solid var(--border);
  padding: 0.4rem 0.5rem;
  text-align: left;
}
table.data th { background: var(--bg); color: var(--muted); }
.prompt-lab-head {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
  margin-bottom: 0.75rem;
}
.prompt-lab-head > div { flex: 1; min-width: 140px; }
.prompt-lab-head label { margin-bottom: 0.2rem; }
.pl-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
@media (max-width: 700px) {
  .pl-grid { grid-template-columns: 1fr; }
}
.pl-col {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem;
  background: var(--bg);
  max-height: 360px;
  overflow-y: auto;
}
.pl-col h4 { margin: 0 0 0.5rem; font-size: 0.75rem; color: var(--muted); }
.pl-scene {
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.72rem;
}
.pl-scene:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
</style>
</head>
<body>
<header>
  <h1>Founder Dashboard</h1>
  <p>Read-only Cockpit · Story-Engine per fetch · BA 10.7 (ohne Auth / Firestore / externe Provider)</p>
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
      <p class="muted">Templates: GET /story-engine/template-selector (beim Laden).</p>
    </section>
    <section class="panel">
      <h2>Actions</h2>
      <p class="muted">POST-Body = ExportPackageRequest (BA 10.3–10.5).</p>
      <div class="actions">
        <button type="button" class="primary" id="btn-export">Build Export Package</button>
        <button type="button" id="btn-preview">Preview Founder Metrics</button>
        <button type="button" id="btn-readiness">Provider Readiness</button>
        <button type="button" id="btn-optimize">Optimize Provider Prompts</button>
        <button type="button" id="btn-ctr">Thumbnail CTR</button>
        <button type="button" id="btn-formats">Export Formats</button>
      </div>
      <p class="muted" style="margin-top:0.75rem">Batch Template Compare lädt alle IDs aus dem Template-Selector und ruft nacheinander Preview + Readiness auf.</p>
      <div class="actions">
        <button type="button" id="btn-batch-compare">Batch Template Compare</button>
        <span class="muted" id="batch-status"></span>
      </div>
    </section>
  </div>

  <details class="fd-coll" open>
    <summary>Export Package (roh)</summary>
    <div class="coll-body">
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-export-full">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-export-full" data-dlname="export-package.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-export-full" data-dlname="export-package.txt">TXT</button>
      </div>
      <pre class="out" id="out-export-full">—</pre>
    </div>
  </details>

  <details class="fd-coll" open>
    <summary>Preview (Hook + Prompt Quality)</summary>
    <div class="coll-body grid grid-2">
      <div class="panel" style="margin:0">
        <h2>Hook Preview</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-hook">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-hook" data-dlname="hook-preview.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-hook" data-dlname="hook-preview.txt">TXT</button>
        </div>
        <pre class="out" id="out-hook">—</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>Prompt Quality Score <span id="pq-badge" class="pq-badge neutral" title="Farbe aus numerischem Preview-Score (≥70 grün, 40–69 gelb, &lt;40 rot); Export = Report.">—</span></h2>
        <div class="score" id="out-pq-score">—</div>
        <div class="out-toolbar" style="margin-top:0.5rem">
          <button type="button" class="sm tb-copy" data-pre="out-pq-detail">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-pq-detail" data-dlname="prompt-quality.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-pq-detail" data-dlname="prompt-quality.txt">TXT</button>
        </div>
        <pre class="out" id="out-pq-detail" style="max-height:160px">—</pre>
      </div>
    </div>
  </details>

  <details class="fd-coll" open>
    <summary>Provider Readiness</summary>
    <div class="coll-body">
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-readiness">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-readiness" data-dlname="provider-readiness.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-readiness" data-dlname="provider-readiness.txt">TXT</button>
      </div>
      <pre class="out" id="out-readiness">—</pre>
    </div>
  </details>

  <details class="fd-coll" open>
    <summary>Provider Optimize (Leonardo / OpenAI / Kling + Shotlists)</summary>
    <div class="coll-body grid grid-2">
      <div class="panel" style="margin:0">
        <h2>Leonardo Prompts</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-leo">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-leo" data-dlname="leonardo-prompts.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-leo" data-dlname="leonardo-prompts.txt">TXT</button>
        </div>
        <pre class="out" id="out-leo">—</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>OpenAI Prompts</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-openai">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-openai" data-dlname="openai-prompts.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-openai" data-dlname="openai-prompts.txt">TXT</button>
        </div>
        <pre class="out" id="out-openai">—</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>Kling Motion Prompts</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-kling">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-kling" data-dlname="kling-prompts.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-kling" data-dlname="kling-prompts.txt">TXT</button>
        </div>
        <pre class="out" id="out-kling">—</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>CapCut Shotlist</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-capcut">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-capcut" data-dlname="capcut-shotlist.json">JSON</button>
          <button type="button" class="sm tb-csv" data-pre="out-capcut" data-dlname="capcut-shotlist.csv">CSV</button>
        </div>
        <pre class="out" id="out-capcut">—</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>CSV Shotlist</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-csv">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-csv" data-dlname="csv-shotlist.json">JSON</button>
          <button type="button" class="sm tb-csv" data-pre="out-csv" data-dlname="csv-shotlist.csv">CSV</button>
        </div>
        <pre class="out" id="out-csv">—</pre>
      </div>
    </div>
  </details>

  <details class="fd-coll" open>
    <summary>Thumbnail CTR</summary>
    <div class="coll-body grid grid-2">
      <div class="panel" style="margin:0">
        <h2>Thumbnail CTR Score</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-ctr-raw">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-ctr-raw" data-dlname="thumbnail-ctr.json">JSON</button>
        </div>
        <div class="score" id="out-ctr">—</div>
        <pre class="out" id="out-ctr-raw" style="display:none">—</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>Thumbnail Variants</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-thumb-var">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-thumb-var" data-dlname="thumbnail-variants.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-thumb-var" data-dlname="thumbnail-variants.txt">TXT</button>
        </div>
        <pre class="out" id="out-thumb-var">—</pre>
      </div>
    </div>
  </details>

  <details class="fd-coll" open>
    <summary>Batch Template Compare</summary>
    <div class="coll-body">
      <p class="muted">readiness_score = Mittelwert aus scores.leonardo, scores.kling, scores.openai (Provider Readiness).</p>
      <div style="overflow-x:auto">
        <table class="data" id="batch-table">
          <thead>
            <tr>
              <th>template_id</th>
              <th>prompt_quality_score</th>
              <th>readiness_score</th>
              <th>thumbnail_strength</th>
            </tr>
          </thead>
          <tbody id="batch-tbody"></tbody>
        </table>
      </div>
    </div>
  </details>

  <details class="fd-coll" open>
    <summary>Prompt Lab (Side-by-side)</summary>
    <div class="coll-body">
      <p class="muted">Quelle: zuletzt „Optimize Provider Prompts“, sonst Stub-Prompts aus Export-Paket.</p>
      <div class="prompt-lab-head">
        <div>
          <label for="lab-left">Links</label>
          <select id="lab-left">
            <option value="leonardo">Leonardo</option>
            <option value="openai">OpenAI</option>
            <option value="kling">Kling</option>
          </select>
        </div>
        <div>
          <label for="lab-right">Rechts</label>
          <select id="lab-right">
            <option value="leonardo">Leonardo</option>
            <option value="openai" selected>OpenAI</option>
            <option value="kling">Kling</option>
          </select>
        </div>
        <div>
          <label>&nbsp;</label>
          <button type="button" class="sm" id="lab-refresh">Vergleich aktualisieren</button>
        </div>
      </div>
      <div class="pl-grid" id="prompt-lab-cols">
        <div class="pl-col" id="lab-col-left"><h4>Links</h4><div id="lab-body-left"></div></div>
        <div class="pl-col" id="lab-col-right"><h4>Rechts</h4><div id="lab-body-right"></div></div>
      </div>
    </div>
  </details>

  <details class="fd-coll">
    <summary>Export Formats Registry</summary>
    <div class="coll-body">
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-formats">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-formats" data-dlname="export-formats.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-formats" data-dlname="export-formats.txt">TXT</button>
      </div>
      <pre class="out" id="out-formats" style="max-height:200px">—</pre>
    </div>
  </details>

  <section class="panel" style="margin-top:1rem">
    <h2>Warning Center</h2>
    <ul class="warn-list" id="out-warnings"></ul>
  </section>
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
  let lastCtrPayload = null;
  let lastNumericPq = null;
  let templateIds = [];
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

  function getPreText(preId) {
    const el = $(preId);
    return el ? el.textContent : "";
  }

  function downloadText(filename, mime, text) {
    const blob = new Blob([text], { type: mime + ";charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function jsonArrayFromPre(preId) {
    const t = getPreText(preId).trim();
    if (!t || t === "—") return null;
    try { return JSON.parse(t); } catch (e) { return null; }
  }

  function arrayToCsv(rows) {
    if (!rows || !rows.length) return "";
    const keys = Object.keys(rows[0]);
    const esc = function(v) {
      const s = v == null ? "" : String(v);
      if (/[",\\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
      return s;
    };
    return keys.join(",") + "\\n" + rows.map(function(r) {
      return keys.map(function(k) { return esc(r[k]); }).join(",");
    }).join("\\n");
  }

  function updatePqBadge() {
    const badge = $("pq-badge");
    if (!badge) return;
    badge.className = "pq-badge neutral";
    badge.textContent = "—";
    if (lastNumericPq != null && !isNaN(lastNumericPq)) {
      var n = lastNumericPq;
      badge.textContent = String(n);
      if (n >= 70) { badge.className = "pq-badge green"; }
      else if (n >= 40) { badge.className = "pq-badge yellow"; }
      else { badge.className = "pq-badge red"; }
    } else {
      badge.textContent = "Report";
    }
  }

  function readinessAggregate(scores) {
    if (!scores) return null;
    var a = (Number(scores.leonardo) || 0) + (Number(scores.kling) || 0) + (Number(scores.openai) || 0);
    return Math.round(a / 3);
  }

  function getPromptBundle() {
    if (lastOptimize && lastOptimize.optimized_prompts) {
      return { kind: "opt", p: lastOptimize.optimized_prompts };
    }
    if (lastExport && lastExport.provider_prompts) {
      return { kind: "stub", p: lastExport.provider_prompts };
    }
    return null;
  }

  function sceneBlockText(kind, row, providerKey) {
    if (!row) return "(keine Szene)";
    if (kind === "opt" && providerKey === "kling") {
      return (row.motion_prompt || "") + "\\n---\\n" + (row.keyframe_positive || "");
    }
    if (kind === "opt") {
      return (row.positive_optimized || row.positive_expanded || "");
    }
    return row.positive_expanded || "";
  }

  function rowsForProvider(bundle, key) {
    if (!bundle || !bundle.p) return [];
    var arr = bundle.p[key];
    return Array.isArray(arr) ? arr : [];
  }

  function renderPromptLab() {
    var bundle = getPromptBundle();
    var lk = $("lab-left").value;
    var rk = $("lab-right").value;
    $("lab-col-left").querySelector("h4").textContent = "Links · " + lk;
    $("lab-col-right").querySelector("h4").textContent = "Rechts · " + rk;
    var leftBody = $("lab-body-left");
    var rightBody = $("lab-body-right");
    leftBody.innerHTML = "";
    rightBody.innerHTML = "";
    if (!bundle) {
      leftBody.textContent = "—";
      rightBody.textContent = "—";
      return;
    }
    var L = rowsForProvider(bundle, lk);
    var R = rowsForProvider(bundle, rk);
    var n = Math.max(L.length, R.length, 1);
    for (var i = 0; i < n; i++) {
      var sn = i + 1;
      var divL = document.createElement("div");
      divL.className = "pl-scene";
      divL.innerHTML = "<strong>Szene " + sn + "</strong><pre style='margin:0.35rem 0 0;white-space:pre-wrap;font-size:0.7rem'>" +
        escapeHtml(sceneBlockText(bundle.kind, L[i], lk)) + "</pre>";
      leftBody.appendChild(divL);
      var divR = document.createElement("div");
      divR.className = "pl-scene";
      divR.innerHTML = "<strong>Szene " + sn + "</strong><pre style='margin:0.35rem 0 0;white-space:pre-wrap;font-size:0.7rem'>" +
        escapeHtml(sceneBlockText(bundle.kind, R[i], rk)) + "</pre>";
      rightBody.appendChild(divR);
    }
  }

  function escapeHtml(s) {
    if (!s) return "";
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  document.querySelector("main").addEventListener("click", function(ev) {
    var t = ev.target;
    if (!t || !t.getAttribute) return;
    var preId = t.getAttribute("data-pre");
    if (!preId) return;
    var txt = getPreText(preId);
    if (t.classList.contains("tb-copy")) {
      if (!txt || txt === "—") return;
      navigator.clipboard.writeText(txt).then(function() {
        t.textContent = "OK";
        setTimeout(function() { t.textContent = "Copy"; }, 1200);
      }).catch(function() { showError("Clipboard nicht verfügbar"); });
      return;
    }
    var name = t.getAttribute("data-dlname") || "download.txt";
    if (t.classList.contains("tb-json")) {
      var j = txt;
      try {
        var parsed = JSON.parse(txt);
        j = JSON.stringify(parsed, null, 2);
      } catch (e1) {}
      downloadText(name, "application/json", j);
      return;
    }
    if (t.classList.contains("tb-txt")) {
      downloadText(name, "text/plain", txt);
      return;
    }
    if (t.classList.contains("tb-csv")) {
      var rows = jsonArrayFromPre(preId);
      if (!rows) { showError("Kein JSON-Array für CSV"); return; }
      downloadText(name, "text/csv", arrayToCsv(rows));
    }
  });

  async function loadTemplates() {
    try {
      const data = await fetchJson("/story-engine/template-selector", { method: "GET" });
      templateIds = (data.templates || []).map(function(x) { return x.template_id; });
      const sel = $("fd-template");
      sel.innerHTML = "";
      (data.templates || []).forEach(function(t){
        const o = document.createElement("option");
        o.value = t.template_id;
        o.textContent = (t.label || t.template_id) + " (" + t.template_id + ")";
        sel.appendChild(o);
      });
      if (!sel.options.length) {
        templateIds = ["generic","true_crime"];
        ["generic","true_crime"].forEach(function(id){
          const o = document.createElement("option");
          o.value = id; o.textContent = id; sel.appendChild(o);
        });
      }
    } catch (e) {
      showError(String(e.message || e));
      templateIds = ["generic","true_crime"];
      const sel = $("fd-template");
      sel.innerHTML = "";
      ["generic","true_crime"].forEach(function(id){
        const o = document.createElement("option");
        o.value = id; o.textContent = id; sel.appendChild(o);
      });
    }
  }

  $("fd-chapters").value = JSON.stringify(DEFAULT_CHAPTERS, null, 2);

  $("lab-left").addEventListener("change", renderPromptLab);
  $("lab-right").addEventListener("change", renderPromptLab);
  $("lab-refresh").addEventListener("click", renderPromptLab);

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
      lastNumericPq = null;
      updatePqBadge();
      setOut("out-export-full", data);
      setOut("out-hook", data.hook || null);
      const pq = data.prompt_quality || (data.scene_prompts && data.scene_prompts.prompt_quality);
      if (pq) {
        $("out-pq-score").textContent = "(Report)";
        setOut("out-pq-detail", pq);
      } else { $("out-pq-score").textContent = "—"; setOut("out-pq-detail", null); }
      mergeWarnings(data.warnings || []);
      renderPromptLab();
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
      lastNumericPq = data.prompt_quality_score;
      updatePqBadge();
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
      setOut("out-openai", op.openai || []);
      setOut("out-kling", op.kling || []);
      setOut("out-capcut", data.capcut_shotlist || []);
      setOut("out-csv", data.csv_shotlist || []);
      setOut("out-thumb-var", data.thumbnail_variants || []);
      mergeWarnings(data.warnings || []);
      renderPromptLab();
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
      lastCtrPayload = data;
      $("out-ctr").textContent = String(data.ctr_score);
      setOut("out-ctr-raw", data);
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

  $("btn-batch-compare").onclick = async function(){
    var btn = $("btn-batch-compare");
    var st = $("batch-status");
    var tbody = $("batch-tbody");
    tbody.innerHTML = "";
    clearWarnings();
    if (!templateIds.length) {
      showError("Keine Template-IDs geladen.");
      return;
    }
    btn.disabled = true;
    st.textContent = "Läuft…";
    try {
      var base = buildExportBody();
      for (var i = 0; i < templateIds.length; i++) {
        var tid = templateIds[i];
        st.textContent = "Template " + (i + 1) + "/" + templateIds.length + ": " + tid;
        var body = Object.assign({}, base, { video_template: tid });
        var prev = await fetchJson("/story-engine/export-package/preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        var ready = await fetchJson("/story-engine/provider-readiness", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        var rs = readinessAggregate(ready.scores);
        var tr = document.createElement("tr");
        tr.innerHTML = "<td>" + escapeHtml(tid) + "</td><td>" + String(prev.prompt_quality_score) +
          "</td><td>" + String(rs != null ? rs : "—") + "</td><td>" + escapeHtml(prev.thumbnail_strength) + "</td>";
        tbody.appendChild(tr);
      }
      st.textContent = "Fertig (" + templateIds.length + " Zeilen).";
    } catch (e) {
      st.textContent = "";
      showError(String(e.message || e));
    } finally {
      btn.disabled = false;
    }
  };

  loadTemplates().then(function() { renderPromptLab(); });
  updatePqBadge();
})();
</script>
</body>
</html>"""
