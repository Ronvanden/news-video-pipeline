"""BA 10.6–11.2 — eingebettetes HTML/CSS/JS für GET /founder/dashboard."""


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
.intake-status { min-height: 1.2rem; margin: 0.45rem 0 0; font-size: 0.82rem; }
.intake-status.intake-status-success { color: var(--ok); font-weight: 600; }
.intake-status.intake-status-err { color: #fecaca; font-weight: 600; }
.intake-status.intake-status-info { color: var(--muted); }
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
button.is-loading {
  opacity: 1 !important;
  cursor: wait !important;
  border-color: var(--accent) !important;
  box-shadow: inset 0 0 0 1px rgba(61, 139, 253, 0.35);
}
button.is-success {
  background: rgba(74, 222, 128, 0.22) !important;
  border-color: var(--ok) !important;
  color: #bbf7d0 !important;
}
button.primary.is-success {
  background: rgba(74, 222, 128, 0.45) !important;
  color: #052e16 !important;
}
button.is-error {
  background: rgba(248, 113, 113, 0.22) !important;
  border-color: var(--danger) !important;
  color: #fecaca !important;
}
button.sm { padding: 0.3rem 0.5rem; font-size: 0.72rem; }
pre.out-empty, .score.out-empty, .lab-empty {
  color: var(--muted);
  font-style: italic;
  font-weight: normal;
}
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
.checklist-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}
.checklist-badge.ready { background: rgba(74,222,128,0.25); color: var(--ok); border: 1px solid var(--ok); }
.checklist-badge.partial { background: rgba(251,191,36,0.2); color: var(--warn); border: 1px solid var(--warn); }
.checklist-badge.blocked { background: rgba(248,113,113,0.2); color: #fecaca; border: 1px solid var(--danger); }
#prod-checklist-items { list-style: none; padding: 0; margin: 0.5rem 0 0; font-size: 0.82rem; }
#prod-checklist-items li { padding: 0.2rem 0; border-bottom: 1px solid var(--border); }
#prod-checklist-items li.ok { color: var(--ok); }
#prod-checklist-items li.no { color: var(--muted); }
.warn-grouped { margin-top: 0.5rem; }
.warn-group { margin-bottom: 1rem; border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 0.75rem; background: var(--bg); }
.warn-group h4 { margin: 0 0 0.35rem; font-size: 0.78rem; color: var(--muted); }
.warn-group ul { margin: 0; padding-left: 1.1rem; font-size: 0.8rem; color: #fde68a; }
.prompt-cards-wrap { margin-top: 1rem; }
.prompt-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
  background: var(--bg);
}
.prompt-card h3 { margin: 0 0 0.5rem; font-size: 0.85rem; color: var(--text); }
.pc-block { margin-bottom: 0.65rem; }
.pc-block label { font-size: 0.72rem; color: var(--muted); margin-bottom: 0.15rem; }
.pc-block pre {
  margin: 0.25rem 0 0;
  padding: 0.45rem;
  font-size: 0.7rem;
  background: var(--surface);
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 140px;
  overflow-y: auto;
}
.mode-toggle { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.mode-toggle button.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
body.raw-view #founder-human-layer,
body.dashboard-mode-operator #founder-human-layer { display: none !important; }
body.dashboard-mode-operator pre.out { max-height: 220px; }
.ba112-panel { margin-top: 1rem; }
.exec-scorecard {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.65rem 0.75rem;
  margin-bottom: 0.75rem;
  background: var(--bg);
}
.exec-scorecard .esc-overall {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
  padding-bottom: 0.45rem;
  border-bottom: 1px solid var(--border);
}
.exec-scorecard .esc-l { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.exec-scorecard .esc-val { font-size: 1.15rem; font-weight: 800; }
.exec-scorecard .esc-val.grade-go { color: var(--ok); }
.exec-scorecard .esc-val.grade-hold { color: var(--warn); }
.exec-scorecard .esc-val.grade-stop { color: var(--danger); }
.esc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
  gap: 0.4rem;
}
.esc-cell {
  text-align: center;
  padding: 0.35rem 0.25rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  font-size: 0.68rem;
  color: var(--muted);
}
.esc-grade { font-size: 1rem; font-weight: 800; color: var(--text); display: block; margin-top: 0.15rem; }
.opp-radar { margin: 0.5rem 0 0.75rem; }
.ba112-radar-title { margin: 0 0 0.45rem !important; }
.radar-bars { display: flex; flex-direction: column; gap: 0.38rem; }
.radar-row { display: flex; align-items: center; gap: 0.45rem; font-size: 0.72rem; }
.radar-row .radar-label { width: 6.75rem; flex-shrink: 0; color: var(--muted); }
.radar-track { flex: 1; height: 9px; background: var(--border); border-radius: 5px; overflow: hidden; min-width: 0; }
.radar-fill { height: 100%; width: 0%; border-radius: 5px; transition: width 0.2s ease; }
.radar-pct { width: 2.5rem; text-align: right; font-size: 0.68rem; color: var(--muted); flex-shrink: 0; }
.rewrite-rec-block { margin: 0.5rem 0 0.65rem; }
.rewrite-rec-block h3 { margin: 0 0 0.35rem; }
#rewrite-rec-list { margin: 0; padding-left: 1.1rem; font-size: 0.82rem; }
#rewrite-rec-list li { margin-bottom: 0.4rem; }
.repair-actions-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.35rem; align-items: center; }
.kill-switch-row {
  margin-top: 0.75rem;
  padding-top: 0.65rem;
  border-top: 1px solid var(--border);
}
.kill-switch-row label { display: flex; align-items: flex-start; gap: 0.45rem; cursor: pointer; font-size: 0.82rem; margin: 0; }
#fd-kill-switch-banner {
  display: none;
  margin-bottom: 0.5rem;
  padding: 0.45rem 0.65rem;
  border-radius: 6px;
  background: rgba(248,113,113,0.12);
  border: 1px solid var(--danger);
  font-size: 0.78rem;
  color: #fecaca;
}
#fd-kill-switch-banner.visible { display: block; }
.founder-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}
.fk-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.55rem 0.65rem;
}
.fk-card .fk-label { font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.fk-card .fk-val { font-size: 1.05rem; font-weight: 700; margin-top: 0.2rem; }
.strat-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0; }
.strat-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--border);
}
.strat-badge.high { background: rgba(74,222,128,0.18); color: var(--ok); border-color: rgba(74,222,128,0.5); }
.strat-badge.mid { background: rgba(251,191,36,0.15); color: var(--warn); }
.strat-badge.low { background: rgba(139,156,179,0.2); color: var(--muted); }
.nba-card {
  border-radius: 10px;
  padding: 0.65rem 0.85rem;
  margin: 0.5rem 0 0.75rem;
  font-weight: 700;
  font-size: 0.95rem;
  border: 1px solid var(--border);
  background: rgba(61,139,253,0.12);
}
.nba-card.produzieren { background: rgba(74,222,128,0.15); border-color: var(--ok); color: #bbf7d0; }
.nba-card.thumb { background: rgba(251,191,36,0.12); border-color: var(--warn); }
.nba-card.provider { background: rgba(248,113,113,0.12); border-color: var(--danger); color: #fecaca; }
.nba-card.hook { background: rgba(147,197,253,0.15); border-color: #93c5fd; }
.nba-card.verwerfen { background: rgba(75,85,99,0.35); color: #e5e7eb; }
.opp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; }
@media (max-width: 700px) { .opp-grid { grid-template-columns: 1fr; } }
.opp-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.65rem;
  background: var(--bg);
}
.opp-card h3 { margin: 0 0 0.4rem; font-size: 0.78rem; color: var(--muted); }
.opp-card ul { margin: 0; padding-left: 1.1rem; font-size: 0.8rem; }
.human-layer { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
.human-block { margin-bottom: 0.65rem; }
.human-block h4 { margin: 0 0 0.25rem; font-size: 0.75rem; color: var(--muted); }
.human-block p { margin: 0; font-size: 0.82rem; line-height: 1.4; color: var(--text); }
.pipe-timeline {
  list-style: none;
  padding: 0;
  margin: 0.75rem 0 1rem;
  border-left: 2px solid var(--border);
}
.pipe-timeline li.pipe-step {
  position: relative;
  padding: 0.35rem 0 0.35rem 1rem;
  margin-left: 0.35rem;
  font-size: 0.82rem;
  color: var(--muted);
}
.pipe-timeline li.pipe-step::before {
  content: "";
  position: absolute;
  left: -0.55rem;
  top: 0.55rem;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: var(--border);
}
.pipe-timeline li.pipe-step.pending { color: var(--muted); }
.pipe-timeline li.pipe-step.active { color: var(--accent); font-weight: 600; }
.pipe-timeline li.pipe-step.active::before { background: var(--accent); box-shadow: 0 0 0 3px rgba(61,139,253,0.25); }
.pipe-timeline li.pipe-step.done { color: var(--ok); }
.pipe-timeline li.pipe-step.done::before { background: var(--ok); }
.pipe-timeline li.pipe-step.err { color: var(--danger); }
.pipe-timeline li.pipe-step.err::before { background: var(--danger); }
.pipe-timeline .ps-msg { display: block; font-size: 0.72rem; font-weight: normal; margin-top: 0.15rem; color: var(--danger); }
.intake-type-row { margin-bottom: 0.75rem; }
</style>
</head>
<body>
<header>
  <h1>Founder Dashboard</h1>
  <p>Read-only Cockpit · Story-Engine per fetch · BA 11.0–11.2 Operator Clarity (ohne Auth / Firestore / externe Provider)</p>
</header>
<main>
  <div id="error-bar" role="alert"></div>

  <section class="panel" id="founder-strategic-summary">
    <h2>Founder Strategic Summary</h2>
    <div class="mode-toggle">
      <button type="button" id="btn-founder-mode" class="active" data-label="Founder Mode">Founder Mode</button>
      <button type="button" id="btn-operator-mode" data-label="Operator Mode">Operator Mode</button>
      <button type="button" id="btn-raw-mode" data-label="Raw Mode">Raw Mode</button>
    </div>
    <div class="founder-kpi-grid">
      <div class="fk-card"><div class="fk-label">Themenpotenzial</div><div class="fk-val" id="fk-potential">—</div></div>
      <div class="fk-card"><div class="fk-label">Produktionsstatus</div><div class="fk-val" id="fk-prod-status">—</div></div>
      <div class="fk-card"><div class="fk-label">Bester Provider</div><div class="fk-val" id="fk-best-provider">—</div></div>
      <div class="fk-card"><div class="fk-label">Risikostufe</div><div class="fk-val" id="fk-risk">—</div></div>
      <div class="fk-card" style="grid-column:1/-1"><div class="fk-label">Handlungsempfehlung</div><div class="fk-val" id="fk-handlung" style="font-size:0.9rem;font-weight:600">—</div></div>
    </div>
    <div class="strat-badges" id="strategic-badges-row" aria-label="Strategic Badges"></div>
    <div id="next-best-action" class="nba-card">Next Best Action: <span id="nba-text">—</span></div>
    <div class="opp-grid">
      <div class="opp-card" id="opp-chances-card">
        <h3>Opportunity · Top Chancen</h3>
        <ul id="opp-chances-list"><li class="muted">Noch keine Daten — Export / Preview ausführen.</li></ul>
      </div>
      <div class="opp-card" id="opp-weak-card">
        <h3>Weakness · Hauptschwächen</h3>
        <ul id="opp-weak-list"><li class="muted">Noch keine Daten.</li></ul>
      </div>
    </div>
    <div id="founder-human-layer" class="human-layer">
      <h2 class="subh">Human Translation Layer</h2>
      <div class="human-block"><h4>Hook</h4><p id="hum-hook">—</p></div>
      <div class="human-block"><h4>Prompt Quality</h4><p id="hum-pq">—</p></div>
      <div class="human-block"><h4>Provider Readiness</h4><p id="hum-readiness">—</p></div>
      <div class="human-block"><h4>Thumbnail CTR</h4><p id="hum-ctr">—</p></div>
    </div>
  </section>

  <section class="panel ba112-panel" id="coll-ba112-clarity">
    <h2>Operator Clarity (BA 11.2)</h2>
    <p class="muted ba112-founder-hint">Executive Scorecard, Rewrite-Hinweise, Schnell-Reparaturen und Opportunity Radar — alles aus bestehenden Dashboard-Daten abgeleitet (keine neuen API-Verträge).</p>
    <div id="fd-kill-switch-banner" role="status">Kill Switch aktiv — keine neuen Story-Engine-Requests bis zur Deaktivierung.</div>
    <div id="exec-scorecard" class="exec-scorecard" aria-label="Executive Scorecard">
      <div class="esc-overall">
        <span class="esc-l">Entscheidung (Go / Hold / Stop)</span>
        <span id="esc-overall" class="esc-val">—</span>
      </div>
      <div class="esc-grid">
        <div class="esc-cell"><span class="esc-l">Hook</span><span id="esc-hook" class="esc-grade">—</span></div>
        <div class="esc-cell"><span class="esc-l">Prompt Q.</span><span id="esc-pq" class="esc-grade">—</span></div>
        <div class="esc-cell"><span class="esc-l">CTR</span><span id="esc-ctr" class="esc-grade">—</span></div>
        <div class="esc-cell"><span class="esc-l">Readiness</span><span id="esc-read" class="esc-grade">—</span></div>
        <div class="esc-cell"><span class="esc-l">Szenen</span><span id="esc-scenes" class="esc-grade">—</span></div>
        <div class="esc-cell"><span class="esc-l">Warnungen</span><span id="esc-warn" class="esc-grade">—</span></div>
      </div>
    </div>
    <div class="opp-radar" id="opp-radar" aria-label="Opportunity Radar">
      <h3 class="subh ba112-radar-title">Opportunity Radar</h3>
      <p class="muted" style="margin:0 0 0.4rem;font-size:0.75rem">Relative Stärke der Signale (0–100 %, heuristisch).</p>
      <div class="radar-bars">
        <div class="radar-row"><span class="radar-label">Hook</span><div class="radar-track"><div class="radar-fill" id="radar-fill-hook"></div></div><span class="radar-pct" id="radar-pct-hook">—</span></div>
        <div class="radar-row"><span class="radar-label">Prompt Quality</span><div class="radar-track"><div class="radar-fill" id="radar-fill-pq"></div></div><span class="radar-pct" id="radar-pct-pq">—</span></div>
        <div class="radar-row"><span class="radar-label">Thumbnail CTR</span><div class="radar-track"><div class="radar-fill" id="radar-fill-ctr"></div></div><span class="radar-pct" id="radar-pct-ctr">—</span></div>
        <div class="radar-row"><span class="radar-label">Readiness</span><div class="radar-track"><div class="radar-fill" id="radar-fill-read"></div></div><span class="radar-pct" id="radar-pct-read">—</span></div>
        <div class="radar-row"><span class="radar-label">Szenenbasis</span><div class="radar-track"><div class="radar-fill" id="radar-fill-scenes"></div></div><span class="radar-pct" id="radar-pct-scenes">—</span></div>
      </div>
    </div>
    <div class="rewrite-rec-block">
      <h3 class="subh">Rewrite Recommendation Engine</h3>
      <ul id="rewrite-rec-list"><li class="muted">Noch keine Ableitung — Export oder Intake ausführen.</li></ul>
    </div>
    <div>
      <span class="esc-l" style="display:block;margin-bottom:0.35rem">One-Click Repair</span>
      <div class="repair-actions-row" id="repair-actions-row">
        <button type="button" class="sm" id="btn-repair-export" data-repair="export">Export</button>
        <button type="button" class="sm" id="btn-repair-preview" data-repair="preview">Preview</button>
        <button type="button" class="sm" id="btn-repair-readiness" data-repair="readiness">Readiness</button>
        <button type="button" class="sm" id="btn-repair-optimize" data-repair="optimize">Optimize</button>
        <button type="button" class="sm" id="btn-repair-ctr" data-repair="ctr">CTR</button>
        <button type="button" class="sm" id="btn-repair-input" data-repair="input">Eingabe</button>
        <button type="button" class="sm" id="btn-repair-warnings" data-repair="warnings">Warning Center</button>
        <button type="button" class="sm" id="btn-repair-clear-warnings" data-repair="clearwarnings">Warnungen leeren</button>
        <button type="button" class="sm" id="btn-repair-batch" data-repair="batch">Batch Compare</button>
      </div>
    </div>
    <div class="kill-switch-row">
      <label for="fd-kill-switch"><input type="checkbox" id="fd-kill-switch" autocomplete="off"/> <strong>Kill Switch</strong> — blockiert alle neuen <code>fetch</code>-Calls zu Story-Engine / Generate (lokaler Schutz, kein Server-State).</label>
    </div>
  </section>

  <section class="panel" id="coll-source-intake" style="margin-top:1rem">
    <h2>Source Intake (BA 11.0)</h2>
    <p class="muted">YouTube- oder News-URL ruft bestehende Generate-Endpunkte auf; Rohtext nur clientseitig in Kapitel segmentiert (Dashboard-V1, kein neuer API-Vertrag).</p>
    <div class="intake-type-row">
      <label for="intake-source-type">Quelle</label>
      <select id="intake-source-type">
        <option value="youtube">YouTube URL</option>
        <option value="news">News / Artikel URL</option>
        <option value="raw_text">Rohtext</option>
      </select>
    </div>
    <label for="intake-youtube-url">YouTube URL</label>
    <input type="text" id="intake-youtube-url" placeholder="https://www.youtube.com/watch?v=…"/>
    <label for="intake-news-url">News URL</label>
    <input type="text" id="intake-news-url" placeholder="https://…"/>
    <label for="intake-raw-text">Rohtext</label>
    <textarea id="intake-raw-text" placeholder="Freitext einfügen…" style="min-height:100px"></textarea>
    <label for="intake-topic">Topic (optional, Kategorie/Thema)</label>
    <input type="text" id="intake-topic" placeholder="z. B. Politik, True Crime, Wirtschaft"/>
    <p class="muted" id="intake-raw-headline-hint" style="font-size:0.76rem;margin:-0.25rem 0 0.6rem">Rohtext: Titel automatisch aus Rohtext erzeugt — oder aus dem Topic-Feld als Headline, falls gesetzt. Rohtext ≠ Titel.</p>
    <div class="actions" style="margin-top:0.5rem">
      <button type="button" class="primary" id="btn-intake-body" data-label="Auto Body aus Quelle">Auto Body aus Quelle</button>
    </div>
    <p id="intake-status" class="intake-status muted" role="status" aria-live="polite"></p>
  </section>

  <section class="panel" id="coll-full-pipeline" style="margin-top:1rem">
    <h2>Run Full Pipeline (BA 11.1)</h2>
    <p class="muted">Orchestrierung: Generate → Export → Preview → Readiness → Optimize → CTR → Founder Summary → Production Bundle (Downloads). Bei Fehler: Schritt rot, Pipeline stoppt. Ende: Session Snapshot speichern.</p>
    <ol id="pipeline-timeline" class="pipe-timeline" aria-label="Pipeline Timeline">
      <li class="pipe-step pending" data-pi="0"><span class="ps-label">1. Generate (Quelle)</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="1"><span class="ps-label">2. Export Package</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="2"><span class="ps-label">3. Preview</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="3"><span class="ps-label">4. Readiness</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="4"><span class="ps-label">5. Optimize</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="5"><span class="ps-label">6. Thumbnail CTR</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="6"><span class="ps-label">7. Founder Summary</span><span class="ps-msg"></span></li>
      <li class="pipe-step pending" data-pi="7"><span class="ps-label">8. Production Bundle</span><span class="ps-msg"></span></li>
    </ol>
    <div class="actions">
      <button type="button" class="primary" id="btn-full-pipeline" data-label="Run Full Pipeline">Run Full Pipeline</button>
    </div>
  </section>

  <div class="grid grid-2">
    <section class="panel" id="coll-input-panel">
      <h2>Input Panel</h2>
      <label for="fd-title">Title (Headline)</label>
      <input type="text" id="fd-title" placeholder="Headline / Videotitel"/>
      <label for="fd-topic">Topic (optional Kategorie/Thema)</label>
      <input type="text" id="fd-topic" placeholder="Kategorie oder Themenschwerpunkt"/>
      <label for="fd-summary">Source summary (Kurzfassung)</label>
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
        <button type="button" class="primary" id="btn-export" data-label="Build Export Package">Build Export Package</button>
        <button type="button" id="btn-preview" data-label="Preview Founder Metrics">Preview Founder Metrics</button>
        <button type="button" id="btn-readiness" data-label="Provider Readiness">Provider Readiness</button>
        <button type="button" id="btn-optimize" data-label="Optimize Provider Prompts">Optimize Provider Prompts</button>
        <button type="button" id="btn-ctr" data-label="Thumbnail CTR">Thumbnail CTR</button>
        <button type="button" id="btn-formats" data-label="Export Formats">Export Formats</button>
      </div>
      <p class="muted" style="margin-top:0.75rem">Batch Template Compare lädt alle IDs aus dem Template-Selector und ruft nacheinander Preview + Readiness auf.</p>
      <div class="actions">
        <button type="button" id="btn-batch-compare" data-label="Batch Template Compare">Batch Template Compare</button>
        <span class="muted" id="batch-status"></span>
      </div>
    </section>
  </div>

  <section class="panel" id="coll-ops" style="margin-top:1rem">
    <h2>Production Ready Checklist</h2>
    <div id="prod-checklist-badge" class="checklist-badge blocked">BLOCKED</div>
    <ul id="prod-checklist-items"></ul>
    <h2 class="subh">Export Ops (lokal)</h2>
    <p class="muted">Download Production Bundle: mehrere Dateien nacheinander (kein ZIP). Session Snapshot: localStorage Key <code>fd_session_snapshot_v1</code>.</p>
    <div class="actions">
      <button type="button" class="primary" id="btn-prod-bundle" data-label="Download Production Bundle">Download Production Bundle</button>
      <button type="button" id="btn-copy-all-prompts" data-label="Copy All Prompts">Copy All Prompts</button>
      <button type="button" id="btn-snapshot-save" data-label="Save Session Snapshot">Save Session Snapshot</button>
      <button type="button" id="btn-snapshot-load" data-label="Load Last Snapshot">Load Last Snapshot</button>
      <button type="button" id="btn-snapshot-clear" data-label="Clear Snapshot">Clear Snapshot</button>
    </div>
  </section>

  <details class="fd-coll" open id="coll-export">
    <summary>Export Package (roh)</summary>
    <div class="coll-body">
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-export-full">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-export-full" data-dlname="export-package.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-export-full" data-dlname="export-package.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-export-full">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-preview">
    <summary>Preview (Hook + Prompt Quality)</summary>
    <div class="coll-body grid grid-2">
      <div class="panel" style="margin:0">
        <h2>Hook Preview</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-hook">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-hook" data-dlname="hook-preview.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-hook" data-dlname="hook-preview.txt">TXT</button>
        </div>
        <pre class="out out-empty" id="out-hook">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>Prompt Quality Score <span id="pq-badge" class="pq-badge neutral" title="Farbe aus numerischem Preview-Score (≥70 grün, 40–69 gelb, &lt;40 rot); Export = Report.">—</span></h2>
        <div class="score out-empty" id="out-pq-score">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</div>
        <div class="out-toolbar" style="margin-top:0.5rem">
          <button type="button" class="sm tb-copy" data-pre="out-pq-detail">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-pq-detail" data-dlname="prompt-quality.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-pq-detail" data-dlname="prompt-quality.txt">TXT</button>
        </div>
        <pre class="out out-empty" id="out-pq-detail" style="max-height:160px">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
    </div>
  </details>

  <details class="fd-coll" open id="coll-readiness">
    <summary>Provider Readiness</summary>
    <div class="coll-body">
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-readiness">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-readiness" data-dlname="provider-readiness.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-readiness" data-dlname="provider-readiness.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-readiness">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-optimize">
    <summary>Provider Optimize (Leonardo / OpenAI / Kling + Shotlists)</summary>
    <div class="coll-body grid grid-2">
      <div class="panel" style="margin:0">
        <h2>Leonardo Prompts</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-leo">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-leo" data-dlname="leonardo-prompts.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-leo" data-dlname="leonardo-prompts.txt">TXT</button>
        </div>
        <pre class="out out-empty" id="out-leo">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>OpenAI Prompts</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-openai">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-openai" data-dlname="openai-prompts.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-openai" data-dlname="openai-prompts.txt">TXT</button>
        </div>
        <pre class="out out-empty" id="out-openai">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>Kling Motion Prompts</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-kling">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-kling" data-dlname="kling-prompts.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-kling" data-dlname="kling-prompts.txt">TXT</button>
        </div>
        <pre class="out out-empty" id="out-kling">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>CapCut Shotlist</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-capcut">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-capcut" data-dlname="capcut-shotlist.json">JSON</button>
          <button type="button" class="sm tb-csv" data-pre="out-capcut" data-dlname="capcut-shotlist.csv">CSV</button>
        </div>
        <pre class="out out-empty" id="out-capcut">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>CSV Shotlist</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-csv">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-csv" data-dlname="csv-shotlist.json">JSON</button>
          <button type="button" class="sm tb-csv" data-pre="out-csv" data-dlname="csv-shotlist.csv">CSV</button>
        </div>
        <pre class="out out-empty" id="out-csv">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <h2 class="subh">Provider Prompt Cards</h2>
      <p class="muted">Nach „Optimize Provider Prompts“ — je Szene Leonardo / Kling / OpenAI mit Copy.</p>
      <div id="provider-prompt-cards" class="prompt-cards-wrap"></div>
    </div>
  </details>

  <details class="fd-coll" open id="coll-ctr">
    <summary>Thumbnail CTR</summary>
    <div class="coll-body grid grid-2">
      <div class="panel" style="margin:0">
        <h2>Thumbnail CTR Score</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-ctr-raw">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-ctr-raw" data-dlname="thumbnail-ctr.json">JSON</button>
        </div>
        <div class="score out-empty" id="out-ctr">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</div>
        <pre class="out out-empty" id="out-ctr-raw" style="display:none">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
      <div class="panel" style="margin:0">
        <h2>Thumbnail Variants</h2>
        <div class="out-toolbar">
          <button type="button" class="sm tb-copy" data-pre="out-thumb-var">Copy</button>
          <button type="button" class="sm tb-json" data-pre="out-thumb-var" data-dlname="thumbnail-variants.json">JSON</button>
          <button type="button" class="sm tb-txt" data-pre="out-thumb-var" data-dlname="thumbnail-variants.txt">TXT</button>
        </div>
        <pre class="out out-empty" id="out-thumb-var">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
      </div>
    </div>
  </details>

  <details class="fd-coll" open id="coll-batch">
    <summary>Batch Template Compare</summary>
    <div class="coll-body">
      <p class="muted">readiness_score = Mittelwert aus scores.leonardo, scores.kling, scores.openai (Provider Readiness).</p>
      <div id="batch-scroll-anchor" style="overflow-x:auto">
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

  <details class="fd-coll" open id="coll-prompt-lab">
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

  <details class="fd-coll" id="coll-formats">
    <summary>Export Formats Registry</summary>
    <div class="coll-body">
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-formats">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-formats" data-dlname="export-formats.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-formats" data-dlname="export-formats.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-formats" style="max-height:200px">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <section class="panel" style="margin-top:1rem" id="coll-warning-center">
    <h2>Warning Center</h2>
    <div id="warn-center-grouped" class="warn-grouped muted">Noch keine Warnungen aggregiert.</div>
    <ul class="warn-list" id="out-warnings" style="display:none" aria-hidden="true"></ul>
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
  let lastPreview = null;
  let lastReadiness = null;
  let lastCtrPayload = null;
  let lastNumericPq = null;
  let templateIds = [];
  let warningsAcc = [];

  const OUTPUT_EMPTY = "Noch kein Ergebnis. Klicke auf den passenden Action-Button.";

  function openPanelAndScroll(detailsId, scrollTargetId) {
    var d = detailsId ? document.getElementById(detailsId) : null;
    if (d && d.tagName === "DETAILS") d.open = true;
    var el = scrollTargetId ? $(scrollTargetId) : d;
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  async function withActionButton(btn, detailsId, scrollTargetId, task) {
    var label = btn.getAttribute("data-label") || btn.textContent;
    btn.setAttribute("data-label", label);
    btn.disabled = true;
    btn.classList.add("is-loading");
    btn.classList.remove("is-success", "is-error");
    btn.textContent = "Loading...";
    try {
      if (isKillSwitchActive()) throw new Error("Kill Switch aktiv — Aktion blockiert.");
      await task();
      btn.textContent = label;
      btn.disabled = false;
      btn.classList.remove("is-loading");
      btn.classList.add("is-success");
      setTimeout(function() { btn.classList.remove("is-success"); }, 1600);
      openPanelAndScroll(detailsId, scrollTargetId || detailsId);
    } catch (e) {
      btn.textContent = label;
      btn.disabled = false;
      btn.classList.remove("is-loading");
      btn.classList.add("is-error");
      setTimeout(function() { btn.classList.remove("is-error"); }, 1600);
      showError(String(e.message || e));
      openPanelAndScroll(detailsId, scrollTargetId || detailsId);
    }
  }

  function showError(msg) {
    err.textContent = msg || "";
    err.classList.toggle("visible", !!msg);
  }

  function setIntakeStatus(msg, kind) {
    var el = $("intake-status");
    if (!el) return;
    el.textContent = msg || "";
    var base = "intake-status muted";
    if (kind === "success") el.className = base + " intake-status-success";
    else if (kind === "err") el.className = base + " intake-status-err";
    else if (kind === "info") el.className = base + " intake-status-info";
    else el.className = base;
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
    refreshWarningCenter();
    updateProductionChecklist();
  }
  function renderWarnings() {
    refreshWarningCenter();
    updateProductionChecklist();
  }
  function clearWarnings() {
    warningsAcc = [];
    refreshWarningCenter();
    updateProductionChecklist();
  }

  const LS_SNAPSHOT_KEY = "fd_session_snapshot_v1";

  function sleep(ms) {
    return new Promise(function(res) { setTimeout(res, ms); });
  }

  function getSceneCount() {
    if (!lastExport) return 0;
    if (lastExport.scene_plan && Array.isArray(lastExport.scene_plan.scenes)) return lastExport.scene_plan.scenes.length;
    if (lastExport.scene_prompts && Array.isArray(lastExport.scene_prompts.scenes)) return lastExport.scene_prompts.scenes.length;
    return 0;
  }

  function collectAllWarningsStrings() {
    var seen = {};
    function addList(arr) {
      (arr || []).forEach(function(w) {
        if (w && typeof w === "string" && !seen[w]) seen[w] = 1;
      });
    }
    addList(warningsAcc);
    if (lastExport) {
      addList(lastExport.warnings);
      if (lastExport.hook && lastExport.hook.warnings) addList(lastExport.hook.warnings);
      if (lastExport.scene_prompts && lastExport.scene_prompts.warnings) addList(lastExport.scene_prompts.warnings);
    }
    if (lastPreview && lastPreview.top_warnings) addList(lastPreview.top_warnings);
    if (lastReadiness) {
      addList(lastReadiness.warnings);
      addList(lastReadiness.blocking_issues);
    }
    if (lastOptimize && lastOptimize.warnings) addList(lastOptimize.warnings);
    if (lastCtrPayload && lastCtrPayload.warnings) addList(lastCtrPayload.warnings);
    return Object.keys(seen);
  }

  function classifyWarningBucket(w) {
    var s = String(w).toLowerCase();
    if (/quality|prompt_quality|conformance|check|evidence|template|refine|policy/.test(s)) return "prompt_quality";
    if (/provider|leonardo|kling|openai|stub|continuity|negative|image/.test(s)) return "provider";
    if (/chapter|kapitel|hook|title|empty|duration|input|szene|scene/.test(s)) return "input";
    if (/source|url|article|extract|summary|quelle/.test(s)) return "source";
    return "other";
  }

  function refreshWarningCenter() {
    var root = $("warn-center-grouped");
    if (!root) return;
    var all = collectAllWarningsStrings();
    if (!all.length) {
      root.innerHTML = "<p class=\\"muted\\">Keine Warnungen aus Export / Preview / Readiness / Optimize / CTR.</p>";
      return;
    }
    var buckets = { prompt_quality: [], provider: [], input: [], source: [], other: [] };
    all.forEach(function(w) {
      buckets[classifyWarningBucket(w)].push(w);
    });
    var order = ["prompt_quality", "provider", "input", "source", "other"];
    var labels = {
      prompt_quality: "prompt_quality",
      provider: "provider",
      input: "input",
      source: "source",
      other: "other"
    };
    root.innerHTML = "";
    order.forEach(function(key) {
      var list = buckets[key];
      var div = document.createElement("div");
      div.className = "warn-group";
      var h = document.createElement("h4");
      h.textContent = labels[key] + " (" + list.length + ")";
      div.appendChild(h);
      if (!list.length) {
        var p = document.createElement("p");
        p.className = "muted";
        p.style.margin = "0";
        p.textContent = "—";
        div.appendChild(p);
      } else {
        var ul = document.createElement("ul");
        list.forEach(function(t) {
          var li = document.createElement("li");
          li.textContent = t;
          ul.appendChild(li);
        });
        div.appendChild(ul);
      }
      root.appendChild(div);
    });
  }

  function updateProductionChecklist() {
    var badge = $("prod-checklist-badge");
    var ul = $("prod-checklist-items");
    if (!badge || !ul) return;
    var sc = getSceneCount();
    var hasEx = !!lastExport;
    var hasPr = !!lastPreview;
    var hasRe = !!lastReadiness;
    var hasOpt = !!lastOptimize;
    var hasCtr = !!lastCtrPayload;
    var wCount = collectAllWarningsStrings().length;
    var blocked = !hasEx || sc === 0;
    var allData = hasEx && sc > 0 && hasPr && hasRe && hasOpt && hasCtr;
    var status, cls;
    if (blocked) {
      status = "BLOCKED";
      cls = "blocked";
    } else if (allData && wCount === 0) {
      status = "READY";
      cls = "ready";
    } else {
      status = "PARTIAL";
      cls = "partial";
    }
    badge.textContent = status;
    badge.className = "checklist-badge " + cls;
    ul.innerHTML = "";
    function addRow(ok, label) {
      var li = document.createElement("li");
      li.className = ok ? "ok" : "no";
      li.textContent = label;
      ul.appendChild(li);
    }
    addRow(hasEx, "Export Package vorhanden: " + (hasEx ? "ja" : "nein"));
    addRow(sc > 0, "scene_count > 0: " + sc);
    addRow(hasPr, "Preview vorhanden: " + (hasPr ? "ja" : "nein"));
    addRow(hasRe, "Readiness vorhanden: " + (hasRe ? "ja" : "nein"));
    addRow(hasOpt, "Optimize vorhanden: " + (hasOpt ? "ja" : "nein"));
    addRow(hasCtr, "CTR vorhanden: " + (hasCtr ? "ja" : "nein"));
    addRow(wCount === 0, "Warnings (gesamt): " + wCount);
    refreshFounderInterpretation();
  }

  const VIEW_MODE_KEY = "fd_view_mode_v1";

  function isKillSwitchActive() {
    var sw = $("fd-kill-switch");
    return !!(sw && sw.checked);
  }

  function syncKillSwitchBanner() {
    var b = $("fd-kill-switch-banner");
    if (b) b.classList.toggle("visible", isKillSwitchActive());
  }

  function getHookScoreVal() {
    if (lastPreview != null && lastPreview.hook_score != null) return Number(lastPreview.hook_score);
    if (lastExport && lastExport.hook && lastExport.hook.hook_score != null) return Number(lastExport.hook.hook_score);
    return null;
  }

  function getPqScoreVal() {
    if (lastPreview != null && lastPreview.prompt_quality_score != null) return Number(lastPreview.prompt_quality_score);
    return null;
  }

  function getCtrVal() {
    if (lastCtrPayload && lastCtrPayload.ctr_score != null) return Number(lastCtrPayload.ctr_score);
    return null;
  }

  function computeThemenpotenzialScore() {
    if (!lastExport && !lastPreview && !lastReadiness && !lastCtrPayload) return null;
    var h01 = (function() {
      var h = getHookScoreVal();
      if (h == null || isNaN(h)) return 50;
      return Math.min(100, Math.max(0, h * 10));
    })();
    var pq01 = getPqScoreVal();
    if (pq01 == null || isNaN(pq01)) pq01 = 50;
    var ctr01 = getCtrVal();
    if (ctr01 == null || isNaN(ctr01)) ctr01 = 50;
    var w = collectAllWarningsStrings().length;
    var warnPart = Math.max(0, 100 - Math.min(w * 8, 100));
    var ra = 50;
    if (lastReadiness && lastReadiness.scores) {
      ra = readinessAggregate(lastReadiness.scores);
      if (ra == null || isNaN(ra)) ra = 50;
    }
    var mix = h01 * 0.22 + pq01 * 0.26 + ctr01 * 0.2 + warnPart * 0.14 + ra * 0.18;
    return Math.max(0, Math.min(100, Math.round(mix)));
  }

  function pickBestProviderName() {
    if (!lastReadiness || !lastReadiness.scores) return "—";
    var s = lastReadiness.scores;
    var pairs = [
      ["openai", Number(s.openai) || 0],
      ["leonardo", Number(s.leonardo) || 0],
      ["kling", Number(s.kling) || 0]
    ];
    pairs.sort(function(a, b) { return b[1] - a[1]; });
    return pairs[0][0] + " (" + pairs[0][1] + ")";
  }

  function computeRiskLevel() {
    var w = collectAllWarningsStrings().length;
    var st = lastReadiness && lastReadiness.overall_status;
    if (w > 8 || st === "not_ready") return { label: "HOCH", cls: "red" };
    if (w > 3 || st === "partial_ready") return { label: "MITTEL", cls: "yellow" };
    if (!lastExport && !lastPreview) return { label: "UNKLAR", cls: "neutral" };
    return { label: "NIEDRIG", cls: "green" };
  }

  function computeNextBestAction() {
    var sc = getSceneCount();
    if (!lastExport || sc === 0) {
      return { code: "VERWERFEN", cls: "verwerfen", de: "VERWERFEN", hint: "Kein nutzbares Szenenmaterial — Eingabe oder Kapitel prüfen." };
    }
    var h = getHookScoreVal();
    if (h != null && !isNaN(h) && h < 4.5) {
      return { code: "HOOK", cls: "hook", de: "HOOK ÜBERARBEITEN", hint: "Hook-Score wirkt schwach für Aufmerksamkeit." };
    }
    if (lastReadiness && lastReadiness.overall_status === "not_ready") {
      return { code: "PROVIDER", cls: "provider", de: "PROVIDER PROMPTS VERBESSERN", hint: "Readiness signalisiert Blocker je Provider-Profil." };
    }
    var pq = getPqScoreVal();
    if (pq != null && !isNaN(pq) && pq < 42) {
      return { code: "PROVIDER", cls: "provider", de: "PROVIDER PROMPTS VERBESSERN", hint: "Prompt-Quality unter Zielkorridor." };
    }
    var ctr = getCtrVal();
    if (ctr != null && !isNaN(ctr) && ctr < 42) {
      return { code: "THUMBNAIL", cls: "thumb", de: "THUMBNAIL OPTIMIEREN", hint: "CTR-Heuristik niedrig — Titel/Hook/Varianten testen." };
    }
    var w = collectAllWarningsStrings().length;
    if (w > 6) {
      return { code: "PROVIDER", cls: "provider", de: "PROVIDER PROMPTS VERBESSERN", hint: "Viele Warnungen — Qualität und Konsistenz prüfen." };
    }
    return { code: "PRODUZIEREN", cls: "produzieren", de: "PRODUZIEREN", hint: "Kernsignale stabil — Export-Paket nutzbar." };
  }

  function humanHookSummary() {
    var h = getHookScoreVal();
    if (h == null || isNaN(h)) return "Noch kein belastbarer Hook-Score — bitte Export oder Preview ausführen.";
    if (h >= 7.5) return "Der Hook wirkt stark: hohe Aufmerksamkeitswahrscheinlichkeit, klarer emotionaler Einstieg.";
    if (h >= 5.5) return "Der Hook ist solide, aber noch ausbaufähig für maximale Klickmotivation.";
    return "Der Hook wirkt schwach — Formulierung schärfen oder stärkeren Winkel wählen.";
  }

  function humanPqSummary() {
    var pq = getPqScoreVal();
    if (pq == null || isNaN(pq)) {
      if (lastExport && (lastExport.prompt_quality || (lastExport.scene_prompts && lastExport.scene_prompts.prompt_quality))) {
        return "Qualitätsreport aus Export vorhanden (ohne numerischen Preview-Score) — technische Checks in den Rohdaten prüfen.";
      }
      return "Noch keine Prompt-Quality-Bewertung — Preview ausführen oder Export-Paket bauen.";
    }
    if (pq >= 72) return "Prompt-Qualität liegt im oberen Bereich — gute Basis für konsistente Szenen-Prompts.";
    if (pq >= 45) return "Prompt-Qualität ist mittig — einzelne Szenen könnten nachgeschärft werden.";
    return "Prompt-Qualität ist niedrig — Eingaben, Kapitelinhalt oder Template-Kontext verbessern.";
  }

  function humanReadinessSummary() {
    if (!lastReadiness) return "Readiness noch nicht geladen — Provider Readiness ausführen.";
    var st = lastReadiness.overall_status || "—";
    var rs = lastReadiness.scores;
    var avg = rs ? readinessAggregate(rs) : null;
    if (st === "ready") return "Provider-Pipeline wirkt stimmig (Status: ready). Mittlere Readiness ca. " + (avg != null ? avg : "?") + "/100.";
    if (st === "partial_ready") return "Teilweise produzierbar (partial_ready) — Schwachstellen in Warnungen/Blocking prüfen.";
    return "Produktion riskant (not_ready oder unklar) — zuerst Prompts und Szeneninhalt stabilisieren.";
  }

  function humanCtrSummary() {
    if (!lastCtrPayload) return "CTR-Heuristik noch nicht geladen — Thumbnail CTR ausführen (nach Export sinnvoll).";
    var c = getCtrVal();
    if (c == null || isNaN(c)) return "Kein CTR-Score ermittelbar.";
    if (c >= 68) return "Thumbnail/Title-Signale wirken stark für Aufmerksamkeit (heuristischer CTR-Score hoch).";
    if (c >= 44) return "CTR-Potenzial mittel — Varianten und emotionalen Trigger testen.";
    return "CTR-Potenzial niedrig — Hook, Titel und Thumbnail-Texte überarbeiten.";
  }

  function buildOpportunities() {
    var out = [];
    var h = getHookScoreVal();
    if (h != null && !isNaN(h) && h >= 6) out.push("Starker Hook-Hebel für erste Sekunden");
    var pq = getPqScoreVal();
    if (pq != null && !isNaN(pq) && pq >= 65) out.push("Solide Prompt-Qualität für wiederholbare Szenen");
    var ctr = getCtrVal();
    if (ctr != null && !isNaN(ctr) && ctr >= 60) out.push("Thumbnail-Pfad mit CTR-Heuristik überdurchschnittlich");
    if (lastReadiness && lastReadiness.overall_status === "ready") out.push("Provider-Readiness signalisiert Go");
    if (getSceneCount() >= 3) out.push("Genug Szenen für klassischen Erzählbogen");
    if (!out.length) out.push("Mehr Daten sammeln (Export + Preview + Readiness) für Chancen-Analyse.");
    return out.slice(0, 5);
  }

  function buildWeaknesses() {
    var ws = collectAllWarningsStrings().slice(0, 5);
    if (!ws.length) {
      var h = getHookScoreVal();
      if (h != null && !isNaN(h) && h < 5) return ["Schwacher Hook-Score"];
      return ["Keine Warnungen gelistet — trotzdem Readiness und Qualität manuell prüfen."];
    }
    return ws;
  }

  function letterGradeFrom100(x) {
    if (x == null || isNaN(x)) return "—";
    if (x >= 76) return "A";
    if (x >= 58) return "B";
    if (x >= 42) return "C";
    return "D";
  }

  function letterGradeFromHook10(h) {
    if (h == null || isNaN(h)) return "—";
    return letterGradeFrom100(Math.min(100, Number(h) * 10));
  }

  function warnLetterGrade(wc) {
    if (wc <= 0) return "A";
    if (wc <= 2) return "B";
    if (wc <= 5) return "C";
    return "D";
  }

  function computeExecOverallLabel() {
    var nba = computeNextBestAction();
    if (nba.code === "PRODUZIEREN") return { text: "GO", cls: "grade-go" };
    if (nba.code === "VERWERFEN") return { text: "STOP", cls: "grade-stop" };
    return { text: "HOLD", cls: "grade-hold" };
  }

  function setRadarBar(fillId, pctId, v) {
    var f = $(fillId);
    var p = $(pctId);
    var n = Math.max(0, Math.min(100, Math.round(v == null || isNaN(v) ? 0 : Number(v))));
    if (f) {
      f.style.width = n + "%";
      f.style.background = n >= 62 ? "rgba(74,222,128,0.88)" : n >= 38 ? "rgba(251,191,36,0.88)" : "rgba(248,113,113,0.88)";
    }
    if (p) p.textContent = n + "%";
  }

  function refreshOperatorClarity() {
    var ov = computeExecOverallLabel();
    var oel = $("esc-overall");
    if (oel) {
      oel.textContent = ov.text;
      oel.className = "esc-val " + ov.cls;
    }
    var h = getHookScoreVal();
    var pq = getPqScoreVal();
    var ctr = getCtrVal();
    var ra = lastReadiness && lastReadiness.scores ? readinessAggregate(lastReadiness.scores) : null;
    if (ra == null || isNaN(ra)) ra = null;
    var sc = getSceneCount();
    var wc = collectAllWarningsStrings().length;
    var egH = $("esc-hook");
    if (egH) egH.textContent = letterGradeFromHook10(h);
    var egPq = $("esc-pq");
    if (egPq) egPq.textContent = letterGradeFrom100(pq);
    var egCtr = $("esc-ctr");
    if (egCtr) egCtr.textContent = letterGradeFrom100(ctr);
    var egR = $("esc-read");
    if (egR) egR.textContent = letterGradeFrom100(ra);
    var egSc = $("esc-scenes");
    if (egSc) egSc.textContent = sc <= 0 ? "—" : (sc >= 5 ? "A" : sc >= 3 ? "B" : "C");
    var egW = $("esc-warn");
    if (egW) egW.textContent = warnLetterGrade(wc);
    var h100 = h == null || isNaN(h) ? 0 : Math.min(100, Number(h) * 10);
    var pqN = pq == null || isNaN(pq) ? 0 : Number(pq);
    var ctrN = ctr == null || isNaN(ctr) ? 0 : Number(ctr);
    var readN = ra == null || isNaN(ra) ? 0 : Number(ra);
    var scN = Math.min(100, sc * 14);
    setRadarBar("radar-fill-hook", "radar-pct-hook", h100);
    setRadarBar("radar-fill-pq", "radar-pct-pq", pqN);
    setRadarBar("radar-fill-ctr", "radar-pct-ctr", ctrN);
    setRadarBar("radar-fill-read", "radar-pct-read", readN);
    setRadarBar("radar-fill-scenes", "radar-pct-scenes", scN);
    renderRewriteRecommendations();
  }

  function buildRewriteRecommendations() {
    var nba = computeNextBestAction();
    var arr = [{ title: nba.de, detail: nba.hint, code: nba.code }];
    var seen = {};
    seen[String(nba.hint)] = 1;
    collectAllWarningsStrings().slice(0, 4).forEach(function(w) {
      if (!w || seen[w]) return;
      seen[w] = 1;
      arr.push({ title: "Qualität / Quelle prüfen", detail: w, code: "PROVIDER" });
    });
    return arr.slice(0, 5);
  }

  function renderRewriteRecommendations() {
    var ul = $("rewrite-rec-list");
    if (!ul) return;
    ul.innerHTML = "";
    buildRewriteRecommendations().forEach(function(r) {
      var li = document.createElement("li");
      var sp = document.createElement("span");
      sp.textContent = r.title + " — " + r.detail + " ";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sm";
      btn.textContent = repairActionLabel(r.code);
      btn.onclick = function() { runRepairFromReco(r.code); };
      li.appendChild(sp);
      li.appendChild(btn);
      ul.appendChild(li);
    });
  }

  function repairActionLabel(code) {
    if (code === "VERWERFEN") return "Zur Eingabe";
    if (code === "HOOK") return "Preview";
    if (code === "PROVIDER") return "Readiness";
    if (code === "THUMBNAIL") return "CTR";
    if (code === "PRODUZIEREN") return "Ops / Bundle";
    return "Preview";
  }

  function runRepairFromReco(code) {
    if (code === "VERWERFEN") return runRepair("input");
    if (code === "HOOK") return runRepair("preview");
    if (code === "PROVIDER") return runRepair("readiness");
    if (code === "THUMBNAIL") return runRepair("ctr");
    if (code === "PRODUZIEREN") return runRepair("ops");
    runRepair("preview");
  }

  function runRepair(kind) {
    if (isKillSwitchActive()) {
      showError("Kill Switch aktiv — Repair blockiert.");
      syncKillSwitchBanner();
      return;
    }
    showError("");
    if (kind === "export") {
      openPanelAndScroll("coll-export", "coll-export");
      var bx = $("btn-export");
      if (bx) bx.click();
      return;
    }
    if (kind === "preview") {
      openPanelAndScroll("coll-preview", "coll-preview");
      var bp = $("btn-preview");
      if (bp) bp.click();
      return;
    }
    if (kind === "readiness") {
      openPanelAndScroll("coll-readiness", "coll-readiness");
      var br = $("btn-readiness");
      if (br) br.click();
      return;
    }
    if (kind === "optimize") {
      openPanelAndScroll("coll-optimize", "coll-optimize");
      var bo = $("btn-optimize");
      if (bo) bo.click();
      return;
    }
    if (kind === "ctr") {
      openPanelAndScroll("coll-ctr", "coll-ctr");
      var bc = $("btn-ctr");
      if (bc) bc.click();
      return;
    }
    if (kind === "input") {
      openPanelAndScroll(null, "coll-input-panel");
      try { $("fd-title").focus(); } catch (e0) {}
      return;
    }
    if (kind === "warnings") {
      openPanelAndScroll(null, "coll-warning-center");
      return;
    }
    if (kind === "clearwarnings") {
      clearWarnings();
      refreshWarningCenter();
      updateProductionChecklist();
      return;
    }
    if (kind === "batch") {
      openPanelAndScroll("coll-batch", "batch-scroll-anchor");
      var bb = $("btn-batch-compare");
      if (bb) bb.click();
      return;
    }
    if (kind === "ops") {
      openPanelAndScroll("coll-ops", "coll-ops");
    }
  }

  function renderStrategicBadges() {
    var host = $("strategic-badges-row");
    if (!host) return;
    host.innerHTML = "";
    function badge(cls, txt) {
      var s = document.createElement("span");
      s.className = "strat-badge " + cls;
      s.textContent = txt;
      host.appendChild(s);
    }
    var h = getHookScoreVal();
    var ctr = getCtrVal();
    var viral = 0;
    if (h != null && !isNaN(h)) viral += h * 10;
    if (ctr != null && !isNaN(ctr)) viral += ctr;
    viral = viral ? Math.round(viral / (h != null && ctr != null ? 2 : 1)) : 40;
    badge(viral >= 72 ? "high" : viral >= 48 ? "mid" : "low", "Strategic Badge · Viral Potential: " + (viral >= 72 ? "hoch" : viral >= 48 ? "mittel" : "niedrig"));
    var tmpl = (buildExportBody().video_template || "").toLowerCase();
    var dur = parseInt(String(buildExportBody().duration_minutes || 10), 10) || 10;
    var ev = (tmpl.indexOf("generic") >= 0 || dur >= 10) ? "mittel" : "niedrig";
    if (dur >= 12 && tmpl.indexOf("true") >= 0) ev = "hoch";
    badge(ev === "hoch" ? "high" : ev === "mittel" ? "mid" : "low", "Strategic Badge · Evergreen Potential: " + ev);
    var fit = "mittel";
    if (lastPreview && lastPreview.export_ready) fit = "hoch";
    else if (lastPreview && !lastPreview.export_ready) fit = "niedrig";
    else if (lastExport && getSceneCount() > 0) fit = "mittel";
    badge(fit === "hoch" ? "high" : fit === "mittel" ? "mid" : "low", "Strategic Badge · Template Fit: " + fit);
  }

  function refreshFounderInterpretation() {
    var pot = computeThemenpotenzialScore();
    $("fk-potential").textContent = pot == null ? "—" : String(pot);
    var sc = getSceneCount();
    var hasEx = !!lastExport;
    var hasPr = !!lastPreview;
    var hasRe = !!lastReadiness;
    var hasOpt = !!lastOptimize;
    var hasCtr = !!lastCtrPayload;
    var wCount = collectAllWarningsStrings().length;
    var blocked = !hasEx || sc === 0;
    var allData = hasEx && sc > 0 && hasPr && hasRe && hasOpt && hasCtr;
    $("fk-prod-status").textContent = blocked ? "Blockiert" : (allData && wCount === 0 ? "Produktionsbereit" : "Teilweise bereit");
    $("fk-best-provider").textContent = pickBestProviderName();
    var risk = computeRiskLevel();
    $("fk-risk").textContent = risk.label;
    $("fk-risk").style.color = risk.cls === "green" ? "var(--ok)" : risk.cls === "yellow" ? "var(--warn)" : risk.cls === "red" ? "var(--danger)" : "var(--muted)";
    var nba = computeNextBestAction();
    $("fk-handlung").textContent = nba.de + " — " + nba.hint;
    var nbaEl = $("next-best-action");
    if (nbaEl) {
      nbaEl.className = "nba-card " + nba.cls;
      $("nba-text").textContent = nba.de;
    }
    $("hum-hook").textContent = humanHookSummary();
    $("hum-pq").textContent = humanPqSummary();
    $("hum-readiness").textContent = humanReadinessSummary();
    $("hum-ctr").textContent = humanCtrSummary();
    var oc = $("opp-chances-list");
    var ow = $("opp-weak-list");
    if (oc) {
      oc.innerHTML = "";
      buildOpportunities().forEach(function(t) {
        var li = document.createElement("li");
        li.textContent = t;
        oc.appendChild(li);
      });
    }
    if (ow) {
      ow.innerHTML = "";
      buildWeaknesses().forEach(function(t) {
        var li = document.createElement("li");
        li.textContent = t;
        ow.appendChild(li);
      });
    }
    renderStrategicBadges();
    refreshOperatorClarity();
  }

  function applyViewMode(mode) {
    document.body.classList.remove("dashboard-mode-founder", "dashboard-mode-operator", "dashboard-mode-raw", "raw-view");
    var f = $("btn-founder-mode");
    var o = $("btn-operator-mode");
    var r = $("btn-raw-mode");
    if (f) f.classList.remove("active");
    if (o) o.classList.remove("active");
    if (r) r.classList.remove("active");
    if (mode === "raw") {
      document.body.classList.add("dashboard-mode-raw", "raw-view");
      if (r) r.classList.add("active");
    } else if (mode === "operator") {
      document.body.classList.add("dashboard-mode-operator");
      if (o) o.classList.add("active");
    } else {
      document.body.classList.add("dashboard-mode-founder");
      if (f) f.classList.add("active");
    }
    try { sessionStorage.setItem(VIEW_MODE_KEY, mode); } catch (e1) {}
  }

  function buildMarkdownBriefing() {
    var lines = [];
    lines.push("# Production Briefing");
    lines.push("");
    lines.push("## Meta");
    lines.push("- generated: " + new Date().toISOString());
    lines.push("");
    lines.push("## Title");
    lines.push(String((buildExportBody().title || $("fd-title").value || "(kein Titel)")));
    lines.push("");
    lines.push("## Template");
    lines.push(String(buildExportBody().video_template || "generic"));
    lines.push("");
    lines.push("## Hook");
    lines.push("```json");
    lines.push(JSON.stringify(lastExport && lastExport.hook ? lastExport.hook : {}, null, 2));
    lines.push("```");
    lines.push("");
    lines.push("## Thumbnail Prompt");
    lines.push(String((lastExport && lastExport.thumbnail_prompt) || ""));
    lines.push("");
    lines.push("## Prompt Quality");
    lines.push("```json");
    lines.push(JSON.stringify((lastExport && (lastExport.prompt_quality || (lastExport.scene_prompts && lastExport.scene_prompts.prompt_quality))) || (lastPreview ? { prompt_quality_score: lastPreview.prompt_quality_score } : {}), null, 2));
    lines.push("```");
    lines.push("");
    lines.push("## Provider Readiness");
    lines.push("```json");
    lines.push(JSON.stringify(lastReadiness || {}, null, 2));
    lines.push("```");
    lines.push("");
    lines.push("## Thumbnail CTR");
    lines.push("```json");
    lines.push(JSON.stringify(lastCtrPayload || {}, null, 2));
    lines.push("```");
    lines.push("");
    lines.push("## Scenes & Provider Prompts");
    if (lastOptimize && lastOptimize.optimized_prompts) {
      var op = lastOptimize.optimized_prompts;
      var max = Math.max((op.leonardo || []).length, (op.openai || []).length, (op.kling || []).length);
      for (var i = 0; i < max; i++) {
        lines.push("### Szene " + (i + 1));
        lines.push("#### Leonardo");
        lines.push("```");
        lines.push((op.leonardo && op.leonardo[i]) ? String((op.leonardo[i].positive_optimized || "")) : "");
        lines.push("```");
        lines.push("#### OpenAI");
        lines.push("```");
        lines.push((op.openai && op.openai[i]) ? String((op.openai[i].positive_optimized || "")) : "");
        lines.push("```");
        lines.push("#### Kling");
        lines.push("```");
        if (op.kling && op.kling[i]) {
          var k = op.kling[i];
          lines.push("motion: " + (k.motion_prompt || ""));
          lines.push("camera: " + (k.camera_path || ""));
          lines.push("transition: " + (k.transition_hint || ""));
          lines.push("keyframe: " + (k.keyframe_positive || ""));
        }
        lines.push("```");
      }
    } else {
      lines.push("_Optimize-Daten fehlen._");
    }
    lines.push("");
    lines.push("## Warnings");
    collectAllWarningsStrings().forEach(function(w) { lines.push("- " + w); });
    return lines.join("\\n");
  }

  function formatProviderTxt(rows, kind) {
    if (!rows || !rows.length) return "";
    var parts = [];
    rows.forEach(function(row, idx) {
      parts.push("=== Szene " + (idx + 1) + " ===");
      if (kind === "kling") {
        parts.push("motion_prompt: " + (row.motion_prompt || ""));
        parts.push("camera_path: " + (row.camera_path || ""));
        parts.push("transition_hint: " + (row.transition_hint || ""));
        parts.push("keyframe_positive: " + (row.keyframe_positive || ""));
      } else {
        parts.push("positive: " + (row.positive_optimized || row.positive_expanded || ""));
        parts.push("negative: " + (row.negative_prompt || ""));
        parts.push("continuity: " + (row.continuity_token || ""));
      }
      parts.push("");
    });
    return parts.join("\\n");
  }

  function formatThumbnailVariantsTxt() {
    var v = (lastOptimize && lastOptimize.thumbnail_variants) || (lastCtrPayload && lastCtrPayload.thumbnail_variants) || [];
    if (!v.length) return "";
    return JSON.stringify(v, null, 2);
  }

  function buildProductionPackageJson() {
    return JSON.stringify({
      version: "10.8-v1",
      timestamp: new Date().toISOString(),
      export_request: buildExportBody(),
      lastExport: lastExport,
      lastPreview: lastPreview,
      lastReadiness: lastReadiness,
      lastOptimize: lastOptimize,
      lastCtr: lastCtrPayload
    }, null, 2);
  }

  function formatAllPromptsForClipboard() {
    var op = lastOptimize.optimized_prompts;
    var blocks = [];
    blocks.push("=== LEONARDO ===");
    blocks.push(formatProviderTxt(op.leonardo, "leo"));
    blocks.push("=== OPENAI (Bild) ===");
    blocks.push(formatProviderTxt(op.openai, "leo"));
    blocks.push("=== KLING ===");
    blocks.push(formatProviderTxt(op.kling, "kling"));
    return blocks.join("\\n\\n");
  }

  var promptCardCopyData = [];

  function renderProviderPromptCards() {
    var host = $("provider-prompt-cards");
    if (!host) return;
    host.innerHTML = "";
    promptCardCopyData = [];
    if (!lastOptimize || !lastOptimize.optimized_prompts) {
      host.innerHTML = "<p class=\\"muted\\">Noch keine Optimize-Daten — zuerst „Optimize Provider Prompts“ ausführen.</p>";
      return;
    }
    var op = lastOptimize.optimized_prompts;
    var max = Math.max((op.leonardo || []).length, (op.openai || []).length, (op.kling || []).length);
    for (var i = 0; i < max; i++) {
      var leo = op.leonardo && op.leonardo[i];
      var oai = op.openai && op.openai[i];
      var kli = op.kling && op.kling[i];
      var leoT = leo ? String(leo.positive_optimized || "") : "";
      var oaiT = oai ? String(oai.positive_optimized || "") : "";
      var kT = "";
      if (kli) {
        kT = ["motion: " + (kli.motion_prompt || ""), "camera: " + (kli.camera_path || ""), "transition: " + (kli.transition_hint || ""), "keyframe: " + (kli.keyframe_positive || "")].join("\\n");
      }
      promptCardCopyData.push({ leo: leoT, openai: oaiT, kling: kT });
      var card = document.createElement("div");
      card.className = "prompt-card";
      card.innerHTML =
        "<h3>Szene " + (i + 1) + "</h3>" +
        "<div class=\\"pc-block\\"><label>Leonardo</label><pre class=\\"pc-pre\\">" + escapeHtml(leoT || "—") + "</pre>" +
        "<button type=\\"button\\" class=\\"sm pc-copy-btn\\" data-pc-idx=\\"" + i + "\\" data-pc-kind=\\"leo\\">Copy</button></div>" +
        "<div class=\\"pc-block\\"><label>Kling Motion / Kamera / Keyframe</label><pre class=\\"pc-pre\\">" + escapeHtml(kT || "—") + "</pre>" +
        "<button type=\\"button\\" class=\\"sm pc-copy-btn\\" data-pc-idx=\\"" + i + "\\" data-pc-kind=\\"kling\\">Copy</button></div>" +
        "<div class=\\"pc-block\\"><label>OpenAI</label><pre class=\\"pc-pre\\">" + escapeHtml(oaiT || "—") + "</pre>" +
        "<button type=\\"button\\" class=\\"sm pc-copy-btn\\" data-pc-idx=\\"" + i + "\\" data-pc-kind=\\"openai\\">Copy</button></div>";
      host.appendChild(card);
    }
  }

  function getInputSnapshot() {
    return {
      title: $("fd-title").value,
      topic: $("fd-topic").value,
      summary: $("fd-summary").value,
      template: $("fd-template").value,
      duration: $("fd-duration").value,
      provider: $("fd-provider").value,
      continuity_lock: $("fd-lock").checked,
      chapters_json: $("fd-chapters").value
    };
  }

  function persistSessionSnapshotSilent() {
    try {
      var pack = {
        timestamp: new Date().toISOString(),
        input: getInputSnapshot(),
        lastExport: lastExport,
        lastPreview: lastPreview,
        lastReadiness: lastReadiness,
        lastOptimize: lastOptimize,
        lastCtr: lastCtrPayload
      };
      localStorage.setItem(LS_SNAPSHOT_KEY, JSON.stringify(pack));
      return true;
    } catch (e) {
      return false;
    }
  }

  function resetPipelineTimeline() {
    var lis = document.querySelectorAll("#pipeline-timeline li.pipe-step");
    for (var k = 0; k < lis.length; k++) {
      lis[k].className = "pipe-step pending";
      var m = lis[k].querySelector(".ps-msg");
      if (m) m.textContent = "";
    }
  }

  function setPipelineStep(idx, status, msg) {
    var lis = document.querySelectorAll("#pipeline-timeline li.pipe-step");
    var li = lis[idx];
    if (!li) return;
    var cls = "pending";
    if (status === "active") cls = "active";
    else if (status === "done") cls = "done";
    else if (status === "err") cls = "err";
    li.className = "pipe-step " + cls;
    var m = li.querySelector(".ps-msg");
    if (m) m.textContent = msg || "";
  }

  function buildRawHeadline(raw, topicOpt) {
    var tOpt = String(topicOpt || "").trim();
    if (tOpt) return tOpt.length > 72 ? (tOpt.slice(0, 69).trim() + "…") : tOpt;
    var t = String(raw || "").replace(/^[\\s\\-–—•*#]+/, "");
    t = t.replace(/\\s+/g, " ").trim();
    if (!t) return "Rohtext";
    var chunks = t.match(/[^.!?]{6,}?[.!?]+|[^.!?]{12,}$/g);
    var first = (chunks && chunks[0]) ? chunks[0].trim() : t;
    if (first.length < 10 && chunks && chunks.length > 1) first = (chunks[0] + " " + chunks[1]).trim().replace(/\\s+/g, " ");
    if (first.length > 60) {
      first = first.slice(0, 57);
      var sp = first.lastIndexOf(" ");
      if (sp > 15) first = first.slice(0, sp);
      first = first.trim() + "…";
    }
    var c = first.charAt(0).toUpperCase() + first.slice(1);
    return c.trim() || "Rohtext";
  }

  function buildRawSourceSummary(raw) {
    var t = String(raw || "").trim().replace(/\\s+/g, " ");
    if (!t) return "";
    var chunks = t.match(/[^.!?]{8,}?[.!?]+|[^.!?]{14,}$/g);
    if (!chunks || !chunks.length) chunks = [t];
    var take = chunks.slice(0, 3).join(" ").trim();
    if (take.length > 480) {
      take = take.slice(0, 440);
      var sp = take.lastIndexOf(" ");
      if (sp > 80) take = take.slice(0, sp);
      take = take.trim() + " …";
    }
    return take;
  }

  function rawTextToChapters(raw) {
    var t = String(raw || "").trim();
    if (!t) return [{ title: "Kapitel 1", content: "" }];
    var paras = t.replace(/\\r\\n/g, "\\n").split(/\\n\\s*\\n+/).map(function(p) { return p.trim(); }).filter(Boolean);
    if (!paras.length) paras = [t];
    if (paras.length === 1 && paras[0].length > 1200) {
      var one = paras[0];
      paras = [];
      var i = 0;
      while (i < one.length) {
        paras.push(one.slice(i, i + 900));
        i += 900;
      }
    }
    return paras.map(function(p, idx) {
      return { title: "Abschnitt " + (idx + 1), content: p };
    });
  }

  function buildPseudoScriptResponseFromRaw(raw) {
    var ch = rawTextToChapters(raw);
    var topicIntake = $("intake-topic") ? $("intake-topic").value.trim() : "";
    var headline = buildRawHeadline(raw, topicIntake);
    var sumShort = buildRawSourceSummary(raw);
    var full = String(raw || "");
    return {
      title: headline,
      hook: "",
      chapters: ch,
      full_script: full,
      client_summary: sumShort,
      sources: [],
      warnings: [
        "[Dashboard BA 11.0] raw_text_client_segmented: Rohtext ohne URL — Kapitel nur clientseitig segmentiert; für Extraktion News- oder YouTube-URL nutzen."
      ]
    };
  }

  function applyIntakeToForm(gen) {
    if (!gen) return;
    $("fd-title").value = String(gen.title || "");
    var topicIn = $("intake-topic").value.trim();
    if (topicIn) $("fd-topic").value = topicIn;
    var sum = "";
    if (gen.client_summary != null && String(gen.client_summary).trim()) {
      sum = String(gen.client_summary).trim();
    } else {
      sum = String(gen.full_script || "").trim();
    }
    if (!sum && gen.chapters && gen.chapters.length) {
      sum = gen.chapters.map(function(c) {
        return (c.title || "") + "\\n" + (c.content || "");
      }).join("\\n\\n");
    }
    $("fd-summary").value = sum;
    var chs = gen.chapters && gen.chapters.length ? gen.chapters : DEFAULT_CHAPTERS;
    $("fd-chapters").value = JSON.stringify(chs, null, 2);
  }

  function validateScriptResponseForIntake(gen, typ) {
    if (!gen || typeof gen !== "object") throw new Error("Ungültige Skript-Antwort vom Server.");
    if (typ === "raw" || typ === "raw_text") return;
    var hasCh = gen.chapters && Array.isArray(gen.chapters) && gen.chapters.length > 0;
    var t = gen.title != null ? String(gen.title).trim() : "";
    var fs = gen.full_script != null ? String(gen.full_script).trim() : "";
    var hook = gen.hook != null ? String(gen.hook).trim() : "";
    if (!hasCh && fs.length < 12 && t.length < 3 && hook.length < 3) {
      mergeWarnings(gen.warnings || []);
      throw new Error("Skript-Response ohne nutzbaren Inhalt (leere Kapitel/Text) — Transkript/URL prüfen oder Fehlermeldung in der Error-Bar.");
    }
  }

  function validateIntakeBeforeFullPipeline() {
    var typ = $("intake-source-type").value;
    if (typ === "youtube") {
      if (!$("intake-youtube-url").value.trim()) throw new Error("Full Pipeline: YouTube-URL im Intake ausfüllen oder Quelle wechseln.");
    } else if (typ === "news") {
      if (!$("intake-news-url").value.trim()) throw new Error("Full Pipeline: News-URL im Intake ausfüllen.");
    } else if (typ === "raw" || typ === "raw_text") {
      if ($("intake-raw-text").value.trim().length < 12) throw new Error("Full Pipeline: Rohtext mindestens ca. 12 Zeichen.");
    } else {
      throw new Error("Full Pipeline: Unbekannte Intake-Quelle.");
    }
  }

  function resetPipelineStoryOutputs() {
    lastExport = null;
    lastPreview = null;
    lastReadiness = null;
    lastOptimize = null;
    lastCtrPayload = null;
    lastNumericPq = null;
    setOut("out-export-full", null);
    setOut("out-hook", null);
    setOut("out-pq-score", null);
    setOut("out-pq-detail", null);
    setOut("out-readiness", null);
    setOut("out-leo", null);
    setOut("out-openai", null);
    setOut("out-kling", null);
    setOut("out-capcut", null);
    setOut("out-csv", null);
    setOut("out-ctr", null);
    setOut("out-ctr-raw", null);
    setOut("out-thumb-var", null);
    updatePqBadge();
    renderPromptLab();
    renderProviderPromptCards();
  }

  async function runBuildBodyFromIntake() {
    setIntakeStatus("Body aus Quelle wird geladen…", "info");
    var typ = $("intake-source-type").value;
    var tmpl = $("fd-template").value || "generic";
    var dur = Math.min(180, Math.max(1, parseInt($("fd-duration").value, 10) || 10));
    var conf = "warn";
    var gen;
    try {
      if (typ === "youtube") {
        var yu = $("intake-youtube-url").value.trim();
        if (!yu) throw new Error("YouTube URL fehlt — Feld „YouTube URL“ ausfüllen.");
        gen = await fetchJson("/youtube/generate-script", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_url: yu,
            target_language: "de",
            duration_minutes: dur,
            video_template: tmpl,
            template_conformance_level: conf
          })
        });
        validateScriptResponseForIntake(gen, typ);
      } else if (typ === "news") {
        var nu = $("intake-news-url").value.trim();
        if (!nu) throw new Error("News-URL fehlt — Feld „News URL“ ausfüllen.");
        gen = await fetchJson("/generate-script", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: nu,
            target_language: "de",
            duration_minutes: dur,
            video_template: tmpl,
            template_conformance_level: conf
          })
        });
        validateScriptResponseForIntake(gen, typ);
      } else if (typ === "raw" || typ === "raw_text") {
        var rt = $("intake-raw-text").value.trim();
        if (rt.length < 12) throw new Error("Rohtext zu kurz (min. ca. 12 Zeichen).");
        gen = buildPseudoScriptResponseFromRaw(rt);
      } else {
        throw new Error("Unbekannter Quelltyp: " + typ);
      }
      applyIntakeToForm(gen);
      mergeWarnings(gen.warnings || []);
      refreshFounderInterpretation();
      setIntakeStatus("Body aus Quelle erstellt — Eingabepanel wurde aktualisiert.", "success");
      showError("");
      openPanelAndScroll(null, "coll-input-panel");
      return gen;
    } catch (e) {
      var msg = String(e.message || e);
      setIntakeStatus("Fehler: " + msg, "err");
      throw e;
    }
  }

  async function runExportOnlyInternal() {
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
      setOut("out-pq-score", "(Report)");
      setOut("out-pq-detail", pq);
    } else {
      setOut("out-pq-score", null);
      setOut("out-pq-detail", null);
    }
    mergeWarnings(data.warnings || []);
    renderPromptLab();
    renderProviderPromptCards();
    return data;
  }

  async function runPreviewOnlyInternal() {
    const data = await fetchJson("/story-engine/export-package/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildExportBody())
    });
    lastPreview = data;
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
    setOut("out-pq-score", data.prompt_quality_score);
    setOut("out-pq-detail", { prompt_quality_score: data.prompt_quality_score, scene_count: data.scene_count });
    mergeWarnings(data.top_warnings || []);
    return data;
  }

  async function runReadinessOnlyInternal() {
    const data = await fetchJson("/story-engine/provider-readiness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildExportBody())
    });
    lastReadiness = data;
    setOut("out-readiness", data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    return data;
  }

  async function runOptimizeOnlyInternal() {
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
    renderProviderPromptCards();
    return data;
  }

  async function runCtrOnlyInternal() {
    var hook = "";
    var thumb = "";
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
    setOut("out-ctr", data.ctr_score);
    setOut("out-ctr-raw", data);
    setOut("out-thumb-var", data.thumbnail_variants || []);
    mergeWarnings(data.warnings || []);
    return data;
  }

  async function runFullPipelineOrchestrator() {
    var stepIdx = 0;
    validateIntakeBeforeFullPipeline();
    setIntakeStatus("", "");
    resetPipelineStoryOutputs();
    resetPipelineTimeline();
    try {
      stepIdx = 0;
      setPipelineStep(stepIdx, "active", "");
      await runBuildBodyFromIntake();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 1;
      setPipelineStep(stepIdx, "active", "");
      await runExportOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 2;
      setPipelineStep(stepIdx, "active", "");
      await runPreviewOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 3;
      setPipelineStep(stepIdx, "active", "");
      await runReadinessOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 4;
      setPipelineStep(stepIdx, "active", "");
      await runOptimizeOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 5;
      setPipelineStep(stepIdx, "active", "");
      await runCtrOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 6;
      setPipelineStep(stepIdx, "active", "");
      refreshFounderInterpretation();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 7;
      setPipelineStep(stepIdx, "active", "");
      await runDownloadProductionBundle();
      setPipelineStep(stepIdx, "done", "");

      persistSessionSnapshotSilent();
      showError("");
      openPanelAndScroll("coll-ops", "coll-ops");
    } catch (e) {
      setPipelineStep(stepIdx, "err", String(e.message || e));
      throw e;
    }
  }

  function applyInputSnapshot(inp) {
    if (!inp) return;
    $("fd-title").value = inp.title || "";
    $("fd-topic").value = inp.topic || "";
    $("fd-summary").value = inp.summary || "";
    if (inp.duration) $("fd-duration").value = inp.duration;
    if (inp.provider) $("fd-provider").value = inp.provider;
    $("fd-lock").checked = !!inp.continuity_lock;
    if (inp.chapters_json) $("fd-chapters").value = inp.chapters_json;
    if (inp.template) {
      var sel = $("fd-template");
      var found = false;
      for (var oi = 0; oi < sel.options.length; oi++) {
        if (sel.options[oi].value === inp.template) { sel.selectedIndex = oi; found = true; break; }
      }
      if (!found) {
        var opt = document.createElement("option");
        opt.value = inp.template;
        opt.textContent = inp.template;
        sel.appendChild(opt);
        sel.value = inp.template;
      }
    }
  }

  function repaintPanelsFromState() {
    clearWarnings();
    if (lastExport) {
      setOut("out-export-full", lastExport);
      mergeWarnings(lastExport.warnings || []);
      var pq = lastExport.prompt_quality || (lastExport.scene_prompts && lastExport.scene_prompts.prompt_quality);
      if (!lastPreview) {
        setOut("out-hook", lastExport.hook || null);
        if (pq) {
          setOut("out-pq-score", "(Report)");
          setOut("out-pq-detail", pq);
        } else {
          setOut("out-pq-score", null);
          setOut("out-pq-detail", null);
        }
        lastNumericPq = null;
        updatePqBadge();
      }
    } else {
      setOut("out-export-full", null);
      if (!lastPreview) {
        setOut("out-hook", null);
        setOut("out-pq-score", null);
        setOut("out-pq-detail", null);
        lastNumericPq = null;
        updatePqBadge();
      }
    }
    if (lastPreview) {
      lastNumericPq = lastPreview.prompt_quality_score;
      updatePqBadge();
      setOut("out-hook", {
        hook_type: lastPreview.hook_type,
        hook_score: lastPreview.hook_score,
        template_id: lastPreview.template_id,
        export_ready: lastPreview.export_ready,
        readiness_status: lastPreview.readiness_status,
        top_warnings: lastPreview.top_warnings
      });
      setOut("out-pq-score", lastPreview.prompt_quality_score);
      setOut("out-pq-detail", { prompt_quality_score: lastPreview.prompt_quality_score, scene_count: lastPreview.scene_count });
      mergeWarnings(lastPreview.top_warnings || []);
    }
    if (lastReadiness) setOut("out-readiness", lastReadiness);
    else setOut("out-readiness", null);
    if (lastOptimize) {
      var op = lastOptimize.optimized_prompts || {};
      setOut("out-leo", op.leonardo || []);
      setOut("out-openai", op.openai || []);
      setOut("out-kling", op.kling || []);
      setOut("out-capcut", lastOptimize.capcut_shotlist || []);
      setOut("out-csv", lastOptimize.csv_shotlist || []);
      setOut("out-thumb-var", lastOptimize.thumbnail_variants || []);
      mergeWarnings(lastOptimize.warnings || []);
    } else {
      setOut("out-leo", null);
      setOut("out-openai", null);
      setOut("out-kling", null);
      setOut("out-capcut", null);
      setOut("out-csv", null);
      if (!lastCtrPayload) setOut("out-thumb-var", null);
    }
    if (lastCtrPayload) {
      setOut("out-ctr", lastCtrPayload.ctr_score);
      setOut("out-ctr-raw", lastCtrPayload);
      if (!lastOptimize) setOut("out-thumb-var", lastCtrPayload.thumbnail_variants || []);
      mergeWarnings(lastCtrPayload.warnings || []);
    } else {
      setOut("out-ctr", null);
      setOut("out-ctr-raw", null);
    }
    renderPromptLab();
    renderProviderPromptCards();
    refreshWarningCenter();
    updateProductionChecklist();
  }

  async function runDownloadProductionBundle() {
    if (!lastExport || !lastOptimize) {
      throw new Error("Bitte zuerst Export Package und Optimize Provider Prompts ausführen.");
    }
    var op = lastOptimize.optimized_prompts || {};
    var jobs = [
      ["production_package.json", "application/json", buildProductionPackageJson()],
      ["briefing.md", "text/markdown", buildMarkdownBriefing()],
      ["leonardo_prompts.txt", "text/plain", formatProviderTxt(op.leonardo, "leo")],
      ["kling_motion_prompts.txt", "text/plain", formatProviderTxt(op.kling, "kling")],
      ["openai_image_prompts.txt", "text/plain", formatProviderTxt(op.openai, "leo")],
      ["thumbnail_variants.txt", "text/plain", formatThumbnailVariantsTxt()],
      ["capcut_shotlist.csv", "text/csv", arrayToCsv(lastOptimize.capcut_shotlist || [])],
      ["csv_shotlist.csv", "text/csv", arrayToCsv(lastOptimize.csv_shotlist || [])],
      ["warnings.txt", "text/plain", collectAllWarningsStrings().join("\\n")]
    ];
    for (var j = 0; j < jobs.length; j++) {
      downloadText(jobs[j][0], jobs[j][1], jobs[j][2]);
      await sleep(140);
    }
  }

  async function fetchJson(url, opts) {
    if (isKillSwitchActive()) {
      throw new Error("Kill Switch aktiv — Anfrage blockiert.");
    }
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
    var el = $(id);
    if (!el) return;
    if (id === "out-pq-score" || id === "out-ctr") {
      var emptyScore = obj === null || obj === undefined || (typeof obj === "string" && !String(obj).trim());
      if (typeof obj === "number") emptyScore = false;
      var t = emptyScore ? OUTPUT_EMPTY : String(obj);
      el.textContent = t;
      el.classList.toggle("out-empty", t === OUTPUT_EMPTY);
      return;
    }
    var text;
    if (obj === null || obj === undefined || (typeof obj === "string" && !String(obj).trim()))
      text = OUTPUT_EMPTY;
    else
      text = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
    el.textContent = text;
    el.classList.toggle("out-empty", text === OUTPUT_EMPTY);
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
    if (!t || t === OUTPUT_EMPTY) return null;
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
      leftBody.textContent = OUTPUT_EMPTY;
      rightBody.textContent = OUTPUT_EMPTY;
      leftBody.className = "lab-empty";
      rightBody.className = "lab-empty";
      return;
    }
    leftBody.className = "";
    rightBody.className = "";
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
    if (!t || !t.classList) return;
    if (t.classList.contains("pc-copy-btn")) {
      var idx = parseInt(t.getAttribute("data-pc-idx"), 10);
      var kind = t.getAttribute("data-pc-kind");
      var row = promptCardCopyData[idx];
      if (!row) return;
      var txt = kind === "leo" ? row.leo : kind === "openai" ? row.openai : row.kling;
      navigator.clipboard.writeText(txt || "").then(function() {
        t.textContent = "OK";
        setTimeout(function() { t.textContent = "Copy"; }, 900);
      }).catch(function() { showError("Clipboard nicht verfügbar"); });
      return;
    }
    if (!t.getAttribute) return;
    var preId = t.getAttribute("data-pre");
    if (!preId) return;
    var txt = getPreText(preId);
    var preEl = $(preId);
    if (preEl && preEl.classList.contains("out-empty")) return;
    if (t.classList.contains("tb-copy")) {
      if (!txt || txt === OUTPUT_EMPTY) return;
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

  var intakeBodyBtn = $("btn-intake-body");
  if (intakeBodyBtn) {
    intakeBodyBtn.addEventListener("click", async function() {
      var btn = this;
      clearWarnings();
      await withActionButton(btn, "coll-source-intake", "coll-input-panel", async function() {
        await runBuildBodyFromIntake();
      });
    });
  }

  $("btn-full-pipeline").onclick = async function() {
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-full-pipeline", "coll-full-pipeline", runFullPipelineOrchestrator);
  };

  $("lab-left").addEventListener("change", renderPromptLab);
  $("lab-right").addEventListener("change", renderPromptLab);
  $("lab-refresh").addEventListener("click", renderPromptLab);

  $("btn-export").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-export", "coll-export", async function() {
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
        setOut("out-pq-score", "(Report)");
        setOut("out-pq-detail", pq);
      } else {
        setOut("out-pq-score", null);
        setOut("out-pq-detail", null);
      }
      mergeWarnings(data.warnings || []);
      renderPromptLab();
      renderProviderPromptCards();
    });
  };

  $("btn-preview").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-preview", "coll-preview", async function() {
      const data = await fetchJson("/story-engine/export-package/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildExportBody())
      });
      lastPreview = data;
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
      setOut("out-pq-score", data.prompt_quality_score);
      setOut("out-pq-detail", { prompt_quality_score: data.prompt_quality_score, scene_count: data.scene_count });
      mergeWarnings(data.top_warnings || []);
    });
  };

  $("btn-readiness").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-readiness", "coll-readiness", async function() {
      const data = await fetchJson("/story-engine/provider-readiness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildExportBody())
      });
      lastReadiness = data;
      setOut("out-readiness", data);
      mergeWarnings(data.warnings || []);
      mergeWarnings(data.blocking_issues || []);
    });
  };

  $("btn-optimize").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-optimize", "coll-optimize", async function() {
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
      renderProviderPromptCards();
    });
  };

  $("btn-ctr").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-ctr", "coll-ctr", async function() {
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
      setOut("out-ctr", data.ctr_score);
      setOut("out-ctr-raw", data);
      setOut("out-thumb-var", data.thumbnail_variants || []);
      mergeWarnings(data.warnings || []);
    });
  };

  $("btn-formats").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-formats", "coll-formats", async function() {
      const data = await fetchJson("/story-engine/export-formats", { method: "GET" });
      setOut("out-formats", data);
      mergeWarnings(data.warnings || []);
    });
  };

  $("btn-batch-compare").onclick = async function(){
    var btn = this;
    var st = $("batch-status");
    var tbody = $("batch-tbody");
    tbody.innerHTML = "";
    clearWarnings();
    if (!templateIds.length) {
      showError("Keine Template-IDs geladen.");
      btn.classList.add("is-error");
      setTimeout(function() { btn.classList.remove("is-error"); }, 1600);
      openPanelAndScroll("coll-batch", "batch-scroll-anchor");
      return;
    }
    await withActionButton(btn, "coll-batch", "batch-scroll-anchor", async function() {
      var batchRoot = $("coll-batch");
      if (batchRoot) batchRoot.open = true;
      var base = buildExportBody();
      for (var i = 0; i < templateIds.length; i++) {
        var tid = templateIds[i];
        st.textContent = "Teste Template " + (i + 1) + " von " + templateIds.length + "…";
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
    });
  };

  $("btn-prod-bundle").onclick = async function() {
    var btn = this;
    await withActionButton(btn, "coll-ops", "coll-ops", runDownloadProductionBundle);
  };

  $("btn-copy-all-prompts").onclick = async function() {
    var btn = this;
    await withActionButton(btn, "coll-optimize", "coll-optimize", async function() {
      if (!lastOptimize || !lastOptimize.optimized_prompts) {
        throw new Error("Bitte zuerst Optimize Provider Prompts ausführen.");
      }
      var t = formatAllPromptsForClipboard();
      await navigator.clipboard.writeText(t);
    });
  };

  $("btn-snapshot-save").onclick = function() {
    var btn = this;
    if (persistSessionSnapshotSilent()) {
      btn.classList.add("is-success");
      setTimeout(function() { btn.classList.remove("is-success"); }, 1600);
      showError("");
    } else {
      showError("Snapshot speichern fehlgeschlagen.");
    }
  };

  $("btn-snapshot-load").onclick = async function() {
    var btn = this;
    await withActionButton(btn, "coll-ops", "coll-ops", async function() {
      var raw = localStorage.getItem(LS_SNAPSHOT_KEY);
      if (!raw) throw new Error("Kein Snapshot in localStorage (fd_session_snapshot_v1).");
      var pack = JSON.parse(raw);
      applyInputSnapshot(pack.input);
      lastExport = pack.lastExport || null;
      lastPreview = pack.lastPreview || null;
      lastReadiness = pack.lastReadiness || null;
      lastOptimize = pack.lastOptimize || null;
      lastCtrPayload = pack.lastCtr != null ? pack.lastCtr : (pack.lastCtrPayload || null);
      repaintPanelsFromState();
    });
  };

  $("btn-snapshot-clear").onclick = function() {
    localStorage.removeItem(LS_SNAPSHOT_KEY);
    var btn = this;
    btn.classList.add("is-success");
    setTimeout(function() { btn.classList.remove("is-success"); }, 1200);
  };

  $("btn-founder-mode").onclick = function() { applyViewMode("founder"); };
  $("btn-operator-mode").onclick = function() { applyViewMode("operator"); };
  $("btn-raw-mode").onclick = function() { applyViewMode("raw"); };
  var ks = $("fd-kill-switch");
  if (ks) {
    ks.addEventListener("change", function() {
      syncKillSwitchBanner();
      if (isKillSwitchActive()) showError("Kill Switch aktiv — neue Requests blockiert.");
      else showError("");
    });
  }
  syncKillSwitchBanner();
  var rar = $("repair-actions-row");
  if (rar) {
    rar.addEventListener("click", function(ev) {
      var btn = ev.target && ev.target.closest ? ev.target.closest("button[data-repair]") : null;
      if (!btn) return;
      runRepair(btn.getAttribute("data-repair") || "");
    });
  }
  try {
    var vm0 = sessionStorage.getItem(VIEW_MODE_KEY);
    if (vm0 === "raw") applyViewMode("raw");
    else if (vm0 === "operator") applyViewMode("operator");
    else applyViewMode("founder");
  } catch (eView) {
    applyViewMode("founder");
  }

  loadTemplates().then(function() {
    renderPromptLab();
    refreshWarningCenter();
    updateProductionChecklist();
  });
  updatePqBadge();
  refreshOperatorClarity();
})();
</script>
</body>
</html>"""
