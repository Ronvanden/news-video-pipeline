"""BA 10.6–11.2 — eingebettetes HTML/CSS/JS für GET /founder/dashboard."""


def get_founder_dashboard_html() -> str:
    """Statisches Single-Page-Dashboard; clientseitige fetch-Calls zu /story-engine/*."""
    return """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>VideoPipe · Founder Dashboard</title>
<style>
:root {
  /* BA 30.6 — Visual tokens (alias → bestehende Semantik) */
  --vp-blue: #0046FF;
  --vp-bg-dark: #0a0f1a;
  --vp-card: #1a2334;
  --vp-border: #2a3349;
  --vp-text-main: #e8edf5;
  --vp-text-muted: #8b9cb3;
  --vp-card-shadow: 0 1px 0 rgba(255, 255, 255, 0.055), 0 16px 40px rgba(0, 0, 0, 0.28);
  --bg: var(--vp-bg-dark);
  --surface: var(--vp-card);
  --border: var(--vp-border);
  --text: var(--vp-text-main);
  --muted: var(--vp-text-muted);
  --accent: var(--vp-blue);
  --danger: #f87171;
  --ok: #4ade80;
  --warn: #fbbf24;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, "Inter", sans-serif;
  background:
    radial-gradient(ellipse 85% 55% at 50% -15%, rgba(0, 70, 255, 0.16), transparent 52%),
    radial-gradient(ellipse 60% 40% at 100% 30%, rgba(0, 50, 180, 0.08), transparent 45%),
    var(--bg);
  color: var(--text);
  line-height: 1.45;
  font-size: 15px;
}
.fd-header-hero {
  padding: 1.85rem clamp(1.25rem, 3vw, 2.25rem) 1.65rem;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(22, 30, 48, 0.97) 0%, rgba(12, 16, 26, 0.94) 100%);
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem 2rem;
}
.fd-header-brand {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  min-width: min(100%, 320px);
}
.fd-logo-mark {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 10px;
  background: linear-gradient(145deg, var(--vp-blue), #0032b8);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1rem;
  font-weight: 800;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(0, 70, 255, 0.35);
}
.fd-header-brand h1 {
  margin: 0;
  font-size: clamp(1.5rem, 2.4vw, 2.05rem);
  font-weight: 680;
  letter-spacing: -0.03em;
  line-height: 1.2;
}
.fd-header-sub {
  margin: 0.55rem 0 0;
  color: rgba(224, 232, 245, 0.92);
  font-size: 1rem;
  font-weight: 450;
  max-width: 40rem;
  line-height: 1.55;
  letter-spacing: -0.015em;
}
.fd-header-tech {
  margin: 0.45rem 0 0;
  font-size: 0.72rem;
  font-weight: 450;
  color: rgba(139, 156, 179, 0.82);
  max-width: 40rem;
  line-height: 1.45;
  letter-spacing: 0.01em;
}
.fd-header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}
.vp-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  padding: 0.26rem 0.72rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 580;
  border: 1px solid rgba(54, 65, 88, 0.95);
  background: rgba(255, 255, 255, 0.025);
  color: rgba(196, 206, 220, 0.88);
  white-space: nowrap;
}
.vp-status-pill::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(139, 156, 179, 0.55);
  flex-shrink: 0;
}
.vp-status-pill--ok {
  border-color: rgba(74, 222, 128, 0.38);
  background: rgba(74, 222, 128, 0.09);
  color: #c4f5d4;
}
.vp-status-pill--ok::before {
  background: var(--ok);
  box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.18);
}
.vp-status-pill--pipeline {
  border-color: rgba(0, 70, 255, 0.32);
  background: rgba(0, 70, 255, 0.08);
  color: #b8ceff;
}
.vp-status-pill--pipeline::before {
  background: var(--vp-blue);
  box-shadow: 0 0 0 2px rgba(0, 70, 255, 0.16);
}
button.fd-header-cta.primary {
  font-size: 0.86rem;
  font-weight: 600;
  padding: 0.58rem 1.2rem;
  border-radius: 9px;
  background: linear-gradient(180deg, #1a5cff 0%, var(--accent) 100%);
  border: 1px solid rgba(100, 150, 255, 0.45);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.1) inset, 0 8px 26px rgba(0, 70, 255, 0.26);
  letter-spacing: -0.01em;
}
button.fd-header-cta.primary:hover:not(:disabled) {
  filter: brightness(1.05);
}
.fd-app-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1680px;
  margin: 0 auto;
  gap: 0;
}
@media (min-width: 960px) {
  .fd-app-shell {
    flex-direction: row;
    align-items: flex-start;
    gap: 1.25rem;
    padding: 0 clamp(1rem, 2.5vw, 1.75rem) 2rem;
    box-sizing: border-box;
  }
}
.fd-sidebar {
  flex-shrink: 0;
  padding: 1rem 1.15rem 1.15rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--vp-card-shadow);
  margin: 0 clamp(1.25rem, 3vw, 2.25rem) 0.85rem;
  box-sizing: border-box;
}
@media (min-width: 960px) {
  .fd-sidebar {
    width: min(280px, 26vw);
    min-width: 240px;
    max-width: 280px;
    margin: 0;
    align-self: flex-start;
  }
}
.fd-sidebar-brand { margin-bottom: 0.65rem; }
.fd-sidebar-logo {
  display: block;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text);
}
.fd-sidebar-tagline {
  margin: 0.28rem 0 0;
  font-size: 0.78rem;
  line-height: 1.4;
  color: rgba(139, 156, 179, 0.92);
  font-weight: 450;
}
.fd-sidebar-pill {
  margin-bottom: 0.85rem;
  font-size: 0.65rem;
}
.fd-sidebar-nav {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0 0 0.85rem;
}
@media (min-width: 960px) {
  .fd-sidebar-nav {
    flex-direction: column;
    flex-wrap: nowrap;
    gap: 0.2rem;
  }
}
button.fd-sidebar-link {
  display: inline-flex;
  align-items: center;
  width: auto;
  padding: 0.42rem 0.65rem;
  border-radius: 8px;
  border: 1px solid rgba(48, 58, 78, 0.85);
  background: rgba(0, 0, 0, 0.12);
  color: rgba(224, 232, 245, 0.92);
  font-size: 0.78rem;
  font-weight: 550;
  text-align: left;
  cursor: pointer;
  box-sizing: border-box;
}
@media (min-width: 960px) {
  button.fd-sidebar-link {
    width: 100%;
  }
}
button.fd-sidebar-link:hover:not(:disabled) {
  background: rgba(0, 70, 255, 0.12);
  border-color: rgba(0, 70, 255, 0.35);
  color: var(--text);
}
.fd-sidebar-score {
  margin-top: 0.35rem;
  padding: 0.72rem 0.65rem;
  border-radius: 10px;
  border: 1px solid rgba(48, 58, 78, 0.85);
  background: rgba(0, 0, 0, 0.14);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
.fd-sidebar-score-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.55rem;
}
.fd-sidebar-mini-gauge .fd-score-gauge-ring {
  --fd-sg-ring: 40px;
  --fd-sg-inner: 28px;
  box-shadow:
    inset 0 1px 3px rgba(0, 0, 0, 0.28),
    0 1px 0 rgba(255, 255, 255, 0.04);
}
.fd-sidebar-mini-gauge .fd-score-gauge-inner {
  padding: 0;
  border-width: 1px;
}
.fd-sidebar-score-copy {
  flex: 1;
  min-width: 0;
}
.fd-sidebar-score-k {
  display: block;
  font-size: 0.62rem;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(139, 156, 179, 0.9);
  margin-bottom: 0.15rem;
}
.fd-sidebar-score-v {
  display: block;
  font-size: 0.82rem;
  font-weight: 680;
  letter-spacing: -0.02em;
  color: rgba(236, 241, 248, 0.96);
  font-family: system-ui, -apple-system, Segoe UI, Roboto, "Inter", sans-serif;
  line-height: 1.25;
}
.fd-sidebar-score-v.fd-sidebar-score-v--empty {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(160, 176, 198, 0.9);
}
.fd-sidebar-score-footnote {
  margin: 0.45rem 0 0;
  font-size: 0.65rem;
  line-height: 1.35;
  color: rgba(139, 156, 179, 0.78);
  font-weight: 450;
}
.fd-main-column {
  flex: 1;
  min-width: 0;
}
.fd-main-column .fd-dashboard-main {
  margin: 0;
  max-width: none;
}
main.fd-dashboard-main {
  padding: 1.5rem clamp(1.25rem, 3vw, 2.25rem) 3rem;
  max-width: 1400px;
  margin: 0 auto;
}
.fd-exec-row {
  margin-bottom: 1.35rem;
}
.fd-exec-row .fp-exec-strip {
  margin-bottom: 0;
}
.fp-cockpit-primary {
  border-color: rgba(0, 70, 255, 0.32);
  background: linear-gradient(165deg, rgba(28, 38, 58, 0.92) 0%, rgba(22, 29, 44, 0.98) 48%, rgba(20, 26, 40, 1) 100%);
  box-shadow: var(--vp-card-shadow), 0 0 0 1px rgba(0, 70, 255, 0.07);
}
.fp-cockpit-panel-head {
  border-bottom-color: rgba(42, 51, 73, 0.9);
}
.fp-cockpit-split {
  display: grid;
  gap: 1.35rem;
  align-items: start;
}
@media (min-width: 1024px) {
  .fp-cockpit-split {
    grid-template-columns: minmax(300px, 0.92fr) minmax(340px, 1.08fr);
  }
}
.fp-cockpit-col { min-width: 0; }
.fp-cockpit-col--actions .fp-dry-run-card {
  margin-bottom: 0;
  height: 100%;
  min-height: 100%;
  background: rgba(0, 0, 0, 0.18);
  border-color: rgba(0, 70, 255, 0.22);
}
.fp-cockpit-col--snapshot {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.fp-cockpit-col--snapshot .fp-readiness-banner {
  margin-top: 0;
}
.fp-btn-dry-run.primary {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.58rem 1.22rem;
  border-radius: 9px;
  background: linear-gradient(180deg, #1a5cff 0%, var(--accent) 100%);
  border: 1px solid rgba(100, 150, 255, 0.5);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.1) inset, 0 10px 28px rgba(0, 70, 255, 0.3);
  letter-spacing: -0.01em;
}
.fp-btn-dry-run.primary:hover:not(:disabled) {
  filter: brightness(1.06);
}
button.fp-btn-secondary {
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(48, 58, 78, 0.95);
  color: rgba(224, 232, 245, 0.9);
  font-weight: 520;
  box-shadow: none;
}
button.fp-btn-secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.055);
  border-color: rgba(0, 70, 255, 0.32);
}
.panel--founder-secondary {
  opacity: 0.97;
  border-color: rgba(42, 51, 73, 0.75);
}
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
.export-action-status { min-height: 1.1rem; margin: 0.35rem 0 0; font-size: 0.82rem; }
.export-action-status.export-action-ok { color: var(--ok); font-weight: 600; }
.export-action-status.export-action-err { color: #fecaca; font-weight: 600; }
.export-action-status.export-action-info { color: var(--muted); }
.grid { display: grid; gap: 1rem; }
@media (min-width: 900px) {
  .grid-2 { grid-template-columns: 1fr 1fr; }
}
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.35rem;
  box-shadow: var(--vp-card-shadow);
}
.panel h2, .subh {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.panel-section-head {
  margin-bottom: 1rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid rgba(36, 43, 61, 0.85);
}
.panel-section-head h2 {
  margin-bottom: 0.35rem;
}
.panel-section-desc {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.45;
}
.fp-cockpit-panel-head h2#fp-snapshot-h {
  font-size: 1.08rem;
  font-weight: 650;
  letter-spacing: -0.025em;
  text-transform: none;
  color: var(--text);
}
.fp-cockpit-panel-head .panel-section-desc {
  font-size: 0.88rem;
  line-height: 1.55;
  color: rgba(196, 206, 220, 0.88);
}
.fp-inline-path {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.82em;
  font-weight: 450;
  padding: 0.1rem 0.32rem;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(42, 51, 73, 0.85);
}
.panel--fresh-preview {
  border-color: rgba(0, 70, 255, 0.22);
  box-shadow: var(--vp-card-shadow), 0 0 0 1px rgba(0, 70, 255, 0.06);
}
.lp-section {
  border: 1px solid rgba(45, 58, 77, 0.65);
  border-radius: 10px;
  padding: 0.75rem;
  margin-top: 0.6rem;
  background: rgba(15, 20, 25, 0.25);
}
.lp-section .subh { margin-top: 0; }
.lp-grid-2 { display: grid; gap: 0.75rem; }
@media (min-width: 900px) { .lp-grid-2 { grid-template-columns: 1.1fr 0.9fr; } }
.lp-inline-actions { display:flex; flex-wrap:wrap; gap:0.5rem; align-items:center; }
.lp-hint { margin: 0.2rem 0 0; font-size: 0.82rem; color: var(--muted); }
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
  border-color: #0038d9;
  color: #fff;
  font-weight: 600;
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
  border-radius: 12px;
  margin-bottom: 0.75rem;
  padding: 0.35rem 0.75rem 0.75rem;
  box-shadow: var(--vp-card-shadow);
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
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
  margin: 0.5rem 0 0.75rem;
  font-weight: 700;
  font-size: 0.95rem;
  border: 1px solid var(--border);
  background: rgba(0, 70, 255, 0.1);
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
.pipe-timeline li.pipe-step.active::before { background: var(--accent); box-shadow: 0 0 0 3px rgba(0, 70, 255, 0.28); }
.pipe-timeline li.pipe-step.done { color: var(--ok); }
.pipe-timeline li.pipe-step.done::before { background: var(--ok); }
.pipe-timeline li.pipe-step.err { color: var(--danger); }
.pipe-timeline li.pipe-step.err::before { background: var(--danger); }
.pipe-timeline .ps-msg { display: block; font-size: 0.72rem; font-weight: normal; margin-top: 0.15rem; color: var(--danger); }
.intake-type-row { margin-bottom: 0.75rem; }
.lp-action-list .lp-act { margin-bottom: 0.75rem; }
.lp-action-list .lp-act h4 { margin: 0 0 0.3rem; font-size: 0.78rem; color: var(--muted); font-weight: 600; }
.lp-action-list pre { margin: 0; max-height: 120px; }
.lp-cards { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.85rem; }
.lp-card {
  flex: 1 1 120px;
  min-width: 100px;
  max-width: 180px;
  padding: 0.45rem 0.55rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  font-size: 0.72rem;
}
.lp-card .lp-card-l { color: var(--muted); display: block; margin-bottom: 0.2rem; }
.lp-card .lp-card-v { font-weight: 700; font-size: 0.78rem; }
.lp-top-issue { font-size: 0.8rem; margin: 0.35rem 0; color: var(--text); }
.lp-next-step { font-size: 0.78rem; color: var(--muted); margin: 0 0 0.5rem; }
.lp-preview-btns { display: flex; flex-wrap: wrap; gap: 0.45rem; margin: 0.35rem 0 0.65rem; align-items: center; }
.lp-preview-btns a { font-size: 0.78rem; color: var(--accent); text-decoration: underline; }
.lp-preview-video-wrap { margin-top: 0.35rem; }
.lp-preview-video-wrap video.lp-preview-video {
  max-width: 100%;
  max-height: 300px;
  display: block;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #000;
}
.fp-exec-strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.65rem;
  margin-bottom: 1rem;
}
.fp-exec-cell {
  border-radius: 11px;
  border: 1px solid rgba(42, 51, 73, 0.75);
  background: linear-gradient(165deg, rgba(32, 40, 58, 0.52) 0%, rgba(18, 24, 38, 0.78) 100%);
  padding: 0.75rem 0.88rem;
  min-height: 4.35rem;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04) inset, 0 10px 28px rgba(0, 0, 0, 0.18);
}
.fp-exec-label {
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(139, 156, 179, 0.88);
  margin-bottom: 0.35rem;
}
.fp-exec-val {
  font-size: 0.98rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.3;
  word-break: break-word;
  color: var(--text);
}
.fp-exec-hint {
  font-size: 0.72rem;
  font-weight: 450;
  line-height: 1.42;
  color: rgba(139, 156, 179, 0.9);
  margin-top: 0.42rem;
}
.fp-exec-readiness-body {
  display: flex;
  align-items: flex-start;
  gap: 0.55rem;
}
.fp-exec-readiness-copy {
  flex: 1;
  min-width: 0;
}
.fp-exec-mini-gauge {
  flex-shrink: 0;
  margin-top: 0.1rem;
}
.fp-readiness-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem 1rem;
  padding: 0.78rem 1rem;
  margin: 0 0 0.85rem;
  border-radius: 11px;
  border: 1px solid rgba(48, 58, 78, 0.92);
  background: rgba(12, 16, 26, 0.55);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.035) inset;
}
.fp-readiness-row { margin: 0; display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; flex: 1; min-width: 140px; }
.fp-readiness-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.3rem 0.72rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 650;
  letter-spacing: 0.05em;
  border: 1px solid rgba(54, 65, 88, 0.9);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.05) inset;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, "Inter", sans-serif;
}
.fp-readiness-ready { background: rgba(34, 120, 80, 0.45); color: #c8ffd8; border-color: rgba(74, 222, 128, 0.45); }
.fp-readiness-warning { background: rgba(140, 100, 30, 0.42); color: #ffe0a8; border-color: rgba(251, 191, 36, 0.45); }
.fp-readiness-blocked { background: rgba(120, 40, 40, 0.42); color: #ffc8c8; border-color: rgba(248, 113, 113, 0.45); }
.fp-readiness-unknown { background: rgba(255, 255, 255, 0.04); color: var(--muted); }
.fp-readiness-score-wrap { font-size: 0.86rem; font-weight: 550; color: rgba(224, 232, 245, 0.92); letter-spacing: -0.01em; }
.fp-readiness-footnote {
  margin: 0.35rem 0 0;
  font-size: 0.72rem;
  line-height: 1.4;
  color: rgba(139, 156, 179, 0.88);
  font-weight: 450;
}
/* BA 30.6d — wiederverwendbares Score-Gauge (Preview Power + weitere 0–100-Werte) */
.fd-score-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}
.fd-score-gauge--large {
  gap: 0.42rem;
}
.fd-score-gauge--large .fd-score-gauge-ring {
  --fd-sg-ring: 118px;
  --fd-sg-inner: 86px;
}
.fd-score-gauge--small .fd-score-gauge-ring {
  --fd-sg-ring: 44px;
  --fd-sg-inner: 32px;
}
.fd-score-gauge-caption {
  margin: 0;
  font-size: 0.63rem;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: rgba(154, 168, 188, 0.9);
  text-align: center;
}
.fd-score-gauge-footnote {
  margin: 0;
  max-width: 11.5rem;
  font-size: 0.68rem;
  line-height: 1.4;
  font-weight: 450;
  color: rgba(139, 156, 179, 0.82);
  text-align: center;
}
.fd-score-gauge-ring {
  --fd-sg-pct: 0;
  --fd-sg-accent: rgba(120, 135, 158, 0.42);
  --fd-sg-track: rgba(28, 34, 48, 0.88);
  width: var(--fd-sg-ring);
  height: var(--fd-sg-ring);
  border-radius: 50%;
  background: conic-gradient(from -90deg, var(--fd-sg-accent) calc(var(--fd-sg-pct) * 1%), var(--fd-sg-track) 0);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    inset 0 2px 5px rgba(0, 0, 0, 0.32),
    0 1px 0 rgba(255, 255, 255, 0.05),
    0 6px 18px rgba(0, 0, 0, 0.16);
}
.fd-score-gauge-inner {
  width: var(--fd-sg-inner);
  height: var(--fd-sg-inner);
  border-radius: 50%;
  background: radial-gradient(circle at 32% 22%, rgba(55, 65, 88, 0.45) 0%, rgba(16, 20, 32, 0.98) 55%, rgba(10, 14, 22, 1) 100%);
  border: 1px solid rgba(55, 65, 88, 0.55);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.28rem 0.32rem;
  text-align: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
.fd-score-gauge-value {
  font-size: 1.32rem;
  font-weight: 680;
  letter-spacing: -0.035em;
  color: rgba(244, 247, 252, 0.98);
  line-height: 1.02;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, "Inter", sans-serif;
}
.fd-score-gauge-value.fd-score-gauge-value--empty {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1.2;
  color: rgba(176, 188, 206, 0.92);
  text-transform: none;
}
.fd-score-gauge-label {
  font-size: 0.6rem;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(154, 168, 188, 0.82);
  margin-top: 0.28rem;
  line-height: 1.2;
  max-width: 5.5rem;
}
.fd-score-gauge-ring--ready {
  --fd-sg-accent: rgba(56, 189, 172, 0.82);
  --fd-sg-track: rgba(45, 110, 100, 0.22);
}
.fd-score-gauge-ring--ready .fd-score-gauge-inner {
  border-color: rgba(56, 189, 172, 0.22);
}
.fd-score-gauge-ring--ready .fd-score-gauge-label { color: rgba(153, 230, 216, 0.88); }
.fd-score-gauge-ring--warning {
  --fd-sg-accent: rgba(217, 165, 70, 0.88);
  --fd-sg-track: rgba(110, 85, 40, 0.2);
}
.fd-score-gauge-ring--warning .fd-score-gauge-label { color: rgba(253, 224, 138, 0.88); }
.fd-score-gauge-ring--blocked {
  --fd-sg-accent: rgba(220, 110, 110, 0.82);
  --fd-sg-track: rgba(95, 45, 45, 0.22);
}
.fd-score-gauge-ring--blocked .fd-score-gauge-label { color: rgba(254, 202, 202, 0.88); }
.fd-score-gauge-ring--neutral {
  --fd-sg-accent: rgba(118, 132, 155, 0.38);
  --fd-sg-track: rgba(30, 36, 50, 0.9);
}
.fp-preview-power-host {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 118px;
}
.fp-preview-power-title { margin: 0; }
.fp-toolbar { margin: 0 0 0.35rem; display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
.fp-toolbar .sm.primary { font-weight: 600; }
.fp-next-step-box {
  border-radius: 11px;
  padding: 1.05rem 1.12rem;
  margin: 0.55rem 0 0.85rem;
  border: 1px solid rgba(54, 65, 88, 0.95);
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.24);
}
.fp-next-step--blocked { border-color: rgba(248, 113, 113, 0.42); background: rgba(120, 40, 40, 0.14); }
.fp-next-step--warning { border-color: rgba(251, 191, 36, 0.42); background: rgba(140, 100, 30, 0.12); }
.fp-next-step--ready { border-color: rgba(74, 222, 128, 0.42); background: rgba(34, 120, 80, 0.14); }
.fp-next-step--neutral { background: rgba(0, 0, 0, 0.18); }
.fp-next-step-label { font-size: 0.64rem; font-weight: 650; text-transform: uppercase; letter-spacing: 0.09em; color: rgba(139, 156, 179, 0.92); margin-bottom: 0.55rem; }
.fp-next-step-text { font-size: 0.96rem; line-height: 1.55; font-weight: 540; color: rgba(240, 244, 250, 0.96); }
.fp-path-grid { display: flex; flex-direction: column; gap: 0.5rem; margin: 0.55rem 0 0.65rem; font-size: 0.82rem; }
.fp-path-row { display: grid; grid-template-columns: minmax(100px, 132px) 1fr auto auto; gap: 0.45rem 0.55rem; align-items: center; }
@media (max-width: 720px) { .fp-path-row { grid-template-columns: 1fr; align-items: start; } }
a.fp-open-artifact {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.22rem 0.52rem;
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid rgba(0, 70, 255, 0.35);
  background: rgba(0, 70, 255, 0.1);
  color: #b8ceff;
  text-decoration: none;
  white-space: nowrap;
}
a.fp-open-artifact:hover {
  background: rgba(0, 70, 255, 0.18);
  border-color: rgba(0, 70, 255, 0.5);
  color: var(--text);
}
.fp-open-placeholder { min-width: 3.25rem; }
.fp-path-label { font-weight: 650; color: var(--muted); font-size: 0.78rem; }
.fp-path-value {
  word-break: break-all;
  font-family: ui-monospace, monospace;
  font-size: 0.76rem;
  padding: 0.4rem 0.55rem;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(36, 43, 61, 0.9);
  color: var(--text);
}
.fp-reasons-stack { display: flex; flex-direction: column; gap: 0.65rem; margin: 0.5rem 0 0.75rem; }
.fp-reasons-block { margin: 0; font-size: 0.84rem; border-radius: 10px; padding: 0.72rem 0.88rem; border: 1px solid rgba(48, 58, 78, 0.85); background: rgba(0, 0, 0, 0.14); line-height: 1.45; }
.fp-reasons-block ul { margin: 0.3rem 0 0 1.1rem; padding: 0; }
.fp-reasons-title { font-weight: 650; margin: 0; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em; color: rgba(196, 206, 220, 0.82); }
.fp-blocking { border-color: rgba(248, 113, 113, 0.32); background: rgba(120, 40, 40, 0.09); }
.fp-blocking .fp-reasons-title { color: #f0a8a8; }
.fp-readiness { border-color: rgba(251, 191, 36, 0.32); background: rgba(140, 100, 30, 0.08); }
.fp-readiness .fp-reasons-title { color: #f5d78a; }
.fp-scan { border-color: rgba(139, 156, 179, 0.28); background: rgba(255, 255, 255, 0.02); }
.fp-scan .fp-reasons-title { color: rgba(160, 176, 198, 0.88); }
button.fp-copy-path {
  padding: 0.16rem 0.4rem;
  font-size: 0.61rem;
  font-weight: 600;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(48, 58, 78, 0.95);
  color: rgba(180, 194, 212, 0.95);
  align-self: center;
}
button.fp-copy-path:hover:not(:disabled) {
  border-color: rgba(0, 70, 255, 0.45);
  color: var(--text);
}
button.fp-copy-path:disabled { opacity: 0.45; cursor: not-allowed; }
.fp-dry-run-card {
  margin-bottom: 1.25rem;
  padding: 1rem 1.15rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 70, 255, 0.28);
  background: rgba(0, 0, 0, 0.2);
}
.fp-dry-run-card .subh { margin-top: 0; }
.fp-module-title {
  font-size: 0.7rem !important;
  font-weight: 650 !important;
  text-transform: uppercase;
  letter-spacing: 0.07em !important;
  color: rgba(196, 206, 220, 0.78) !important;
  margin-bottom: 0.7rem !important;
  padding-bottom: 0.55rem;
  border-bottom: 1px solid rgba(42, 51, 73, 0.85);
}
.fp-dry-run-meta {
  margin: 0 0 1rem;
  font-size: 0.75rem;
  line-height: 1.5;
  font-weight: 450;
  color: rgba(139, 156, 179, 0.94);
  padding: 0;
  border: none;
  background: transparent;
}
.fp-dry-run-grid { display: grid; gap: 0.15rem 1rem; }
@media (min-width: 720px) {
  .fp-dry-run-grid { grid-template-columns: 1fr 1fr; }
}
.fp-dry-run-actions { margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
#fp-dry-run-status { min-height: 1.2rem; margin: 0.5rem 0 0; font-size: 0.82rem; }
#fp-dry-run-result { margin-top: 0.5rem; }
.fp-dry-run-handoff {
  margin-top: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 70, 255, 0.35);
  background: rgba(0, 70, 255, 0.08);
}
.fp-handoff-h { margin: 0 0 0.5rem; font-size: 0.82rem; color: var(--text); }
.fp-handoff-note, .fp-handoff-warning { margin: 0 0 0.45rem; font-size: 0.78rem; line-height: 1.45; }
#fp-dry-run-handoff-ps { margin: 0.5rem 0; max-height: 220px; font-size: 0.72rem; }
</style>
</head>
<body>
  <header class="fd-header-hero" id="fd-overview-anchor">
    <div class="fd-header-brand">
      <div class="fd-logo-mark" aria-hidden="true">▶</div>
      <div>
        <h1>VideoPipe Founder Cockpit</h1>
        <p class="fd-header-sub">Start, prüfe und steuere Fresh Preview Runs aus einem ruhigen Operator-Cockpit.</p>
        <p class="fd-header-tech">Lokaler Snapshot · Dry-Run ohne Live-Provider · read-only</p>
      </div>
    </div>
    <div class="fd-header-actions">
      <span class="vp-status-pill vp-status-pill--ok" title="Lokaler Produktions- und Preview-Pfad vorbereitet">Production Ready</span>
      <span class="vp-status-pill vp-status-pill--pipeline" title="Lokale Preview-Pipeline ohne externe Provider-Calls">Local Preview Pipeline</span>
      <button type="button" class="primary fd-header-cta" id="fd-header-cta-local-preview" data-ba306-header-cta="1">Zum Fresh Preview Panel</button>
    </div>
  </header>
<div class="fd-app-shell" data-ba306c-sidebar="1">
  <aside id="fd-sidebar" class="fd-sidebar" aria-label="Hauptnavigation">
    <div class="fd-sidebar-brand">
      <span class="fd-sidebar-logo">VideoPipe</span>
      <p class="fd-sidebar-tagline">Founder Cockpit</p>
    </div>
    <span class="vp-status-pill vp-status-pill--pipeline fd-sidebar-pill" title="Lokale Preview-Pipeline ohne externe Provider-Calls">Local Preview Pipeline</span>
    <nav id="fd-sidebar-nav" class="fd-sidebar-nav" aria-label="Bereiche">
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="fd-overview-anchor">Overview</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="panel-ba303-fresh-preview">Fresh Preview</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="panel-ba303-fresh-preview">Readiness</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="fp-dry-run-handoff">Handoff</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="panel-ba22-local-preview">Local Preview</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="founder-strategic-summary">Founder Summary</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="coll-input-panel">Raw / Debug</button>
    </nav>
    <div class="fd-sidebar-score" data-ba306d-score-gauge="sidebar" aria-live="polite">
      <div class="fd-sidebar-score-row">
        <div class="fd-sidebar-mini-gauge fd-score-gauge fd-score-gauge--small" aria-hidden="true">
          <div class="fd-score-gauge-ring fd-score-gauge-ring--neutral" id="fd-sidebar-preview-power-ring" style="--fd-sg-pct: 0">
            <div class="fd-score-gauge-inner"></div>
          </div>
        </div>
        <div class="fd-sidebar-score-copy">
          <span class="fd-sidebar-score-k">Preview Power</span>
          <span class="fd-sidebar-score-v fd-sidebar-score-v--empty" id="fd-sidebar-preview-power">Noch kein Score</span>
        </div>
      </div>
      <p class="fd-sidebar-score-footnote">Score basiert auf Fresh Preview Readiness</p>
    </div>
  </aside>
  <div class="fd-main-column">
<main class="fd-dashboard-main">
  <div id="error-bar" role="alert"></div>

  <div class="fd-exec-row" data-ba306b-exec-row="1">
    <div class="fp-exec-strip" id="fp-exec-strip" data-ba306-exec-strip="1" aria-label="Executive Kurzüberblick Fresh Preview">
      <div class="fp-exec-cell"><div class="fp-exec-label">Fresh Preview Status</div><div class="fp-exec-val" id="fp-exec-fresh-status">Warte auf Snapshot</div><div class="fp-exec-hint" id="fp-exec-hint-fresh"></div></div>
      <div class="fp-exec-cell"><div class="fp-exec-label">Readiness Score</div><div class="fp-exec-readiness-body"><div class="fp-exec-mini-gauge fd-score-gauge fd-score-gauge--small" aria-hidden="true"><div class="fd-score-gauge-ring fd-score-gauge-ring--neutral" id="fp-exec-readiness-ring" style="--fd-sg-pct: 0"><div class="fd-score-gauge-inner"></div></div></div><div class="fp-exec-readiness-copy"><div class="fp-exec-val" id="fp-exec-readiness-score">Nicht bewertet</div><div class="fp-exec-hint" id="fp-exec-hint-score">Readiness wird nach dem Snapshot berechnet</div></div></div></div>
      <div class="fp-exec-cell"><div class="fp-exec-label">Latest Run</div><div class="fp-exec-val" id="fp-exec-latest-run">Noch kein Run</div><div class="fp-exec-hint" id="fp-exec-hint-run"></div></div>
      <div class="fp-exec-cell"><div class="fp-exec-label">Next Operator Step</div><div class="fp-exec-val" id="fp-exec-next-step-short">Starte einen Dry-Run, um den ersten Snapshot zu erzeugen</div><div class="fp-exec-hint" id="fp-exec-hint-next"></div></div>
    </div>
  </div>

  <section class="panel panel--fresh-preview fp-cockpit-primary" id="panel-ba303-fresh-preview" aria-labelledby="fp-snapshot-h">
    <div class="panel-section-head fp-cockpit-panel-head">
      <h2 id="fp-snapshot-h">Fresh Preview Smoke (BA 30.3–30.8)</h2>
      <p class="panel-section-desc muted">Read-only Snapshot unter <code class="fp-inline-path">output/fresh_topic_preview/</code> · Ready, Warning oder Blocked auf einen Blick · Dry-Run und Aktualisieren an einem Ort.</p>
    </div>
    <div class="fp-cockpit-split">
      <div class="fp-cockpit-col fp-cockpit-col--actions">
        <div class="fp-dry-run-card" id="fp-dry-run-panel" data-ba307-dry-run-panel="1" aria-labelledby="fp-dry-run-h">
          <h3 class="subh fp-module-title" id="fp-dry-run-h">Fresh Preview starten</h3>
          <p class="fp-dry-run-meta">Dry-Run: keine Live-Provider, keine externen Asset-Kosten.</p>
          <div class="fp-dry-run-grid">
            <div>
              <label for="fp-dry-topic">Topic</label>
              <input type="text" id="fp-dry-topic" placeholder="Thema (exklusiv zu URL)" autocomplete="off"/>
            </div>
            <div>
              <label for="fp-dry-url">URL</label>
              <input type="text" id="fp-dry-url" placeholder="Artikel-URL (exklusiv zu Topic)" autocomplete="off"/>
            </div>
            <div>
              <label for="fp-dry-duration">Dauer (Sekunden)</label>
              <input type="number" id="fp-dry-duration" min="5" max="900" value="45"/>
            </div>
            <div>
              <label for="fp-dry-max-scenes">Max. Szenen</label>
              <input type="number" id="fp-dry-max-scenes" min="1" max="40" value="6"/>
            </div>
          </div>
          <div class="fp-dry-run-actions">
            <button type="button" class="primary fp-btn-dry-run" id="fp-btn-start-dry-run" data-label="Dry-Run starten" data-ba307-start-dry-run="1">Dry-Run starten</button>
          </div>
          <p class="muted" id="fp-dry-run-status" aria-live="polite"></p>
          <pre class="out out-empty" id="fp-dry-run-result" style="display:none;max-height:180px" data-ba307-dry-run-result="1"></pre>
          <div id="fp-dry-run-handoff" class="fp-dry-run-handoff" style="display:none" data-ba308-handoff="1" aria-labelledby="fp-handoff-heading">
            <h4 class="subh fp-handoff-h" id="fp-handoff-heading">Nächster Schritt: Full Preview Smoke lokal starten</h4>
            <p class="fp-handoff-note muted" id="fp-handoff-note"></p>
            <p class="fp-handoff-warning" id="fp-handoff-warning"></p>
            <pre class="out" id="fp-dry-run-handoff-ps"></pre>
            <button type="button" class="sm fp-copy-path" id="fp-btn-copy-handoff-cli" data-ba308-copy-handoff="1">CLI-Befehl kopieren</button>
          </div>
        </div>
      </div>
      <div class="fp-cockpit-col fp-cockpit-col--snapshot">
        <div class="fp-readiness-banner">
          <div class="fp-preview-power-host fd-score-gauge fd-score-gauge--large" id="fp-preview-power-gauge" data-ba306c-preview-power="1" data-ba306d-score-gauge="cockpit" aria-label="Preview Power Readiness">
            <p class="fp-preview-power-title fd-score-gauge-caption">Preview Power</p>
            <div class="fp-preview-power-ring fd-score-gauge-ring fd-score-gauge-ring--neutral" id="fp-preview-power-ring" style="--fd-sg-pct: 0">
              <div class="fp-preview-power-inner fd-score-gauge-inner">
                <span class="fp-preview-power-value fd-score-gauge-value fd-score-gauge-value--empty" id="fp-preview-power-value">Noch kein Score</span>
                <span class="fp-preview-power-label fd-score-gauge-label" id="fp-preview-power-label"></span>
              </div>
            </div>
            <p class="fd-score-gauge-footnote">Score basiert auf Fresh Preview Readiness</p>
          </div>
          <div class="fp-readiness-row" id="fp-readiness-row" data-ba304-readiness-marker="1">
            <span id="fp-readiness-badge" class="fp-readiness-badge fp-readiness-unknown" title="BA 30.4 Readiness Gate">OFFEN</span>
            <span id="fp-readiness-score" class="fp-readiness-score-wrap">Readiness wird nach dem Snapshot berechnet</span>
          </div>
          <p class="fp-readiness-footnote muted">Score basiert auf Fresh Preview Readiness</p>
        </div>
        <div class="fp-toolbar">
          <button type="button" class="primary" id="fp-btn-refresh" data-label="Fresh Preview aktualisieren" data-ba305-refresh="1">Fresh Preview aktualisieren</button>
        </div>
        <p class="muted" id="fp-snapshot-status" style="margin:0.25rem 0 0.5rem;font-size:0.82rem">Lade Snapshot…</p>
        <div id="fp-next-step-box" class="fp-next-step-box fp-next-step--neutral" data-ba305-next-step="1" data-operator-next-step-host="1" data-field="operator_next_step" role="status">
          <div class="fp-next-step-label">Nächster Schritt (Operator)</div>
          <div id="fp-operator-next-step" class="fp-next-step-text">—</div>
        </div>
        <div id="fp-path-rows" class="fp-path-grid" data-ba305-copy-markers="1" data-ba309-artifact-open="1" aria-label="Fresh Preview Pfade"></div>
        <div id="fp-reasons-wrap" class="fp-reasons-stack">
          <div id="fp-blocking-list" class="fp-reasons-block fp-blocking" style="display:none"></div>
          <div id="fp-readiness-list" class="fp-reasons-block fp-readiness" style="display:none"></div>
          <div id="fp-scan-warnings-list" class="fp-reasons-block fp-scan" style="display:none"></div>
        </div>
        <pre class="out out-empty" id="out-fp-snapshot" style="max-height:200px" data-fp-snapshot-marker="ba303">Noch kein Fresh Preview Run gefunden. Starte einen Dry-Run, um den ersten Snapshot zu erzeugen. Technische Kurzübersicht erscheint danach hier (read-only).</pre>
      </div>
    </div>
  </section>

  <section class="panel panel--founder-secondary" id="founder-strategic-summary">
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

  <section class="panel" id="panel-ba22-local-preview" aria-labelledby="lp-panel-h">
    <h2 id="lp-panel-h">Local Preview (BA 22.0–22.6) · Founder Summary · Operator Controls</h2>
    <p class="muted" id="lp-panel-status">Lade Panel…</p>
    <div id="lp-panel-body" style="display:none">
      <p class="muted" id="lp-out-root"></p>

      <div class="lp-section" id="lp-founder-summary">
        <h3 class="subh">Founder Summary (Verdict / Quality / Founder decision)</h3>
        <div id="lp-latest-cards" aria-live="polite"></div>
        <p class="lp-top-issue" id="lp-top-issue" style="display:none"></p>
        <p class="lp-next-step" id="lp-next-step" style="display:none"></p>
      </div>

      <div class="lp-grid-2">
        <div class="lp-section" id="lp-preview-actions">
          <h3 class="subh">Preview Actions</h3>
          <div class="lp-inline-actions">
            <button type="button" class="primary" id="lp-btn-run-mini" data-label="Preview erstellen">Preview erstellen</button>
            <span class="muted" id="lp-run-status" aria-live="polite" style="font-size:0.82rem"></span>
          </div>
          <p class="lp-hint">Danach: Preview/Report/OPEN_ME/JSON über die Links öffnen.</p>
          <div id="lp-preview-toolbar" class="lp-preview-btns" aria-label="Preview Artefakte"></div>
          <div id="lp-preview-video-wrap" class="lp-preview-video-wrap"></div>
        </div>

        <div class="lp-section" id="lp-quality-diagnostics">
          <h3 class="subh">Quality & Diagnostics</h3>
          <span class="muted" style="display:none">Kosten-Schätzung (BA 22.4)</span>
          <p class="lp-hint">Qualität, Warnstufe, Kosten — ohne externe Calls.</p>
          <div id="lp-cost-card" class="lp-cost-card" aria-live="polite"></div>
        </div>
      </div>

      <div class="lp-grid-2">
        <div class="lp-section" id="lp-human-approval">
          <h3 class="subh">Human Approval</h3>
          <div id="lp-approval-card" class="lp-approval-card" aria-live="polite"></div>
        </div>

        <div class="lp-section" id="lp-final-render">
          <h3 class="subh">Final Render</h3>
          <span class="muted" style="display:none">Final Render (BA 22.6)</span>
          <span class="muted" style="display:none">Final Render ist vorbereitet. Die Ausführung folgt in einer späteren BA.</span>
          <div id="lp-final-render-card" class="lp-final-render-card" aria-live="polite"></div>
        </div>
      </div>

      <div class="lp-section" id="lp-operator-actions">
        <h3 class="subh">Operator-Aktionen</h3>
        <div id="lp-actions" class="lp-action-list"></div>
      </div>

      <div class="lp-section" id="lp-recent-runs">
        <h3 class="subh">Recent Runs · Letzte Läufe unter output/</h3>
        <div id="lp-runs-wrap"></div>
      </div>
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
    <div class="actions" style="margin-top:0.5rem;display:flex;flex-wrap:wrap;gap:0.5rem;align-items:center">
      <button type="button" class="primary" id="btn-intake-body" data-label="Quelle analysieren & Input füllen">Quelle analysieren & Input füllen</button>
      <button type="button" id="btn-fill-test-body" title="Schreibt feste Testwerte ins Input Panel (DOM/IDs prüfen, kein Intake)">Fill Test Body</button>
      <button type="button" id="btn-dom-test" title="Prüft Error-Bar / JS ohne Intake">DOM TEST</button>
    </div>
    <p id="intake-status" class="intake-status muted" role="status" aria-live="polite"></p>
    <p id="intake-source-debug" class="muted" style="font-size:0.78rem;margin:0.15rem 0 0" aria-live="polite"></p>
    <p id="intake-field-debug" class="muted" style="font-size:0.74rem;margin:0.2rem 0 0;font-family:ui-monospace,monospace;white-space:pre-wrap;word-break:break-word" aria-live="polite"></p>
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
      <p id="fd-intake-apply-badge" class="muted" style="font-size:0.78rem;min-height:1.1rem;margin:0 0 0.55rem" aria-live="polite"></p>
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
      <p id="story-engine-request-debug" class="muted" style="font-size:0.78rem;min-height:1.1rem;margin:0.35rem 0 0.25rem" aria-live="polite"></p>
      <p id="export-action-status" class="export-action-status muted" role="status" aria-live="polite"></p>
      <div class="actions">
        <button type="button" class="primary" id="btn-export-package" data-label="Build Export Package">Build Export Package</button>
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
    <h2 class="subh">Production Pack (read-only)</h2>
    <p class="muted" id="prod-pack-meta" style="margin:0.25rem 0 0.5rem;font-size:0.82rem">Noch kein Production Pack Summary im geladenen JSON.</p>
    <div class="out-toolbar">
      <button type="button" class="sm tb-copy" data-pre="out-prod-pack-summary">Copy</button>
      <button type="button" class="sm tb-json" data-pre="out-prod-pack-summary" data-dlname="production_summary.json">JSON</button>
      <button type="button" class="sm tb-txt" data-pre="out-prod-pack-summary" data-dlname="production_summary.txt">TXT</button>
    </div>
    <pre class="out out-empty" id="out-prod-pack-summary">Noch kein Ergebnis. (Optional) In Export/Run-Snapshots kann ein Production Summary eingebettet sein.</pre>
    <h2 class="subh" id="prod-flow-heading">Produktionsfluss</h2>
    <p class="muted" id="prod-flow-intro" style="margin:0.25rem 0 0.5rem;font-size:0.82rem">Lokale Vorschau, menschliche Prüfung und finale Render-Freigabe (read-only, aus eingebettetem <code>production_summary</code>).</p>
    <pre class="out out-empty" id="out-prod-flow">Kein Production Summary — Produktionsfluss nicht verfügbar.</pre>
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
      <div id="export-scene-plan-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem">
        <strong>Scene Plan Summary</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Export — zuerst „Build Export Package“.</p>
      </div>
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
      <div id="visual-policy-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem">
        <strong>Visual Policy Summary (BA 26.4b/26.4c)</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Optimize-Daten — Summary erscheint nach „Optimize Provider Prompts“.</p>
      </div>
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
  </div>
</div>
<script>
try {
(function(){
  const DEFAULT_CHAPTERS = [
    {"title":"Kapitel 1","content":"Inhalt genug für eine Szene. ".repeat(8)},
    {"title":"Kapitel 2","content":"Weiterer Inhalt. ".repeat(10)}
  ];
  const $ = function(id){ return document.getElementById(id); };
  const err = $("error-bar");

  function getIntakeSourceTypeNormalized() {
    var el = document.getElementById("intake-source-type");
    if (!el || el.value == null) return "";
    return String(el.value).trim().toLowerCase();
  }

  function isIntakeRawMode(st) {
    return st === "raw_text" || st === "raw" || st.indexOf("roh") >= 0;
  }

  function setIntakeSourceDebug(msg) {
    var d = $("intake-source-debug");
    if (d) d.textContent = msg || "";
  }

  function dispatchElInputEvents(el) {
    if (!el || typeof Event === "undefined") return;
    try { el.dispatchEvent(new Event("input", { bubbles: true })); } catch (e1) {}
    try { el.dispatchEvent(new Event("change", { bubbles: true })); } catch (e2) {}
  }

  function setIntakeFieldDebug(contextLabel) {
    var dbg = $("intake-field-debug");
    if (!dbg) return;
    var tEl = $("fd-title");
    var tpEl = $("fd-topic");
    var smEl = $("fd-summary");
    var chEl = $("fd-chapters");
    var titleV = tEl ? String(tEl.value || "") : "(kein Element fd-title)";
    var topicV = tpEl ? String(tpEl.value || "") : "(kein Element fd-topic)";
    var sumV = smEl ? String(smEl.value || "") : "";
    var chRaw = chEl ? String(chEl.value || "").trim() : "";
    var chCount = -1;
    try {
      var parsed = chRaw ? JSON.parse(chRaw) : null;
      chCount = Array.isArray(parsed) ? parsed.length : -1;
    } catch (eP) {
      chCount = -1;
    }
    var prefix = contextLabel ? String(contextLabel) + "\\n" : "";
    dbg.textContent = prefix +
      "Debug fd-* nach applyIntake:\\n" +
      '  title="' + titleV.slice(0, 120) + (titleV.length > 120 ? "…" : "") + '"\\n' +
      '  topic="' + topicV.slice(0, 80) + (topicV.length > 80 ? "…" : "") + '"\\n' +
      "  summary_len=" + sumV.length + "\\n" +
      "  chapters_json_chars=" + chRaw.length + " | chapters_count=" + chCount;
  }

  function fillTestBodyIntoInputPanel() {
    var testCh = [{ title: "Kapitel 1", content: "Test Kapitel Inhalt lang genug." }];
    var payload = {
      title: "Test Titel",
      topic: "Test Topic",
      source_summary: "Test Summary",
      chapters: testCh,
      full_script: "",
      warnings: []
    };
    commitIntakePayloadToInputPanel(payload);
    setIntakeFieldDebug("Fill Test Body — direkt ohne Quelle.");
    setIntakeStatus("Fill Test Body: Input Panel gesetzt (fd-title, fd-topic, fd-summary, fd-chapters).", "success");
    showError("");
    openPanelAndScroll(null, "coll-input-panel");
  }

  function commitIntakePayloadToInputPanel(payload) {
    applyIntakeToForm(payload);
    var ti = $("fd-title");
    var tp = $("fd-topic");
    var su = $("fd-summary");
    var ch = $("fd-chapters");
    if (ti) {
      ti.value = String(payload.title || "");
      dispatchElInputEvents(ti);
    }
    if (tp) {
      tp.value = String(payload.topic || "");
      dispatchElInputEvents(tp);
    }
    if (su) {
      su.value = String(payload.source_summary || "");
      dispatchElInputEvents(su);
    }
    if (ch) {
      var chs = payload.chapters && payload.chapters.length ? payload.chapters : [];
      ch.value = JSON.stringify(chs, null, 2);
      dispatchElInputEvents(ch);
    }
  }
  function setFdIntakeApplyBadge(msg) {
    var b = $("fd-intake-apply-badge");
    if (b) b.textContent = msg || "";
  }
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
    if (el && el.closest) {
      var det = el.closest("details");
      if (det) det.open = true;
    }
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
      if (btn && btn.id === "btn-export-package") {
        setExportActionStatus("Build Export fehlgeschlagen — siehe Error-Bar.", "err");
      }
      openPanelAndScroll(detailsId, scrollTargetId || detailsId);
    }
  }

  function showError(msg) {
    if (!err) return;
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
  function normalizeStoryTemplateId(v) {
    var s = String(v == null ? "" : v).trim().toLowerCase();
    return s || "generic";
  }

  function setStoryEngineRequestDebug(msg) {
    var el = $("story-engine-request-debug");
    if (el) el.textContent = msg || "";
  }

  function setExportActionStatus(msg, kind) {
    var el = $("export-action-status");
    if (!el) return;
    el.textContent = msg || "";
    var base = "export-action-status muted";
    if (kind === "success") el.className = base + " export-action-ok";
    else if (kind === "err") el.className = base + " export-action-err";
    else if (kind === "info") el.className = base + " export-action-info";
    else el.className = base;
  }

  function clearExportScenePlanSummary() {
    var box = $("export-scene-plan-summary");
    if (!box) return;
    box.innerHTML = '<strong>Scene Plan Summary</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Export — zuerst „Build Export Package“.</p>';
  }

  function renderExportScenePlanSummary(exportData, requestBody) {
    var box = $("export-scene-plan-summary");
    if (!box || !exportData) return;
    var sp = exportData.scene_plan || {};
    var scenes = sp.scenes || [];
    var sceneCount = scenes.length;
    var chIn = requestBody && requestBody.chapters && requestBody.chapters.length ? requestBody.chapters.length : 0;
    var hk = exportData.hook || {};
    var rhythm = exportData.rhythm && typeof exportData.rhythm === "object" ? exportData.rhythm : {};
    var rKeys = Object.keys(rhythm);
    var rhythmBrief = rKeys.length ? rKeys.slice(0, 8).join(", ") + (rKeys.length > 8 ? "…" : "") : "—";
    var ul = document.createElement("ul");
    ul.style.margin = "0.35rem 0 0";
    ul.style.paddingLeft = "1.15rem";
    function addLi(t) {
      var li = document.createElement("li");
      li.textContent = t;
      ul.appendChild(li);
    }
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "Scene Plan Summary";
    box.appendChild(head);
    box.appendChild(ul);
    addLi("scene_count (scene_plan): " + sceneCount);
    addLi("Kapitel (Request): " + chIn);
    addLi("Rhythm (Keys): " + rhythmBrief);
    addLi("Hook Type: " + (hk.hook_type || "—"));
    addLi("Hook Score: " + (typeof hk.hook_score === "number" ? String(hk.hook_score) : "—"));
  }

  function validateExportFormForStoryEngine() {
    if (!$("fd-title")) throw new Error("Story-Engine: Input-Feld nicht gefunden: fd-title");
    if (!$("fd-topic")) throw new Error("Story-Engine: Input-Feld nicht gefunden: fd-topic");
    if (!$("fd-summary")) throw new Error("Story-Engine: Input-Feld nicht gefunden: fd-summary");
    if (!$("fd-chapters")) throw new Error("Story-Engine: Input-Feld nicht gefunden: fd-chapters");
    var title = ($("fd-title").value || "").trim();
    if (!title) throw new Error("Story-Engine: Titel (fd-title) darf nicht leer sein.");
    var tmplEl = $("fd-template");
    if (!tmplEl) throw new Error("Story-Engine: Template-Select fd-template nicht gefunden.");
    if (!tmplEl.options || tmplEl.options.length === 0) {
      throw new Error("Story-Engine: Keine Template-Optionen — bitte Seite neu laden (GET /story-engine/template-selector).");
    }
    var vt = normalizeStoryTemplateId(tmplEl.value);
    if (!vt) throw new Error("Story-Engine: Template nicht gesetzt.");
    var pe = $("fd-provider");
    if (!pe) throw new Error("Story-Engine: Provider fd-provider nicht gefunden.");
    var pv = (pe.value || "").trim().toLowerCase();
    if (!pv || !/^(openai|leonardo|kling)$/.test(pv)) {
      throw new Error("Story-Engine: Provider nicht gesetzt oder ungültig (openai | leonardo | kling).");
    }
    var raw = ($("fd-chapters").value || "").trim();
    if (!raw) throw new Error("Story-Engine: Kapitel-JSON (fd-chapters) ist leer.");
    var arr;
    try { arr = JSON.parse(raw); } catch (eC) {
      throw new Error("Story-Engine: Kapitel-JSON nicht parsebar: " + eC.message);
    }
    if (!Array.isArray(arr) || arr.length === 0) {
      throw new Error("Story-Engine: Mindestens ein Kapitel mit Inhalt erforderlich.");
    }
    for (var i = 0; i < arr.length; i++) {
      var c = arr[i];
      var body = c && c.content != null ? String(c.content).trim() : "";
      if (!body) throw new Error("Story-Engine: Kapitel #" + (i + 1) + " hat leeren content.");
    }
  }

  function buildCurrentExportRequestFromForm() {
    try {
      validateExportFormForStoryEngine();
    } catch (eVal) {
      throw new Error("Export Request ungültig: " + String(eVal.message || eVal));
    }
    var raw = $("fd-chapters").value.trim();
    var chapters = JSON.parse(raw);
    return {
      video_template: normalizeStoryTemplateId($("fd-template").value),
      duration_minutes: Math.min(180, Math.max(1, parseInt($("fd-duration").value, 10) || 10)),
      title: ($("fd-title").value || "").trim(),
      topic: ($("fd-topic").value || "").trim(),
      source_summary: ($("fd-summary").value || "").trim(),
      provider_profile: ($("fd-provider").value || "openai").trim().toLowerCase(),
      continuity_lock: $("fd-lock").checked,
      chapters: chapters
    };
  }

  function assertCompleteStoryResponse(endpoint, data, kind) {
    if (data === null || typeof data !== "object") {
      throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint);
    }
    if (kind === "export") {
      if (!data.hook || typeof data.hook !== "object") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (hook)");
      }
      if (!data.scene_plan || typeof data.scene_plan !== "object") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (scene_plan)");
      }
      if (!data.scene_prompts || typeof data.scene_prompts !== "object") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (scene_prompts)");
      }
    } else if (kind === "preview") {
      if (typeof data.prompt_quality_score !== "number") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (prompt_quality_score)");
      }
    } else if (kind === "readiness") {
      if (!data.scores || typeof data.scores !== "object") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (scores)");
      }
    } else if (kind === "optimize") {
      if (!data.optimized_prompts || typeof data.optimized_prompts !== "object") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (optimized_prompts)");
      }
    } else if (kind === "ctr") {
      if (typeof data.ctr_score !== "number") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (ctr_score)");
      }
    }
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
      video_template: normalizeStoryTemplateId($("fd-template").value),
      duration_minutes: Math.min(180, Math.max(1, parseInt($("fd-duration").value, 10) || 10)),
      title: $("fd-title").value || "",
      topic: $("fd-topic").value || "",
      source_summary: $("fd-summary").value || "",
      provider_profile: ($("fd-provider").value || "openai").trim().toLowerCase(),
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
      root.innerHTML = '<p class="muted">Keine Warnungen aus Export / Preview / Readiness / Optimize / CTR.</p>';
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
    // BA 27.0–27.4: read-only production pack summary (only if embedded in loaded JSON)
    var ps = extractProductionPackSummary();
    var meta = $("prod-pack-meta");
    if (meta) {
      var rs = ps && ps.reference_library_summary ? ps.reference_library_summary : null;
      var rcount = rs && rs.reference_assets_count != null ? String(rs.reference_assets_count) : "0";
      var cs = ps && ps.continuity_wiring_summary ? ps.continuity_wiring_summary : null;
      var cprep = cs && cs.prepared_count != null ? String(cs.prepared_count) : "0";
      var cmiss = cs && cs.missing_reference_count != null ? String(cs.missing_reference_count) : "0";
      var rps = ps && ps.reference_provider_payload_summary ? ps.reference_provider_payload_summary : null;
      var rpPrep = rps && rps.prepared_count != null ? String(rps.prepared_count) : "0";
      var ms = ps && ps.motion_clip_summary ? ps.motion_clip_summary : null;
      var mPlanned = ms && ms.clips_planned != null ? String(ms.clips_planned) : "0";
      var mMissing = ms && ms.missing_input_count != null ? String(ms.missing_input_count) : "0";
      var mDry = ms && ms.dry_run != null ? (ms.dry_run ? "ja" : "nein") : "—";
      meta.textContent = ps
        ? ("Production Summary gefunden (read-only). References: " + rcount + " · Continuity prepared: " + cprep + " · Missing refs: " + cmiss + " · Referenz-Provider vorbereitet: " + rpPrep + " · Motion Clips: " + mPlanned + " · Missing inputs: " + mMissing + " · Dry-run: " + mDry)
        : "Noch kein Production Pack Summary im geladenen JSON.";
    }
    setOut("out-prod-pack-summary", ps);
    refreshProductionFlowPanel(ps);
    refreshFounderInterpretation();
  }

  // BA 30.0 — Founder production flow (read-only, German operator labels)
  function mapHumanPreviewReviewDe(st) {
    var k = String(st || "").toLowerCase();
    if (k === "pending") return "Offen";
    if (k === "approved") return "Freigegeben";
    if (k === "rejected") return "Abgelehnt";
    if (k === "needs_changes") return "Änderungen nötig";
    return st || "—";
  }
  function mapFinalReadinessDe(st) {
    var k = String(st || "").toLowerCase();
    if (k === "ready") return "Renderbereit";
    if (k === "needs_review") return "Prüfung nötig";
    if (k === "blocked") return "Blockiert";
    return st || "—";
  }
  function refreshProductionFlowPanel(ps) {
    var host = $("out-prod-flow");
    if (!host) return;
    if (!ps) {
      host.textContent = "Kein Production Summary — Produktionsfluss nicht verfügbar.";
      return;
    }
    var pf = ps.visual_production_preflight_result || null;
    var mc = ps.motion_clip_summary || null;
    var rib = ps.render_input_bundle_path || "";
    var lpPath = String(ps.local_preview_video_path || "").trim();
    var lpSt = String(ps.local_preview_status || "absent");
    var lpOk = lpSt === "available" || lpSt === "video_only";
    var hpr = ps.human_preview_review_result || null;
    var frr = ps.final_render_readiness_result || null;
    var lines = [];
    lines.push("Produktionspaket / Pack-Status");
    lines.push("- ready_for_render: " + (ps.ready_for_render ? "ja" : "nein") + " · render_readiness_status: " + String(ps.render_readiness_status || "—"));
    lines.push("- approval_status: " + String(ps.approval_status || "—"));
    lines.push("");
    lines.push("Visual Preflight");
    lines.push(pf ? ("- Status: " + String(pf.preflight_status || "—") + " · ok: " + (pf.ok ? "ja" : "nein")) : "- (kein Preflight im Summary)");
    lines.push("");
    lines.push("Motion Clips");
    lines.push(mc ? ("- geplant: " + String(mc.clips_planned != null ? mc.clips_planned : "—") + " · fehlende Inputs: " + String(mc.missing_input_count != null ? mc.missing_input_count : "—")) : "- (kein motion_clip_summary)");
    lines.push("");
    lines.push("Timeline / Bundle");
    lines.push("- render_input_bundle_path: " + (rib || "—"));
    lines.push("");
    lines.push("Lokale Vorschau");
    lines.push("- Vorschau verfügbar: " + (lpOk ? "ja" : "nein") + " · Status: " + lpSt);
    if (lpPath) lines.push("- Pfad: " + lpPath);
    if (ps.local_preview_render_result && ps.local_preview_render_result.blocking_reasons && ps.local_preview_render_result.blocking_reasons.length) {
      lines.push("- Blockierende Gründe: " + ps.local_preview_render_result.blocking_reasons.join(", "));
    }
    lines.push("");
    lines.push("Menschliche Vorschau-Prüfung");
    if (hpr) {
      lines.push("- Status: " + mapHumanPreviewReviewDe(hpr.review_status) + " (raw: " + String(hpr.review_status || "") + ")");
      lines.push("- Freigabe finaler Render: " + (hpr.approved_for_final_render ? "ja" : "nein"));
    } else {
      lines.push("- (noch kein human_preview_review_result)");
    }
    lines.push("");
    lines.push("Finale Render-Freigabe");
    if (frr) {
      lines.push("- Gesamt: " + mapFinalReadinessDe(frr.readiness_status) + " · ok: " + (frr.ok ? "ja" : "nein"));
      lines.push("- technisch: " + (frr.technical_ready ? "ja" : "nein") + " · menschlich freigegeben: " + (frr.human_review_approved ? "ja" : "nein"));
      if (frr.blocking_reasons && frr.blocking_reasons.length) lines.push("- Blockiert wegen: " + frr.blocking_reasons.join(", "));
    } else {
      lines.push("- (noch kein final_render_readiness_result)");
    }
    lines.push("");
    lines.push("Nächste Schritte (Vorschlag)");
    lines.push("- Lokale Vorschau erzeugen (sofern FFmpeg verfügbar) und Pfad prüfen.");
    lines.push("- human_preview_review per CLI setzen, danach final_render_readiness_gate ausführen.");
    lines.push("- Finalen Render nur mit Freigabe und explizitem --execute starten.");
    host.textContent = lines.join("\n");
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
      var bx = $("btn-export-package");
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
    var pol = $("visual-policy-summary");
    // BA 26.4d — Fallback-Reihenfolge:
    // 1) lastOptimize.optimized_prompts
    // 2) lastExport.provider_prompts
    // 3) lastExport.scene_prompts.scenes
    function resolveVisualPolicySource() {
      if (lastOptimize && lastOptimize.optimized_prompts) {
        return { source: "Optimize", kind: "opt", p: lastOptimize.optimized_prompts };
      }
      if (lastExport && lastExport.provider_prompts) {
        return { source: "Export Package", kind: "stub", p: lastExport.provider_prompts };
      }
      if (lastExport && lastExport.scene_prompts && Array.isArray(lastExport.scene_prompts.scenes)) {
        return { source: "Story Pack", kind: "scene", p: lastExport.scene_prompts.scenes };
      }
      return { source: "Not available", kind: "none", p: null };
    }

    function extractPolicyItems(vps) {
      var out = [];
      if (!vps) return out;
      // provider bundles: { leonardo:[], openai:[], kling:[] }
      if (typeof vps === "object" && !Array.isArray(vps) && (vps.leonardo || vps.openai || vps.kling)) {
        function pushArr(arr, providerName) {
          if (!Array.isArray(arr)) return;
          for (var ii = 0; ii < arr.length; ii++) {
            var it = arr[ii] || {};
            var routed = String(it.routed_visual_provider || it.routed_provider || it.provider || "").toLowerCase();
            var st = String(it.visual_policy_status || "");
            var ts2 = !!it.text_sensitive;
            var oi = it.overlay_intent || [];
            var ovc = (Array.isArray(oi) ? oi.length : 0);
            var txt = String(it.positive_optimized || it.positive_expanded || it.visual_prompt_effective || it.visual_prompt || "");
            var guard2 = txt.indexOf("[visual_no_text_guard_v26_4]") >= 0;
            out.push({ provider: providerName, routed: routed, status: st, text_sensitive: ts2, overlay_count: ovc, guard_applied: guard2 });
          }
        }
        pushArr(vps.leonardo, "leonardo");
        pushArr(vps.openai, "openai");
        pushArr(vps.kling, "kling");
        return out;
      }
      // scene list
      if (Array.isArray(vps)) {
        for (var k = 0; k < vps.length; k++) {
          var it2 = vps[k] || {};
          var routed2 = String(it2.routed_visual_provider || it2.routed_provider || it2.provider || "").toLowerCase();
          var st2 = String(it2.visual_policy_status || "");
          var ts3 = !!it2.text_sensitive;
          var oi2 = it2.overlay_intent || [];
          var ovc2 = (Array.isArray(oi2) ? oi2.length : 0);
          var txt2 = String(it2.positive_expanded || it2.visual_prompt_effective || it2.visual_prompt || "");
          var guard3 = txt2.indexOf("[visual_no_text_guard_v26_4]") >= 0;
          out.push({ provider: "scene", routed: routed2, status: st2, text_sensitive: ts3, overlay_count: ovc2, guard_applied: guard3 });
        }
      }
      return out;
    }

    function renderVisualPolicySummary() {
      if (!pol) return;
      var src = resolveVisualPolicySource();
      var items = extractPolicyItems(src.p);
      var rows = [];
      var tot = 0, ts = 0, ov = 0, guard = 0, need = 0, oai = 0, leo = 0, rw = 0, rl = 0;
      for (var j = 0; j < items.length; j++) {
        var it = items[j] || {};
        tot++;
        if (String(it.status || "") === "needs_review") need++;
        if (it.text_sensitive) ts++;
        ov += Number(it.overlay_count || 0);
        if (it.guard_applied) guard++;
        var rp = String(it.routed || "").toLowerCase();
        if (rp === "openai_images") oai++;
        else if (rp === "leonardo") leo++;
        else if (rp === "runway") rw++;
        else if (rp === "render_layer") rl++;
      }
      rows.push("<div class='muted' style='font-size:0.82rem;margin-top:0.15rem'>Visual Policy Source: <strong>" + escapeHtml(String(src.source || "Not available")) + "</strong></div>");
      rows.push("<div class='muted' style='font-size:0.82rem;margin-top:0.15rem'>Visual Text Guard: aktiv (Marker <code>[visual_no_text_guard_v26_4]</code>)</div>");
      rows.push("<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.35rem'>");
      function pill(label, val) {
        return \"<span style='display:inline-block;padding:0.15rem 0.45rem;border:1px solid var(--border);border-radius:999px;background:var(--surface2);font-size:0.82rem'><strong>\" + escapeHtml(label) + \":</strong> \" + escapeHtml(String(val)) + \"</span>\";
      }
      rows.push(pill("Scenes", tot));
      rows.push(pill("Text-sensitive", ts));
      rows.push(pill("Overlay intents", ov));
      rows.push(pill("Guard applied", guard));
      rows.push(pill("OpenAI Images routed", oai));
      rows.push(pill("Leonardo routed", leo));
      rows.push(pill("Runway routed", rw));
      rows.push(pill("Render Layer overlays", rl));
      rows.push(pill("Needs review", need));
      rows.push("</div>");
      pol.innerHTML = "<strong>Visual Policy Summary (BA 26.4b/26.4c/26.4d)</strong>" + rows.join(\"\\n\");
    }

    // Summary immer rendern, auch ohne Optimize (Export-Fallback).
    renderVisualPolicySummary();

    // Prompt Cards bleiben Optimize-first (weil sie die optimierten Texte zeigen).
    if (!lastOptimize || !lastOptimize.optimized_prompts) {
      host.innerHTML = '<p class="muted">Noch keine Optimize-Daten — Prompt Cards erscheinen nach „Optimize Provider Prompts“. (Summary nutzt Export-Fallback.)</p>';
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
      var polLine = "";
      var polSrc = leo || oai || {};
      if (polSrc) {
        var stx = String(polSrc.visual_policy_status || "").trim();
        var ovn = (polSrc.overlay_intent && Array.isArray(polSrc.overlay_intent)) ? polSrc.overlay_intent.length : 0;
        var rpv = String(polSrc.routed_visual_provider || \"\");
        if (stx || ovn || rpv) {
          polLine = '<div class=\"muted\" style=\"font-size:0.78rem;margin:-0.25rem 0 0.4rem\">Policy: <strong>' + escapeHtml(stx || \"—\") + '</strong> · Routed: <strong>' + escapeHtml(rpv || \"—\") + '</strong> · Overlay: <strong>' + escapeHtml(String(ovn)) + '</strong></div>';
        }
      }
      var cmpLine = "";
      if (polSrc) {
        var rec = String(polSrc.recommended_provider || "").trim();
        var cst = String(polSrc.provider_compare_status || "").trim();
        var creason = String(polSrc.provider_quality_reason || "").trim();
        var cc = (polSrc.provider_candidates && Array.isArray(polSrc.provider_candidates)) ? polSrc.provider_candidates.length : 0;
        if (rec || cst || creason || cc) {
          cmpLine =
            '<div class=\"muted\" style=\"font-size:0.78rem;margin:-0.15rem 0 0.4rem\">' +
            'Compare: <strong>' + escapeHtml(rec || \"—\") + '</strong>' +
            ' · Status: <strong>' + escapeHtml(cst || \"—\") + '</strong>' +
            ' · Candidates: <strong>' + escapeHtml(String(cc)) + '</strong>' +
            (creason ? (' · <span title=\"' + escapeHtml(creason) + '\">Reason</span>') : \"\") +
            '</div>';
        }
      }
      // BA 27.3 — Continuity line (read-only, only if fields exist)
      var contLine = "";
      if (polSrc) {
        var cst2 = String(polSrc.continuity_provider_preparation_status || "").trim();
        var cids = polSrc.reference_asset_ids;
        var cc2 = (Array.isArray(cids) ? cids.length : 0);
        var cstr = String(polSrc.continuity_strength || "").trim();
        var ch = String(polSrc.continuity_prompt_hint || "").trim();
        if (cst2 || cc2 || cstr || ch) {
          var hintShort = ch ? (ch.length > 140 ? ch.slice(0, 139) + "…" : ch) : "";
          // display only: translate to German labels, keep raw status values intact elsewhere
          var cstDe = cst2;
          if (cst2 === "prepared") cstDe = "vorbereitet";
          else if (cst2 === "missing_reference") cstDe = "Referenz fehlt";
          else if (cst2 === "needs_review") cstDe = "Prüfung nötig";
          else if (!cst2 && cc2) cstDe = "vorbereitet";
          else if (!cst2) cstDe = "keine";
          var cstrDe = cstr;
          if (cstr === "low") cstrDe = "niedrig";
          else if (cstr === "medium") cstrDe = "mittel";
          else if (cstr === "high") cstrDe = "hoch";
          contLine =
            '<div class="muted" style="font-size:0.78rem;margin:-0.15rem 0 0.4rem">' +
            'Kontinuität: <strong>' + escapeHtml(cstDe) + '</strong>' +
            ' · Referenzen: <strong>' + escapeHtml(String(cc2)) + '</strong>' +
            (cstr ? (' · Stärke: <strong>' + escapeHtml(cstrDe) + '</strong>') : '') +
            (hintShort ? (' · <span title="' + escapeHtml(ch) + '">Hint</span>') : '') +
            '</div>';
        }
      }
      // BA 27.5b — Reference Provider payload line (read-only, only if fields exist)
      var refProvLine = "";
      if (polSrc) {
        function mapRefStatusDe(st) {
          if (st === "prepared") return "vorbereitet";
          if (st === "missing_reference") return "Referenz fehlt";
          if (st === "needs_review") return "Prüfung nötig";
          if (st === "not_supported") return "nicht unterstützt";
          return "keine";
        }
        function mapRefModeDe(m) {
          if (m === "image_reference_prepared") return "Bildreferenz vorbereitet";
          if (m === "image_to_video_reference_prepared") return "Bild-zu-Video-Referenz vorbereitet";
          if (m === "prompt_hint_only") return "nur Prompt-Hinweis";
          return "keine";
        }
        function mapRefProviderDe(p) {
          if (p === "openai_images") return "OpenAI Images";
          if (p === "leonardo") return "Leonardo";
          if (p === "runway") return "Runway";
          if (p === "seedance") return "Seedance";
          if (p === "render_layer") return "Render-Layer";
          return p ? p : "—";
        }
        function pickRefPayload(src) {
          var rec = src && src.recommended_reference_provider_payload ? src.recommended_reference_provider_payload : null;
          if (rec && typeof rec === "object") return rec;
          var all = src && src.reference_provider_payloads ? src.reference_provider_payloads : null;
          if (all && typeof all === "object") {
            var oai = all.openai_images;
            if (oai && typeof oai === "object") return oai;
            var keys = Object.keys(all);
            for (var kk = 0; kk < keys.length; kk++) {
              var v = all[keys[kk]];
              if (v && typeof v === "object") return v;
            }
          }
          return null;
        }
        function findAssetLikeForScene(sceneNumber) {
          try {
            var exp = lastExport && lastExport.asset_manifest ? lastExport.asset_manifest : null;
            if (!exp && lastExport && lastExport.asset_manifest_reference_index) {
              var idx = lastExport.asset_manifest_reference_index;
              var by = idx && idx.by_scene_number ? idx.by_scene_number : null;
              if (by && by[String(sceneNumber)]) return by[String(sceneNumber)];
            }
            var man = exp && exp.assets && Array.isArray(exp.assets) ? exp : null;
            if (!man) return null;
            for (var ai = 0; ai < man.assets.length; ai++) {
              var a = man.assets[ai] || {};
              var sn = Number(a.scene_number || a.scene_index || 0);
              if (sn === sceneNumber) return a;
            }
            return null;
          } catch (e) {
            return null;
          }
        }
        var rpp = pickRefPayload(polSrc);
        var rps = String(polSrc.reference_provider_payload_status || (rpp && rpp.status) || "").trim();
        if (!rpp || !rps) {
          // BA 27.6: fallback to asset_manifest if prompt object has no reference fields
          var assetLike = findAssetLikeForScene(i + 1);
          if (assetLike && !rpp) rpp = pickRefPayload(assetLike);
          if (assetLike && !rps) rps = String(assetLike.reference_provider_payload_status || (rpp && rpp.status) || "").trim();
        }
        var rpsDe = mapRefStatusDe(rps);
        var provRaw = String((rpp && rpp.provider) || "").toLowerCase();
        var provDe = mapRefProviderDe(provRaw);
        var modeRaw = String((rpp && rpp.supported_mode) || "").trim();
        var modeDe = mapRefModeDe(modeRaw);
        var fmt = String((rpp && rpp.payload_format) || "").trim();
        var noLive = (rpp && rpp.no_live_upload) === true;
        var refCount = 0;
        if (rpp && rpp.payload && typeof rpp.payload === "object" && Array.isArray(rpp.payload.reference_images)) {
          refCount = rpp.payload.reference_images.length;
        } else if (rpp && Array.isArray(rpp.reference_paths)) {
          refCount = rpp.reference_paths.length;
        }
        if (rps || rpp) {
          refProvLine =
            '<div class="muted" style="font-size:0.78rem;margin:-0.15rem 0 0.4rem">' +
            'Referenz-Provider: <strong>' + escapeHtml(rpsDe) + '</strong>' +
            (provRaw ? (' · Provider: <strong>' + escapeHtml(provDe) + '</strong>') : '') +
            (modeRaw ? (' · Modus: <strong>' + escapeHtml(modeDe) + '</strong>') : '') +
            (refCount ? (' · Referenzen: <strong>' + escapeHtml(String(refCount)) + '</strong>') : '') +
            (fmt ? (' · <span title="' + escapeHtml(fmt) + '">Format</span>') : '') +
            (noLive ? (' · <strong>Kein Live-Upload</strong>') : '') +
            '</div>';
        }
      }
      card.innerHTML =
        "<h3>Szene " + (i + 1) + "</h3>" + polLine + cmpLine + contLine + refProvLine +
        '<div class="pc-block"><label>Leonardo</label><pre class="pc-pre">' + escapeHtml(leoT || "—") + "</pre>" +
        '<button type="button" class="sm pc-copy-btn" data-pc-idx="' + i + '" data-pc-kind="leo">Copy</button></div>' +
        '<div class="pc-block"><label>Kling Motion / Kamera / Keyframe</label><pre class="pc-pre">' + escapeHtml(kT || "—") + "</pre>" +
        '<button type="button" class="sm pc-copy-btn" data-pc-idx="' + i + '" data-pc-kind="kling">Copy</button></div>' +
        '<div class="pc-block"><label>OpenAI</label><pre class="pc-pre">' + escapeHtml(oaiT || "—") + "</pre>" +
        '<button type="button" class="sm pc-copy-btn" data-pc-idx="' + i + '" data-pc-kind="openai">Copy</button></div>';
      host.appendChild(card);
    }
  }

  // BA 26.9c — helper for read-only display (if JSON contains production_asset_approval_result)
  function extractProductionAssetApproval() {
    if (!lastExport) return null;
    return lastExport.production_asset_approval_result || null;
  }

  // BA 27.0 — read-only: show if a production summary is embedded in JSON
  function extractProductionPackSummary() {
    if (!lastExport) return null;
    return lastExport.production_summary || lastExport.production_pack_summary || null;
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
    if (!t || t.length < 20) return [];
    var mono = t.replace(/\\r\\n/g, "\\n");
    var parts = mono.split(/\\n\\s*\\n+/).map(function(x) {
      return x.replace(/[ \\t]+/g, " ").trim();
    }).filter(function(x) { return x.length > 0; });
    if (!parts.length) parts = [mono.replace(/[ \\t]+/g, " ").trim()];
    var merged = [];
    parts.forEach(function(p) {
      if (!merged.length) { merged.push(p); return; }
      var last = merged[merged.length - 1];
      if (last.length < 20 || p.length < 12) merged[merged.length - 1] = (last + "\\n\\n" + p).trim();
      else merged.push(p);
    });
    if (merged.length === 1 && merged[0].length > 800) {
      var one = merged[0];
      var targetN = Math.min(4, Math.max(2, Math.ceil(one.length / 400)));
      merged = [];
      var start = 0;
      for (var ci = 0; ci < targetN && start < one.length; ci++) {
        var chunkSize = Math.ceil((one.length - start) / (targetN - ci));
        var chunk = one.slice(start, start + chunkSize).trim();
        var cut = chunk.lastIndexOf(" ");
        if (ci < targetN - 1 && cut > 35) chunk = chunk.slice(0, cut).trim();
        if (chunk.length >= 20) merged.push(chunk);
        start += chunk.length;
        while (start < one.length && one.charAt(start) === " ") start++;
      }
      if (!merged.length) merged = [one];
    }
    while (merged.length > 4) {
      var a = merged.pop();
      var b = merged.pop();
      merged.push((b + "\\n\\n" + a).trim());
    }
    if (merged.length === 1 && merged[0].length > 240) {
      var u = merged[0];
      var mid = Math.floor(u.length / 2);
      var spm = u.lastIndexOf(" ", mid + 50);
      if (spm > 25 && u.length - spm - 1 >= 20) {
        merged = [u.slice(0, spm).trim(), u.slice(spm + 1).trim()];
      }
    }
    var out = merged.map(function(p, idx) {
      return { title: "Abschnitt " + (idx + 1), content: p };
    });
    for (var j = 0; j < out.length; j++) {
      if (out[j].content.length < 20) {
        if (t.length >= 20) out[j] = { title: out[j].title, content: t };
        else return [];
      }
    }
    return out;
  }

  function normalizeChapterListForIntake(chs) {
    if (!chs || !Array.isArray(chs)) return [];
    var out = [];
    for (var i = 0; i < chs.length; i++) {
      var c = chs[i];
      if (!c || typeof c !== "object") continue;
      var t = c.title != null ? String(c.title).trim() : "";
      var body = c.content != null ? String(c.content).trim() : "";
      if (!body) continue;
      if (!t) t = "Kapitel " + (out.length + 1);
      out.push({ title: t, content: body });
    }
    return out;
  }

  function normalizeIntakePayloadFromResponse(gen, typ, fromRaw) {
    var topicIn = $("intake-topic") ? $("intake-topic").value.trim() : "";
    var warnings = (gen && gen.warnings && Array.isArray(gen.warnings)) ? gen.warnings.slice() : [];
    if (fromRaw) {
      var chR = normalizeChapterListForIntake(gen.chapters);
      var titleR = String(gen.title != null ? gen.title : "").trim();
      var fsR = String(gen.full_script != null ? gen.full_script : "").trim();
      var sumR = String(gen.client_summary != null ? gen.client_summary : "").trim();
      return {
        title: titleR,
        topic: topicIn || titleR,
        source_summary: sumR,
        chapters: chR,
        full_script: fsR,
        warnings: warnings
      };
    }
    var title = String(gen && gen.title != null ? gen.title : "").trim();
    var full_script = String(gen && gen.full_script != null ? gen.full_script : "").trim();
    var hook = String(gen && gen.hook != null ? gen.hook : "").trim();
    var source_summary = hook;
    if (!source_summary && full_script) {
      if (full_script.length <= 480) source_summary = full_script;
      else {
        var slice = full_script.slice(0, 440);
        var sp = slice.lastIndexOf(" ");
        if (sp > 80) slice = slice.slice(0, sp);
        source_summary = slice.trim() + " …";
      }
    }
    if (!source_summary && gen && gen.chapters && gen.chapters.length) {
      source_summary = gen.chapters.slice(0, 3).map(function(c) {
        var ct = (c && c.title != null) ? String(c.title).trim() : "";
        var cx = (c && c.content != null) ? String(c.content).trim().slice(0, 140) : "";
        return (ct || "Kapitel") + ": " + cx;
      }).join(" — ").trim();
    }
    var chapters = normalizeChapterListForIntake(gen && gen.chapters ? gen.chapters : []);
    return {
      title: title,
      topic: topicIn || title,
      source_summary: source_summary,
      chapters: chapters,
      full_script: full_script,
      warnings: warnings
    };
  }

  function getRequiredInputEl(id) {
    var el = $(id);
    if (!el) {
      var m = "Input-Feld nicht gefunden: " + id;
      showError(m);
      throw new Error(m);
    }
    return el;
  }

  function applyIntakeToForm(payload) {
    if (!payload || typeof payload !== "object") {
      throw new Error("applyIntakeToForm: kein gültiger Payload.");
    }
    getRequiredInputEl("fd-title").value = String(payload.title || "");
    getRequiredInputEl("fd-topic").value = String(payload.topic || "");
    getRequiredInputEl("fd-summary").value = String(payload.source_summary || "");
    var chs = payload.chapters && payload.chapters.length ? payload.chapters : [];
    getRequiredInputEl("fd-chapters").value = JSON.stringify(chs, null, 2);
  }

  function validateFormAfterIntake(mode) {
    mode = mode || "intake";
    var prefix = mode === "pipeline" ? "Bitte zuerst Auto Body aus Quelle erfolgreich ausführen. " : "";
    var titleEl = $("fd-title");
    if (!titleEl) throw new Error(prefix + "Input-Feld nicht gefunden: fd-title");
    var title = (titleEl.value || "").trim();
    if (!title) throw new Error(prefix + "Titel (Title/Headline) ist leer.");
    var chEl = $("fd-chapters");
    if (!chEl) throw new Error(prefix + "Input-Feld nicht gefunden: fd-chapters");
    var raw = (chEl.value || "").trim();
    if (!raw) throw new Error(prefix + "Kapitel (JSON) ist leer.");
    var arr;
    try { arr = JSON.parse(raw); } catch (e0) {
      throw new Error(prefix + "Kapitel-JSON nicht parsebar: " + e0.message);
    }
    if (!Array.isArray(arr) || arr.length === 0) {
      throw new Error(prefix + "Keine Kapitel (JSON-Array leer).");
    }
    for (var i = 0; i < arr.length; i++) {
      var c = arr[i];
      var body = c && c.content != null ? String(c.content).trim() : "";
      if (!body) throw new Error(prefix + "Kapitel #" + (i + 1) + " hat leeren content.");
    }
    return arr.length;
  }

  function buildPseudoScriptResponseFromRaw(raw) {
    var ch = rawTextToChapters(raw);
    if (!ch || !ch.length) {
      throw new Error("Rohtext fehlt oder zu kurz — mindestens ca. 20 Zeichen sinnvoller Text für Kapitel erforderlich.");
    }
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

  function validateScriptResponseForIntake(gen, typ) {
    if (!gen || typeof gen !== "object") throw new Error("Ungültige Skript-Antwort vom Server.");
    if (isIntakeRawMode(String(typ || "").trim().toLowerCase())) return;
    var normCh = normalizeChapterListForIntake(gen.chapters);
    var hasCh = normCh.length > 0;
    var t = gen.title != null ? String(gen.title).trim() : "";
    var fs = gen.full_script != null ? String(gen.full_script).trim() : "";
    var hook = gen.hook != null ? String(gen.hook).trim() : "";
    if ((typ === "youtube" || typ === "news") && !hasCh) {
      mergeWarnings(gen.warnings || []);
      throw new Error("Skript-Response ohne Kapitel mit Inhalt (title/chapters) — prüfe response.title und response.chapters von /generate-script bzw. /youtube/generate-script.");
    }
    if (!hasCh && fs.length < 12 && t.length < 3 && hook.length < 3) {
      mergeWarnings(gen.warnings || []);
      throw new Error("Skript-Response ohne nutzbaren Inhalt (leere Kapitel/Text) — Transkript/URL prüfen oder Fehlermeldung in der Error-Bar.");
    }
  }

  function validateIntakeBeforeFullPipeline() {
    var typ = getIntakeSourceTypeNormalized();
    if (isIntakeRawMode(typ)) {
      if ($("intake-raw-text").value.trim().length < 20) throw new Error("Full Pipeline: Rohtext fehlt oder zu kurz (min. 20 Zeichen).");
      return;
    }
    if (typ === "youtube") {
      if (!$("intake-youtube-url").value.trim()) throw new Error("Full Pipeline: YouTube-URL im Intake ausfüllen oder Quelle wechseln.");
    } else if (typ === "news") {
      if (!$("intake-news-url").value.trim()) throw new Error("Full Pipeline: News-URL im Intake ausfüllen.");
    } else {
      throw new Error("Full Pipeline: Unbekannte Intake-Quelle: " + typ);
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
    clearExportScenePlanSummary();
    setExportActionStatus("", "");
  }

  async function runBuildBodyFromIntake() {
    setIntakeStatus("Auto Body geklickt", "info");
    var typ = getIntakeSourceTypeNormalized();
    setFdIntakeApplyBadge("");
    var labelCanon = isIntakeRawMode(typ) ? "raw_text" : (typ === "news" ? "news" : (typ === "youtube" ? "youtube" : typ || "?"));
    setIntakeSourceDebug("Quelle erkannt: " + labelCanon);
    setIntakeStatus("Auto Body geklickt · Quelle erkannt: " + labelCanon, "info");
    var tmpl = $("fd-template").value || "generic";
    var dur = Math.min(180, Math.max(1, parseInt($("fd-duration").value, 10) || 10));
    var conf = "warn";
    var gen;
    var fromRaw = false;
    try {
      setIntakeStatus("Auto Body geklickt · Quelle erkannt: " + labelCanon + " — lade…", "info");
      if (isIntakeRawMode(typ)) {
        var rt = $("intake-raw-text").value.trim();
        if (rt.length < 20) throw new Error("Rohtext fehlt oder zu kurz — mindestens 20 Zeichen erforderlich.");
        setIntakeStatus("Rohtext-Pfad: keine YouTube/News-Validierung — segmentiere…", "info");
        gen = buildPseudoScriptResponseFromRaw(rt);
        fromRaw = true;
      } else if (typ === "youtube") {
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
      } else {
        throw new Error("Unbekannter Quelltyp: " + typ);
      }
      var normalized = normalizeIntakePayloadFromResponse(gen, typ, fromRaw);
      if (!normalized.chapters || normalized.chapters.length === 0) {
        throw new Error("Keine Kapitel mit Inhalt aus der Quelle — Eingabe oder Server-Antwort prüfen (response.chapters).");
      }
      commitIntakePayloadToInputPanel(normalized);
      setIntakeFieldDebug("Nach commitIntakePayloadToInputPanel (applyIntakeToForm + DOM refresh).");
      var nCh = validateFormAfterIntake("intake");
      mergeWarnings(normalized.warnings || []);
      refreshFounderInterpretation();
      var okMsg = "Input Panel aktualisiert: " + nCh + " Kapitel";
      setIntakeStatus(fromRaw ? "Rohtext verarbeitet — " + okMsg + "." : okMsg + ".", "success");
      setFdIntakeApplyBadge("Übernommen: Titel, Topic, Summary, Kapitel (JSON).");
      showError("");
      openPanelAndScroll(null, "coll-input-panel");
      return gen;
    } catch (e) {
      setFdIntakeApplyBadge("");
      var msg = String(e.message || e);
      setIntakeStatus("Fehler: " + msg, "err");
      throw e;
    }
  }

  async function runExportOnlyInternal() {
    setExportActionStatus("Build Export: Formular wird validiert…", "info");
    const body = buildCurrentExportRequestFromForm();
    var nc = body.chapters && body.chapters.length ? body.chapters.length : 0;
    setStoryEngineRequestDebug("Export Request gebaut: Template=" + body.video_template + " | Provider=" + body.provider_profile + " | Kapitel=" + nc);
    setExportActionStatus("Build Export: POST /story-engine/export-package …", "info");
    const data = await fetchJson("/story-engine/export-package", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    assertCompleteStoryResponse("/story-engine/export-package", data, "export");
    lastExport = data;
    lastNumericPq = null;
    updatePqBadge();
    setOut("out-export-full", data);
    setOut("out-hook", data.hook || null);
    renderExportScenePlanSummary(data, body);
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
    var cx = $("coll-export");
    if (cx && cx.tagName === "DETAILS") cx.open = true;
    openPanelAndScroll("coll-export", "out-export-full");
    setExportActionStatus("Build Export: fertig — Rohpaket & Hook Preview aktualisiert.", "success");
    return data;
  }

  async function runPreviewOnlyInternal() {
    const body = buildCurrentExportRequestFromForm();
    var nc = body.chapters && body.chapters.length ? body.chapters.length : 0;
    setStoryEngineRequestDebug("Export Request gebaut: Template=" + body.video_template + " | Provider=" + body.provider_profile + " | Kapitel=" + nc);
    const data = await fetchJson("/story-engine/export-package/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    assertCompleteStoryResponse("/story-engine/export-package/preview", data, "preview");
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
    openPanelAndScroll("coll-preview", "out-pq-score");
    return data;
  }

  async function runReadinessOnlyInternal() {
    const body = buildCurrentExportRequestFromForm();
    var nc = body.chapters && body.chapters.length ? body.chapters.length : 0;
    setStoryEngineRequestDebug("Export Request gebaut: Template=" + body.video_template + " | Provider=" + body.provider_profile + " | Kapitel=" + nc);
    const data = await fetchJson("/story-engine/provider-readiness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    assertCompleteStoryResponse("/story-engine/provider-readiness", data, "readiness");
    lastReadiness = data;
    setOut("out-readiness", data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    openPanelAndScroll("coll-readiness", "out-readiness");
    return data;
  }

  async function runOptimizeOnlyInternal() {
    const body = buildCurrentExportRequestFromForm();
    var nc = body.chapters && body.chapters.length ? body.chapters.length : 0;
    setStoryEngineRequestDebug("Export Request gebaut: Template=" + body.video_template + " | Provider=" + body.provider_profile + " | Kapitel=" + nc);
    const data = await fetchJson("/story-engine/provider-prompts/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    assertCompleteStoryResponse("/story-engine/provider-prompts/optimize", data, "optimize");
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
    openPanelAndScroll("coll-optimize", "out-leo");
    return data;
  }

  async function runCtrOnlyInternal() {
    const req = buildCurrentExportRequestFromForm();
    var hook = "";
    var thumb = "";
    if (lastExport && lastExport.hook) hook = lastExport.hook.hook_text || "";
    if (lastExport && lastExport.thumbnail_prompt) thumb = lastExport.thumbnail_prompt;
    var nc = req.chapters && req.chapters.length ? req.chapters.length : 0;
    setStoryEngineRequestDebug("CTR Request gebaut: Template=" + req.video_template + " | Kapitel=" + nc + " | Hook aus Export=" + (hook ? "ja" : "nein"));
    const body = {
      title: req.title,
      hook: hook,
      video_template: req.video_template,
      thumbnail_prompt: thumb,
      chapters: req.chapters
    };
    const data = await fetchJson("/story-engine/thumbnail-ctr", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    assertCompleteStoryResponse("/story-engine/thumbnail-ctr", data, "ctr");
    lastCtrPayload = data;
    setOut("out-ctr", data.ctr_score);
    setOut("out-ctr-raw", data);
    setOut("out-thumb-var", data.thumbnail_variants || []);
    mergeWarnings(data.warnings || []);
    openPanelAndScroll("coll-ctr", "out-ctr");
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
      validateFormAfterIntake("pipeline");
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
    if (data === null || data === undefined) {
      throw new Error("Endpoint antwortet leer oder unvollständig: " + url);
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
      if (sel.options.length && (!sel.value || sel.selectedIndex < 0)) {
        sel.selectedIndex = 0;
      }
      setStoryEngineRequestDebug("Templates geladen: " + sel.options.length + " — aktiv: " + normalizeStoryTemplateId(sel.value));
    } catch (e) {
      showError(String(e.message || e));
      templateIds = ["generic","true_crime"];
      const sel = $("fd-template");
      sel.innerHTML = "";
      ["generic","true_crime"].forEach(function(id){
        const o = document.createElement("option");
        o.value = id; o.textContent = id; sel.appendChild(o);
      });
      sel.selectedIndex = 0;
      setStoryEngineRequestDebug("Template-Fallback aktiv (generic / true_crime). API template-selector fehlgeschlagen.");
    }
  }

  function lpAppendTextLink(container, label, href) {
    if (!container || !href) return;
    var a = document.createElement("a");
    a.href = href;
    a.textContent = label;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.className = "lp-file-link";
    container.appendChild(a);
  }

  function lpRenderPreviewArtifacts(toolbarEl, videoEl, urls) {
    if (!toolbarEl || !videoEl) return;
    toolbarEl.innerHTML = "";
    videoEl.innerHTML = "";
    urls = urls || {};
    var tu = document.createElement("div");
    tu.className = "lp-preview-btns";
    lpAppendTextLink(tu, "Preview öffnen", urls.preview_url);
    lpAppendTextLink(tu, "Report öffnen", urls.report_url);
    lpAppendTextLink(tu, "OPEN_ME öffnen", urls.open_me_url);
    lpAppendTextLink(tu, "JSON öffnen", urls.result_json_url);
    toolbarEl.appendChild(tu);
    if (urls.preview_url) {
      var v = document.createElement("video");
      v.controls = true;
      v.muted = true;
      v.setAttribute("preload", "metadata");
      v.setAttribute("playsinline", "");
      v.className = "lp-preview-video";
      v.src = urls.preview_url;
      var hint = document.createElement("p");
      hint.className = "muted";
      hint.style.marginTop = "0.35rem";
      hint.textContent = "Falls das Video nicht lädt, nutze „Preview öffnen“ (neuer Tab).";
      videoEl.appendChild(v);
      videoEl.appendChild(hint);
    } else {
      var mp = document.createElement("p");
      mp.className = "muted";
      mp.textContent = "Keine Preview-Datei gefunden.";
      videoEl.appendChild(mp);
    }
  }

  function lpRenderStatusCards(container, cards) {
    if (!container) return;
    container.innerHTML = "";
    if (!cards) {
      var emptyRun = document.createElement("p");
      emptyRun.className = "muted";
      emptyRun.textContent = "Noch kein Local Preview Run gefunden.";
      container.appendChild(emptyRun);
      return;
    }
    var defs = [
      ["Verdict", cards.verdict || "UNKNOWN"],
      ["Quality", cards.quality || "UNKNOWN"],
      ["Subtitle Q.", cards.subtitle_quality || "UNKNOWN"],
      ["Sync Guard", cards.sync_guard || "UNKNOWN"],
      ["Warning level", cards.warning_level || "UNKNOWN"],
      ["Founder decision", cards.founder_decision || "UNKNOWN"]
    ];
    var wrap = document.createElement("div");
    wrap.className = "lp-cards";
    defs.forEach(function(pair) {
      var c = document.createElement("div");
      c.className = "lp-card";
      var sl = document.createElement("span");
      sl.className = "lp-card-l";
      sl.textContent = pair[0];
      var sv = document.createElement("span");
      sv.className = "lp-card-v";
      sv.textContent = pair[1];
      c.appendChild(sl);
      c.appendChild(sv);
      wrap.appendChild(c);
    });
    container.appendChild(wrap);
    if (cards.contract_present === false) {
      var hint = document.createElement("p");
      hint.className = "muted";
      hint.style.marginTop = "0.35rem";
      hint.textContent = "Contract: nicht gefunden (älterer Run oder noch kein Lauf nach BA 22.1) — Status UNKNOWN.";
      container.appendChild(hint);
    }
  }

  function lpFmtEur(v) {
    if (v === null || v === undefined) return "—";
    if (typeof v !== "number") {
      try { v = Number(v); } catch (e) { return "—"; }
    }
    if (!isFinite(v)) return "—";
    return (Math.round(v * 100) / 100).toFixed(2) + " €";
  }

  function lpRenderCostCard(container, cost) {
    if (!container) return;
    container.innerHTML = "";
    cost = cost || {};
    var st = document.createElement("div");
    st.className = "lp-cost-row";
    var s1 = document.createElement("span");
    s1.className = "lp-cost-k";
    s1.textContent = "Status";
    var s2 = document.createElement("span");
    s2.className = "lp-cost-v";
    s2.textContent = (cost.status || "UNKNOWN");
    st.appendChild(s1);
    st.appendChild(s2);
    container.appendChild(st);

    function addLine(label, val) {
      var r = document.createElement("div");
      r.className = "lp-cost-row";
      var k = document.createElement("span");
      k.className = "lp-cost-k";
      k.textContent = label;
      var v = document.createElement("span");
      v.className = "lp-cost-v";
      v.textContent = val;
      r.appendChild(k);
      r.appendChild(v);
      container.appendChild(r);
    }

    var total = cost.actual_total_eur != null ? cost.actual_total_eur : cost.estimated_total_eur;
    addLine("Gesamt", lpFmtEur(total));
    var bd = cost.breakdown || {};
    addLine("Voice", lpFmtEur(bd.voice_eur));
    addLine("Assets", lpFmtEur(bd.assets_eur));
    addLine("Render", lpFmtEur(bd.render_eur));
    addLine("Puffer", lpFmtEur(bd.buffer_eur));

    var hint = document.createElement("p");
    hint.className = "muted";
    hint.style.marginTop = "0.35rem";
    hint.textContent = (cost.hint || "");
    container.appendChild(hint);
  }

  let lpLatestRunId = "";

  function lpRenderApprovalGate(container, gate, runId) {
    if (!container) return;
    container.innerHTML = "";
    gate = gate || {};
    runId = String(runId || "");
    var st = document.createElement("div");
    st.className = "lp-cost-row";
    var k1 = document.createElement("span");
    k1.className = "lp-cost-k";
    k1.textContent = "Status";
    var v1 = document.createElement("span");
    v1.className = "lp-cost-v";
    v1.textContent = (gate.status || "not_approved");
    st.appendChild(k1);
    st.appendChild(v1);
    container.appendChild(st);

    var r2 = document.createElement("div");
    r2.className = "lp-cost-row";
    var k2 = document.createElement("span");
    k2.className = "lp-cost-k";
    k2.textContent = "Eligible";
    var v2 = document.createElement("span");
    v2.className = "lp-cost-v";
    v2.textContent = gate.eligible ? "ja" : "nein";
    r2.appendChild(k2);
    r2.appendChild(v2);
    container.appendChild(r2);

    if (gate.reason) {
      var p = document.createElement("p");
      p.className = "muted";
      p.style.marginTop = "0.25rem";
      p.textContent = String(gate.reason);
      container.appendChild(p);
    }
    if (gate.approved_at || gate.approved_by) {
      var meta = document.createElement("p");
      meta.className = "muted";
      meta.style.margin = "0.25rem 0 0";
      meta.textContent = "Approved: " + (gate.approved_at || "—") + " · by " + (gate.approved_by || "—");
      container.appendChild(meta);
    }
    if (gate.note) {
      var note = document.createElement("p");
      note.className = "muted";
      note.style.margin = "0.25rem 0 0";
      note.textContent = "Note: " + String(gate.note);
      container.appendChild(note);
    }

    var msg = document.createElement("p");
    msg.className = "muted";
    msg.id = "lp-approval-msg";
    msg.style.margin = "0.3rem 0 0";
    msg.textContent = "";
    container.appendChild(msg);

    var row = document.createElement("div");
    row.className = "actions";
    row.style.marginTop = "0.35rem";
    row.style.display = "flex";
    row.style.flexWrap = "wrap";
    row.style.gap = "0.5rem";

    var bA = document.createElement("button");
    bA.type = "button";
    bA.id = "lp-btn-approve";
    bA.textContent = "Preview freigeben";
    bA.disabled = !(gate.actions && gate.actions.approve_enabled) || !runId;

    var bR = document.createElement("button");
    bR.type = "button";
    bR.id = "lp-btn-revoke";
    bR.textContent = "Freigabe zurückziehen";
    bR.disabled = !(gate.actions && gate.actions.revoke_enabled) || !runId;

    row.appendChild(bA);
    row.appendChild(bR);
    container.appendChild(row);

    bA.addEventListener("click", async function() {
      await fdLocalPreviewApprovalAction("approve", runId, bA, msg);
    });
    bR.addEventListener("click", async function() {
      await fdLocalPreviewApprovalAction("revoke", runId, bR, msg);
    });
  }

  async function fdLocalPreviewApprovalAction(kind, runId, btn, msgEl) {
    runId = String(runId || "");
    if (!runId) return;
    if (!btn || !msgEl) return;
    var label = btn.textContent || "";
    btn.disabled = true;
    btn.classList.add("is-loading");
    msgEl.textContent = "";
    msgEl.classList.remove("intake-status-err", "intake-status-success");
    try {
      if (isKillSwitchActive()) throw new Error("Kill Switch aktiv — Approval blockiert.");
      var url = kind === "revoke"
        ? ("/founder/dashboard/local-preview/revoke-approval/" + encodeURIComponent(runId))
        : ("/founder/dashboard/local-preview/approve/" + encodeURIComponent(runId));
      const r = await fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ note: "" })
      });
      let j = null;
      try { j = await r.json(); } catch (eJson) {}
      if (!r.ok || !j || j.ok !== true) {
        var m = (j && j.message) ? j.message : ("HTTP " + r.status);
        msgEl.textContent = "Approval: " + m;
        msgEl.classList.add("intake-status-err");
        return;
      }
      msgEl.textContent = "Approval gespeichert. Panel wird aktualisiert…";
      msgEl.classList.add("intake-status-success");
      try {
        await fdLoadLocalPreviewPanel();
        msgEl.textContent = "Approval gespeichert. Panel aktualisiert.";
      } catch (eReload) {
        msgEl.textContent = "Approval gespeichert, aber Panel konnte nicht aktualisiert werden.";
        msgEl.classList.remove("intake-status-success");
        msgEl.classList.add("intake-status-err");
      }
    } catch (e) {
      msgEl.textContent = "Approval: " + String(e && e.message ? e.message : e);
      msgEl.classList.add("intake-status-err");
    } finally {
      btn.textContent = label;
      btn.classList.remove("is-loading");
      btn.disabled = false;
    }
  }

  function lpRenderFinalRenderGate(container, gate) {
    if (!container) return;
    container.innerHTML = "";
    gate = gate || {};

    function row(label, val) {
      var r = document.createElement("div");
      r.className = "lp-cost-row";
      var k = document.createElement("span");
      k.className = "lp-cost-k";
      k.textContent = label;
      var v = document.createElement("span");
      v.className = "lp-cost-v";
      v.textContent = val;
      r.appendChild(k);
      r.appendChild(v);
      container.appendChild(r);
    }

    row("Status", String(gate.status || "unknown"));
    if (gate.reason) {
      var p = document.createElement("p");
      p.className = "muted";
      p.style.marginTop = "0.25rem";
      p.textContent = String(gate.reason);
      container.appendChild(p);
    }

    var reqs = (gate.requirements && Array.isArray(gate.requirements)) ? gate.requirements : [];
    if (reqs.length) {
      var ul = document.createElement("ul");
      ul.style.margin = "0.35rem 0 0";
      ul.style.paddingLeft = "1.15rem";
      reqs.forEach(function(rq) {
        var li = document.createElement("li");
        var id = String(rq.id || "");
        var lbl = String(rq.label || id);
        var st = String(rq.status || "unknown");
        var det = String(rq.detail || "");
        li.textContent = lbl + ": " + st + (det ? (" (" + det + ")") : "");
        ul.appendChild(li);
      });
      container.appendChild(ul);
    }

    var msg = document.createElement("p");
    msg.className = "muted";
    msg.id = "lp-final-render-msg";
    msg.style.margin = "0.3rem 0 0";
    msg.textContent = "";
    container.appendChild(msg);

    var dry = document.createElement("button");
    dry.type = "button";
    dry.id = "lp-btn-final-render-dry-run";
    dry.textContent = "Dry-Run prüfen";
    dry.addEventListener("click", async function() {
      msg.textContent = "Dry-Run läuft…";
      msg.classList.remove("intake-status-err", "intake-status-success");
      try {
        if (!lpLatestRunId) throw new Error("Kein run_id gefunden.");
        const r = await fetch("/founder/dashboard/local-preview/final-render/dry-run/" + encodeURIComponent(lpLatestRunId), { method: "POST" });
        let j = null;
        try { j = await r.json(); } catch (eJson) {}
        if (!r.ok || !j || j.ok !== true) {
          msg.textContent = "Dry-Run: " + (j && j.message ? j.message : ("HTTP " + r.status));
          msg.classList.add("intake-status-err");
          return;
        }
        msg.textContent = (j.message || "Dry-Run ok") + " (status: " + (j.status || "?") + ")";
        msg.classList.add("intake-status-success");
      } catch (e) {
        msg.textContent = "Dry-Run: " + String(e && e.message ? e.message : e);
        msg.classList.add("intake-status-err");
      }
    });
    container.appendChild(dry);

    var btn = document.createElement("button");
    btn.type = "button";
    btn.id = "lp-btn-final-render";
    btn.textContent = String(gate.label || "Finales Video erstellen");
    btn.disabled = !(gate.button_enabled === true);
    btn.addEventListener("click", async function() {
      if (btn.disabled) return;
      msg.textContent = "Final Render läuft…";
      msg.classList.remove("intake-status-err", "intake-status-success");
      btn.disabled = true;
      btn.classList.add("is-loading");
      try {
        if (!lpLatestRunId) throw new Error("Kein run_id gefunden.");
        const r = await fetch(
          "/founder/dashboard/local-preview/final-render/run/" + encodeURIComponent(lpLatestRunId),
          { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ force: false }) }
        );
        let j = null;
        try { j = await r.json(); } catch (eJson) {}
        if (!r.ok || !j) {
          msg.textContent = "Final Render fehlgeschlagen: HTTP " + r.status;
          msg.classList.add("intake-status-err");
          return;
        }
        if (j.ok === true) {
          if (j.status === "completed") msg.textContent = "Final Render abgeschlossen.";
          else if (j.status === "skipped_existing") msg.textContent = "Final Render existiert bereits.";
          else msg.textContent = "Final Render: " + (j.status || "ok");
          msg.classList.add("intake-status-success");
        } else {
          msg.textContent = "Final Render gesperrt: " + (j.message || (j.status || "locked"));
          msg.classList.add("intake-status-err");
        }
        try {
          await fdLoadLocalPreviewPanel();
        } catch (eReload) {}
      } catch (e) {
        msg.textContent = "Final Render fehlgeschlagen: " + String(e && e.message ? e.message : e);
        msg.classList.add("intake-status-err");
      } finally {
        btn.classList.remove("is-loading");
        btn.disabled = false;
      }
    });
    container.appendChild(btn);
  }

  async function fdLoadLocalPreviewPanel() {
    var st = document.getElementById("lp-panel-status");
    var body = document.getElementById("lp-panel-body");
    var rootEl = document.getElementById("lp-out-root");
    var actEl = document.getElementById("lp-actions");
    var runsEl = document.getElementById("lp-runs-wrap");
    var cardsEl = document.getElementById("lp-latest-cards");
    var costEl = document.getElementById("lp-cost-card");
    var apprEl = document.getElementById("lp-approval-card");
    var frEl = document.getElementById("lp-final-render-card");
    var tiEl = document.getElementById("lp-top-issue");
    var nsEl = document.getElementById("lp-next-step");
    var tbPrev = document.getElementById("lp-preview-toolbar");
    var vidWrap = document.getElementById("lp-preview-video-wrap");
    if (!st || !body || !rootEl || !actEl || !runsEl) return;
    try {
      const r = await fetch("/founder/dashboard/local-preview/panel", { method: "GET" });
      if (!r.ok) {
        st.textContent = "Local Preview konnte nicht geladen werden (HTTP " + r.status + ").";
        st.classList.add("intake-status-err");
        return;
      }
      const data = await r.json();
      st.textContent = "Local Preview geladen · Contract " + (data.result_contract && data.result_contract.id ? data.result_contract.id : "?")
        + " · Läufe: " + ((data.runs && data.runs.length) || 0);
      st.classList.remove("intake-status-err");
      rootEl.textContent = "out_root: " + (data.out_root || "") + (data.out_root_exists ? "" : " (nicht lesbar)");
      try {
        if (costEl) {
          var cc = data.latest_cost_card;
          if (!cc && data.runs && data.runs.length) cc = data.runs[0].cost_card || null;
          lpRenderCostCard(costEl, cc || null);
        }
        if (apprEl) {
          lpLatestRunId = (data.runs && data.runs.length && data.runs[0].run_id) ? String(data.runs[0].run_id) : "";
          var ag = data.latest_approval_gate;
          if (!ag && data.runs && data.runs.length) ag = data.runs[0].approval_gate || null;
          lpRenderApprovalGate(apprEl, ag || null, lpLatestRunId);
        }
        if (frEl) {
          var fg = data.latest_final_render_gate;
          if (!fg && data.runs && data.runs.length) fg = data.runs[0].final_render_gate || null;
          lpRenderFinalRenderGate(frEl, fg || null);
        }
        var latest = data.latest_status_cards;
        if (!latest && data.runs && data.runs.length) {
          latest = data.runs[0].status_cards || null;
        }
        if (cardsEl) {
          if (!(data.runs && data.runs.length)) {
            lpRenderStatusCards(cardsEl, null);
          } else {
            lpRenderStatusCards(cardsEl, latest);
          }
        }
        if (tiEl && nsEl) {
          if (latest && latest.top_issue) {
            tiEl.style.display = "block";
            tiEl.textContent = "Wichtigster Hinweis: " + latest.top_issue;
          } else {
            tiEl.style.display = "none";
          }
          if (latest && latest.next_step) {
            nsEl.style.display = "block";
            nsEl.textContent = "Nächster Schritt: " + latest.next_step;
          } else {
            nsEl.style.display = "none";
          }
        }
        var latestUrls = data.latest_file_urls || {};
        if ((!latestUrls.preview_url && !latestUrls.report_url) && data.runs && data.runs.length) {
          latestUrls = data.runs[0].file_urls || latestUrls;
        }
        if (tbPrev && vidWrap) {
          lpRenderPreviewArtifacts(tbPrev, vidWrap, latestUrls);
        }
        actEl.innerHTML = "";
        (data.actions || []).forEach(function(a) {
          var wrap = document.createElement("div");
          wrap.className = "lp-act";
          var h = document.createElement("h4");
          h.textContent = (a.label_de || a.id || "Aktion");
          wrap.appendChild(h);
          if (a.kind === "shell" && a.example) {
            var pre = document.createElement("pre");
            pre.className = "out";
            pre.textContent = a.example;
            wrap.appendChild(pre);
          } else if (a.kind === "doc" && a.path) {
            var p = document.createElement("p");
            p.className = "muted";
            p.style.margin = "0";
            p.textContent = "Repo: " + a.path;
            wrap.appendChild(p);
          }
          actEl.appendChild(wrap);
        });
        runsEl.innerHTML = "";
        if (!(data.runs && data.runs.length)) {
          var empty = document.createElement("p");
          empty.className = "muted";
          empty.textContent = "Noch kein Local Preview Run gefunden.";
          runsEl.appendChild(empty);
        } else {
          var tbl = document.createElement("table");
          tbl.className = "data";
          tbl.innerHTML = "<thead><tr><th>run_id</th><th>Verdict</th><th>Quality</th><th>Founder decision</th><th>Warning level</th><th>OPEN_ME</th><th>Report</th><th>Preview MP4</th><th>Aktionen</th></tr></thead><tbody></tbody>";
          var tb = tbl.querySelector("tbody");
          data.runs.forEach(function(run) {
            var ar = run.artifacts || {};
            var sc = run.status_cards || {};
            var fu = run.file_urls || {};
            var tr = document.createElement("tr");
            function tdText(val) {
              var d = document.createElement("td");
              d.textContent = val;
              return d;
            }
            tr.appendChild(tdText(run.run_id || ""));
            tr.appendChild(tdText(sc.verdict || "UNKNOWN"));
            tr.appendChild(tdText(sc.quality || "UNKNOWN"));
            tr.appendChild(tdText(sc.founder_decision || "UNKNOWN"));
            tr.appendChild(tdText(sc.warning_level || "UNKNOWN"));
            tr.appendChild(tdText(ar.open_me ? "ja" : "nein"));
            tr.appendChild(tdText(ar.founder_report ? "ja" : "nein"));
            tr.appendChild(tdText(ar.preview_with_subtitles ? "ja" : "nein"));
            var act = document.createElement("td");
            function addAct(label, u) {
              if (!u) return;
              var a = document.createElement("a");
              a.href = u;
              a.textContent = label;
              a.target = "_blank";
              a.rel = "noopener noreferrer";
              a.style.marginRight = "0.35rem";
              a.style.fontSize = "0.72rem";
              act.appendChild(a);
            }
            addAct("Preview", fu.preview_url);
            addAct("Report", fu.report_url);
            addAct("OPEN_ME", fu.open_me_url);
            addAct("JSON", fu.result_json_url);
            if (!act.textContent.trim()) {
              var sp = document.createElement("span");
              sp.className = "muted";
              sp.textContent = "—";
              act.appendChild(sp);
            }
            tr.appendChild(act);
            tb.appendChild(tr);
          });
          runsEl.appendChild(tbl);
        }
      } catch (renderErr) {
        if (st) {
          st.textContent = "Local Preview (Render): " + (renderErr && renderErr.message ? renderErr.message : String(renderErr));
          st.classList.add("intake-status-err");
        }
      }
      body.style.display = "block";
    } catch (e) {
      st.textContent = "Local Preview Panel: " + (e && e.message ? e.message : String(e));
      st.classList.add("intake-status-err");
    }
  }

  function fdFpCopyToClipboard(text, btn) {
    var t = String(text || "").trim();
    if (!t || !navigator.clipboard || !navigator.clipboard.writeText) return;
    navigator.clipboard.writeText(t).then(function() {
      if (btn) {
        btn.classList.add("is-success");
        setTimeout(function() { btn.classList.remove("is-success"); }, 900);
      }
    }).catch(function() {});
  }

  function fdFpArtifactFileUrl(absPath) {
    return "/founder/dashboard/fresh-preview/file?path=" + encodeURIComponent(String(absPath || ""));
  }

  function fdFpIsArtifactOpenable(absPath) {
    var s = String(absPath || "").trim().toLowerCase();
    if (!s) return false;
    return /\.(md|json|txt)$/.test(s);
  }

  function fdFpBuildPathRow(label, pathVal) {
    var wrap = document.createElement("div");
    wrap.className = "fp-path-row";
    var has = !!(pathVal && String(pathVal).trim());
    var pl = document.createElement("span");
    pl.className = "fp-path-label";
    pl.textContent = label;
    var v = document.createElement("span");
    v.className = "fp-path-value muted";
    v.textContent = has ? String(pathVal) : "Noch kein Pfad";
    var openEl;
    if (has && fdFpIsArtifactOpenable(pathVal)) {
      openEl = document.createElement("a");
      openEl.href = fdFpArtifactFileUrl(pathVal);
      openEl.target = "_blank";
      openEl.rel = "noopener noreferrer";
      openEl.className = "fp-open-artifact";
      openEl.textContent = "Öffnen";
      openEl.setAttribute("data-ba309-open", label);
    } else {
      openEl = document.createElement("span");
      openEl.className = "fp-open-placeholder";
      openEl.setAttribute("aria-hidden", "true");
    }
    var b = document.createElement("button");
    b.type = "button";
    b.className = "fp-copy-path";
    b.textContent = "Kopieren";
    b.setAttribute("data-ba305-copy-path", label);
    b.disabled = !has;
    if (has) {
      (function(pv, bt) {
        b.onclick = function() { fdFpCopyToClipboard(pv, bt); };
      })(String(pathVal), b);
    }
    wrap.appendChild(pl);
    wrap.appendChild(v);
    wrap.appendChild(openEl);
    wrap.appendChild(b);
    return wrap;
  }

  function fdFpFillReasonList(elId, title, items) {
    var el = document.getElementById(elId);
    if (!el) return;
    el.innerHTML = "";
    if (!items || !items.length) {
      el.style.display = "none";
      return;
    }
    el.style.display = "block";
    var h = document.createElement("div");
    h.className = "fp-reasons-title";
    h.textContent = title;
    el.appendChild(h);
    var ul = document.createElement("ul");
    items.forEach(function(x) {
      var li = document.createElement("li");
      li.textContent = String(x);
      ul.appendChild(li);
    });
    el.appendChild(ul);
  }

  async function fdStartFreshPreviewDryRun() {
    var st = document.getElementById("fp-dry-run-status");
    var resEl = document.getElementById("fp-dry-run-result");
    var handoffWrap = document.getElementById("fp-dry-run-handoff");
    var btn = document.getElementById("fp-btn-start-dry-run");
    if (!btn) return;
    var label = btn.getAttribute("data-label") || btn.textContent || "Dry-Run starten";
    if (isKillSwitchActive()) {
      if (st) {
        st.textContent = "Kill Switch aktiv — Fresh-Preview-Dry-Run blockiert.";
        st.classList.add("intake-status-err");
      }
      return;
    }
    var topicEl = document.getElementById("fp-dry-topic");
    var urlEl = document.getElementById("fp-dry-url");
    var durEl = document.getElementById("fp-dry-duration");
    var msEl = document.getElementById("fp-dry-max-scenes");
    var topic = topicEl ? String(topicEl.value || "").trim() : "";
    var url = urlEl ? String(urlEl.value || "").trim() : "";
    if (st) {
      st.classList.remove("intake-status-err", "intake-status-success");
    }
    if (!topic && !url) {
      if (st) {
        st.textContent = "Bitte genau eines ausfüllen: Topic oder URL.";
        st.classList.add("intake-status-err");
      }
      return;
    }
    if (topic && url) {
      if (st) {
        st.textContent = "Nur Topic oder URL — nicht beides gleichzeitig.";
        st.classList.add("intake-status-err");
      }
      return;
    }
    var dur = durEl ? parseInt(durEl.value, 10) : 45;
    if (isNaN(dur) || dur < 5) dur = 45;
    var maxSc = msEl ? parseInt(msEl.value, 10) : 6;
    if (isNaN(maxSc) || maxSc < 1) maxSc = 6;
    var body = {
      topic: topic || null,
      url: url || null,
      duration_target_seconds: dur,
      max_scenes: maxSc,
      provider: "placeholder"
    };
    btn.disabled = true;
    btn.classList.add("is-loading");
    btn.classList.remove("is-success", "is-error");
    btn.textContent = "Dry-Run läuft…";
    if (resEl) {
      resEl.style.display = "none";
      resEl.textContent = "";
    }
    if (handoffWrap) handoffWrap.style.display = "none";
    if (st) st.textContent = "Starte Fresh-Preview-Dry-Run…";
    try {
      const r = await fetch("/founder/dashboard/fresh-preview/start-dry-run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body)
      });
      var j = null;
      try { j = await r.json(); } catch (eJson) {}
      if (!r.ok) {
        var detail = j && j.detail != null ? j.detail : ("HTTP " + r.status);
        if (st) {
          st.textContent = "Dry-Run: " + String(detail);
          st.classList.add("intake-status-err");
        }
        if (handoffWrap) handoffWrap.style.display = "none";
        btn.classList.add("is-error");
        return;
      }
      if (!j || j.ok !== true) {
        if (st) {
          st.textContent = "Dry-Run beendet mit Blockern. Siehe Details.";
          st.classList.add("intake-status-err");
        }
        if (resEl) {
          resEl.style.display = "block";
          resEl.classList.remove("out-empty");
          resEl.textContent = JSON.stringify(j, null, 2);
        }
        if (handoffWrap) handoffWrap.style.display = "none";
        btn.classList.add("is-error");
        return;
      }
      if (st) {
        st.textContent = (j.snapshot_hint || "Snapshot aktualisieren") + " — Run " + (j.run_id || "—");
        st.classList.add("intake-status-success");
      }
      if (resEl) {
        resEl.style.display = "block";
        resEl.classList.remove("out-empty");
        resEl.textContent = JSON.stringify(j, null, 2);
      }
      var handoffPre = document.getElementById("fp-dry-run-handoff-ps");
      var hn = document.getElementById("fp-handoff-note");
      var hw = document.getElementById("fp-handoff-warning");
      if (handoffWrap && j.handoff_cli_command_powershell) {
        handoffWrap.style.display = "block";
        if (handoffPre) handoffPre.textContent = j.handoff_cli_command_powershell;
        if (hn) hn.textContent = j.handoff_note || "";
        if (hw) hw.textContent = j.handoff_warning || "";
      } else if (handoffWrap) {
        handoffWrap.style.display = "none";
      }
      btn.classList.add("is-success");
      try { await fdLoadFreshPreviewSnapshot(); } catch (eRef) {}
    } catch (e) {
      if (st) {
        st.textContent = "Dry-Run: " + (e && e.message ? e.message : String(e));
        st.classList.add("intake-status-err");
      }
      if (handoffWrap) handoffWrap.style.display = "none";
      btn.classList.add("is-error");
    } finally {
      btn.textContent = label;
      btn.disabled = false;
      btn.classList.remove("is-loading");
    }
  }

  function fdFpReadinessGaugeModifier(rs) {
    if (rs === "ready") return "fd-score-gauge-ring--ready";
    if (rs === "warning") return "fd-score-gauge-ring--warning";
    if (rs === "blocked") return "fd-score-gauge-ring--blocked";
    return "fd-score-gauge-ring--neutral";
  }

  function fdFpSyncReadinessRings(mod, pctStr) {
    var main = document.getElementById("fp-preview-power-ring");
    if (main) {
      main.className = "fp-preview-power-ring fd-score-gauge-ring " + mod;
      main.style.setProperty("--fd-sg-pct", pctStr);
    }
    var side = document.getElementById("fd-sidebar-preview-power-ring");
    if (side) {
      side.className = "fd-score-gauge-ring " + mod;
      side.style.setProperty("--fd-sg-pct", pctStr);
    }
    var ex = document.getElementById("fp-exec-readiness-ring");
    if (ex) {
      ex.className = "fd-score-gauge-ring " + mod;
      ex.style.setProperty("--fd-sg-pct", pctStr);
    }
  }

  function fdFpResetPreviewPowerNeutral() {
    var pv = document.getElementById("fp-preview-power-value");
    var pl = document.getElementById("fp-preview-power-label");
    var sidePp = document.getElementById("fd-sidebar-preview-power");
    fdFpSyncReadinessRings("fd-score-gauge-ring--neutral", "0");
    if (sidePp) {
      sidePp.textContent = "Noch kein Score";
      sidePp.classList.add("fd-sidebar-score-v--empty");
    }
    if (pv) {
      pv.textContent = "Noch kein Score";
      pv.classList.add("fd-score-gauge-value--empty");
    }
    if (pl) pl.textContent = "";
  }

  function fdFpUpdatePreviewPower(d) {
    var pv = document.getElementById("fp-preview-power-value");
    var pl = document.getElementById("fp-preview-power-label");
    var sidePp = document.getElementById("fd-sidebar-preview-power");
    var rs = String(d.readiness_status || "").toLowerCase();
    var raw = d.readiness_score;
    var hasNum = raw !== null && raw !== undefined && raw !== "" && !isNaN(Number(raw));
    var scoreNum = hasNum ? Math.max(0, Math.min(100, Number(raw))) : null;
    var mod = fdFpReadinessGaugeModifier(rs);
    var pctStr = scoreNum == null ? "0" : String(scoreNum);
    fdFpSyncReadinessRings(mod, pctStr);
    if (sidePp) {
      if (scoreNum == null) {
        sidePp.textContent = "Noch kein Score";
        sidePp.classList.add("fd-sidebar-score-v--empty");
      } else {
        sidePp.textContent = String(Math.round(scoreNum)) + "%";
        sidePp.classList.remove("fd-sidebar-score-v--empty");
      }
    }
    if (!pv || !pl) return;
    if (scoreNum == null) {
      pv.textContent = "Noch kein Score";
      pv.classList.add("fd-score-gauge-value--empty");
      pl.textContent = "";
      return;
    }
    pv.classList.remove("fd-score-gauge-value--empty");
    pv.textContent = String(Math.round(scoreNum)) + "%";
    if (rs === "ready") pl.textContent = "Ready";
    else if (rs === "warning") pl.textContent = "Warning";
    else if (rs === "blocked") pl.textContent = "Blocked";
    else pl.textContent = "—";
  }

  async function fdLoadFreshPreviewSnapshot() {
    var st = document.getElementById("fp-snapshot-status");
    var out = document.getElementById("out-fp-snapshot");
    if (!st || !out) return;
    try {
      if (isKillSwitchActive()) {
        st.textContent = "Kill Switch aktiv — Fresh-Preview-Snapshot übersprungen.";
        return;
      }
      const r = await fetch("/founder/dashboard/fresh-preview/snapshot", { method: "GET" });
      if (!r.ok) {
        st.textContent = "Fresh Preview Snapshot: HTTP " + r.status;
        st.classList.add("intake-status-err");
        fdFpResetPreviewPowerNeutral();
        return;
      }
      const d = await r.json();
      st.textContent = "Snapshot geladen · read-only · " + (d.fresh_preview_snapshot_version || "ba30_4_v1");
      st.classList.remove("intake-status-err");
      var rs = String(d.readiness_status || "").toLowerCase();
      var badge = document.getElementById("fp-readiness-badge");
      var scEl = document.getElementById("fp-readiness-score");
      if (badge) {
        var bl = rs === "ready" ? "READY" : (rs === "warning" ? "WARNING" : (rs === "blocked" ? "BLOCKED" : "OFFEN"));
        badge.textContent = bl;
        badge.className = "fp-readiness-badge " + (rs === "ready" ? "fp-readiness-ready" : (rs === "warning" ? "fp-readiness-warning" : (rs === "blocked" ? "fp-readiness-blocked" : "fp-readiness-unknown")));
      }
      if (scEl) scEl.textContent = d.readiness_score != null ? ("Score: " + String(d.readiness_score) + " / 100 · Score basiert auf Fresh Preview Readiness") : "Readiness wird nach dem Snapshot berechnet";
      fdFpUpdatePreviewPower(d);
      var nsOp = String(d.operator_next_step || "").trim();
      var exFs = document.getElementById("fp-exec-fresh-status");
      if (exFs) exFs.textContent = d.fresh_preview_available ? "Aktiv" : "Noch kein Fresh Preview Run gefunden";
      var exScore = document.getElementById("fp-exec-readiness-score");
      if (exScore) exScore.textContent = d.readiness_score != null ? String(d.readiness_score) + " / 100" : "Nicht bewertet";
      var exRun = document.getElementById("fp-exec-latest-run");
      if (exRun) exRun.textContent = d.latest_run_id || "Noch kein Run";
      var exNx = document.getElementById("fp-exec-next-step-short");
      if (exNx) {
        exNx.textContent = nsOp ? (nsOp.length > 72 ? nsOp.slice(0, 72) + "…" : nsOp) : "Starte einen Dry-Run, um den ersten Snapshot zu erzeugen";
        exNx.setAttribute("title", nsOp || "");
      }
      var hFresh = document.getElementById("fp-exec-hint-fresh");
      if (hFresh) hFresh.textContent = d.fresh_preview_available ? "" : "Starte einen Dry-Run, um den ersten Snapshot zu erzeugen";
      var hScore = document.getElementById("fp-exec-hint-score");
      if (hScore) hScore.textContent = d.readiness_score != null ? "" : "Readiness wird nach dem Snapshot berechnet";
      var hRun = document.getElementById("fp-exec-hint-run");
      if (hRun) hRun.textContent = d.latest_run_id ? "" : "Der zuletzt erkannte Run erscheint hier";
      var hNext = document.getElementById("fp-exec-hint-next");
      if (hNext) hNext.textContent = nsOp ? "" : "Wird aus Snapshot und Readiness abgeleitet";
      var nextBox = document.getElementById("fp-next-step-box");
      var nextText = document.getElementById("fp-operator-next-step");
      if (nextBox && nextText) {
        nextText.textContent = nsOp || "Starte einen Dry-Run, um den ersten Snapshot zu erzeugen";
        var ncls = "fp-next-step-box ";
        if (rs === "ready") ncls += "fp-next-step--ready";
        else if (rs === "warning") ncls += "fp-next-step--warning";
        else if (rs === "blocked") ncls += "fp-next-step--blocked";
        else ncls += "fp-next-step--neutral";
        nextBox.className = ncls;
      }
      var pr = document.getElementById("fp-path-rows");
      if (pr) {
        pr.innerHTML = "";
        pr.appendChild(fdFpBuildPathRow("Run-Ordner", d.latest_run_dir));
        pr.appendChild(fdFpBuildPathRow("script.json", d.script_path));
        pr.appendChild(fdFpBuildPathRow("scene_asset_pack.json", d.scene_asset_pack_path));
        pr.appendChild(fdFpBuildPathRow("asset_manifest.json", d.asset_manifest_path));
        pr.appendChild(fdFpBuildPathRow("preview_smoke_summary", d.preview_smoke_summary_path));
        pr.appendChild(fdFpBuildPathRow("OPEN_PREVIEW_SMOKE.md", d.open_preview_smoke_report_path));
      }
      fdFpFillReasonList("fp-blocking-list", "Freigabe blockiert (Review)", d.blocking_reasons);
      fdFpFillReasonList("fp-readiness-list", "Readiness zur Prüfung", d.readiness_reasons);
      fdFpFillReasonList("fp-scan-warnings-list", "Pfade und Dateien (Review)", d.warnings);
      var lines = [];
      lines.push("Fresh Preview — Kurzüberblick (Details oben)");
      lines.push("- Readiness: " + (d.readiness_status || "—") + " · Score: " + (d.readiness_score != null ? d.readiness_score : "—"));
      lines.push("- fresh_preview_available: " + (d.fresh_preview_available ? "ja" : "nein"));
      lines.push("- latest_run_id: " + (d.latest_run_id || "—"));
      lines.push("- Artefakt-Flags: script " + (d.script_json_present ? "ja" : "nein") + " · pack " + (d.scene_asset_pack_present ? "ja" : "nein") + " · manifest " + (d.asset_manifest_present ? "ja" : "nein") + " · summary " + (d.preview_smoke_summary_present ? "ja" : "nein") + " · open_me " + (d.open_preview_smoke_report_present ? "ja" : "nein"));
      out.textContent = lines.join("\n");
      out.classList.remove("out-empty");
    } catch (e) {
      st.textContent = "Fresh Preview Snapshot: " + String(e && e.message ? e.message : e);
      st.classList.add("intake-status-err");
      fdFpResetPreviewPowerNeutral();
    }
  }

  async function fdRunLocalPreviewMiniFixture() {
    var btn = document.getElementById("lp-btn-run-mini");
    var st = document.getElementById("lp-run-status");
    if (!btn || !st) return;
    var label = btn.getAttribute("data-label") || btn.textContent || "Preview erstellen";
    btn.setAttribute("data-label", label);
    btn.disabled = true;
    btn.classList.add("is-loading");
    btn.classList.remove("is-success", "is-error");
    btn.textContent = "Preview läuft…";
    st.textContent = "";
    st.classList.remove("intake-status-err", "intake-status-success", "intake-status-info");
    try {
      if (isKillSwitchActive()) throw new Error("Kill Switch aktiv — Preview-Start blockiert.");
      const r = await fetch("/founder/dashboard/local-preview/run-mini-fixture", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ run_id: "mini_e2e", force_burn: false, skip_preflight: false })
      });
      let j = null;
      try { j = await r.json(); } catch (eJson) {}
      if (!r.ok) {
        st.textContent = "Preview-Start: HTTP " + r.status;
        st.classList.add("intake-status-err");
        return;
      }
      if (!j || j.ok !== true) {
        var msg = (j && j.message) ? j.message : "Preview-Start fehlgeschlagen.";
        var hint = (j && j.preflight && j.preflight.setup_hint) ? String(j.preflight.setup_hint) : "";
        st.textContent = msg + (hint ? (" " + hint) : "");
        st.classList.add("intake-status-err");
        return;
      }
      st.textContent = "Preview-Lauf abgeschlossen. Panel wird aktualisiert…";
      st.classList.add("intake-status-success");
      try {
        await fdLoadLocalPreviewPanel();
        st.textContent = "Preview-Lauf abgeschlossen. Panel aktualisiert.";
      } catch (eReload) {
        st.textContent = "Preview-Lauf abgeschlossen, aber Panel konnte nicht aktualisiert werden.";
        st.classList.remove("intake-status-success");
        st.classList.add("intake-status-err");
      }
    } catch (e) {
      st.textContent = "Preview-Start: " + String(e && e.message ? e.message : e);
      st.classList.add("intake-status-err");
    } finally {
      btn.textContent = label;
      btn.disabled = false;
      btn.classList.remove("is-loading");
    }
  }

  function fdBindSidebarNav() {
    var nav = document.getElementById("fd-sidebar-nav");
    if (!nav) return;
    nav.addEventListener("click", function(ev) {
      var t = ev.target && ev.target.closest("[data-fd-nav-scroll]");
      if (!t || t.disabled) return;
      ev.preventDefault();
      var scrollId = t.getAttribute("data-fd-nav-scroll");
      if (!scrollId) return;
      var detRaw = t.getAttribute("data-fd-nav-details");
      var detailsId = detRaw === null || detRaw === "" ? null : detRaw;
      openPanelAndScroll(detailsId, scrollId);
    });
  }

  function fdBootstrapDashboard() {
    try {
      console.log("FD_BOOTSTRAP_START");
      showError("FD_BOOTSTRAP_START");
    } catch (eBootLog) {}
    fdBindSidebarNav();
    var autoBtn = document.getElementById("btn-intake-body");
    if (!autoBtn) {
      try {
        showError("BTN_MISSING: btn-intake-body");
      } catch (eMiss) {}
    }
    var domTestBtn = document.getElementById("btn-dom-test");
    if (domTestBtn) {
      domTestBtn.addEventListener("click", function() {
        showError("DOM_TEST_OK");
      });
    }
    var headerPreviewCta = document.getElementById("fd-header-cta-local-preview");
    if (headerPreviewCta) {
      headerPreviewCta.addEventListener("click", function() {
        openPanelAndScroll(null, "panel-ba303-fresh-preview");
      });
    }

    $("fd-chapters").value = JSON.stringify(DEFAULT_CHAPTERS, null, 2);

    if (autoBtn) {
      autoBtn.onclick = function() {
        showError("BTN_CLICK_RAW");
        alert("BTN_CLICK_RAW");
      };
      autoBtn.addEventListener("click", async function() {
        var btn = autoBtn;
        clearWarnings();
        await withActionButton(btn, "coll-source-intake", "coll-input-panel", async function() {
          await runBuildBodyFromIntake();
        });
      });
    }
  var fillTestBodyBtn = $("btn-fill-test-body");
  if (fillTestBodyBtn) {
    fillTestBodyBtn.addEventListener("click", function() {
      clearWarnings();
      try {
        fillTestBodyIntoInputPanel();
      } catch (eFill) {
        showError(String(eFill.message || eFill));
        setIntakeStatus("Fill Test Body fehlgeschlagen.", "err");
      }
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

  async function onBuildExportPackageClick() {
    var btn = $("btn-export-package");
    if (!btn) return;
    showError("DEBUG: Build Export Button ausgelöst");
    setExportActionStatus("Build Export gestartet…", "info");
    clearWarnings();
    await withActionButton(btn, "coll-export", "out-export-full", async function() {
      await runExportOnlyInternal();
    });
  }

  function bindBuildExportPackageButton() {
    var el = $("btn-export-package");
    if (!el || el.getAttribute("data-fd-bound-export") === "1") return;
    el.setAttribute("data-fd-bound-export", "1");
    el.addEventListener("click", function() {
      onBuildExportPackageClick();
    });
  }

  bindBuildExportPackageButton();

  $("btn-preview").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-preview", "out-pq-score", async function() {
      await runPreviewOnlyInternal();
    });
  };

  $("btn-readiness").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-readiness", "out-readiness", async function() {
      await runReadinessOnlyInternal();
    });
  };

  $("btn-optimize").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-optimize", "out-leo", async function() {
      await runOptimizeOnlyInternal();
    });
  };

  $("btn-ctr").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-ctr", "out-ctr", async function() {
      await runCtrOnlyInternal();
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
    if (!templateIds || !templateIds.length) {
      showError("Batch Compare: keine Template-IDs — Template-Selector prüfen oder Seite neu laden.");
      btn.classList.add("is-error");
      setTimeout(function() { btn.classList.remove("is-error"); }, 1600);
      openPanelAndScroll("coll-batch", "batch-scroll-anchor");
      return;
    }
    await withActionButton(btn, "coll-batch", "batch-scroll-anchor", async function() {
      var batchRoot = $("coll-batch");
      if (batchRoot) batchRoot.open = true;
      var base = buildCurrentExportRequestFromForm();
      for (var i = 0; i < templateIds.length; i++) {
        var tid = templateIds[i];
        st.textContent = "Teste Template " + (i + 1) + " von " + templateIds.length + "…";
        var body = Object.assign({}, base, { video_template: tid });
        var prev = await fetchJson("/story-engine/export-package/preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        assertCompleteStoryResponse("/story-engine/export-package/preview", prev, "preview");
        var ready = await fetchJson("/story-engine/provider-readiness", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        assertCompleteStoryResponse("/story-engine/provider-readiness", ready, "readiness");
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
  var fdTpl = $("fd-template");
  if (fdTpl) {
    fdTpl.addEventListener("change", function() {
      setStoryEngineRequestDebug("Template aktiv: " + normalizeStoryTemplateId(this.value));
    });
  }
  updatePqBadge();
  refreshOperatorClarity();
  fdLoadLocalPreviewPanel();
  fdLoadFreshPreviewSnapshot();
    var lpBtn = document.getElementById("lp-btn-run-mini");
    if (lpBtn) {
      lpBtn.addEventListener("click", async function() {
        try { await fdRunLocalPreviewMiniFixture(); } catch (eLp) {}
      });
    }
    var fpRef = document.getElementById("fp-btn-refresh");
    if (fpRef) {
      fpRef.addEventListener("click", async function() {
        try { await fdLoadFreshPreviewSnapshot(); } catch (eFp) {}
      });
    }
    var fpDry = document.getElementById("fp-btn-start-dry-run");
    if (fpDry) {
      fpDry.addEventListener("click", async function() {
        try { await fdStartFreshPreviewDryRun(); } catch (eDry) {}
      });
    }
    var fpCopyHandoff = document.getElementById("fp-btn-copy-handoff-cli");
    if (fpCopyHandoff) {
      fpCopyHandoff.addEventListener("click", function() {
        var pre = document.getElementById("fp-dry-run-handoff-ps");
        var t = pre && pre.textContent ? pre.textContent.trim() : "";
        if (t) fdFpCopyToClipboard(t, fpCopyHandoff);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", fdBootstrapDashboard);
  } else {
    fdBootstrapDashboard();
  }
})();
} catch (globalErr) {
  console.error(globalErr);
  var _eb = document.getElementById("error-bar");
  if (_eb) {
    _eb.textContent = "GLOBAL_JS_FAIL: " + (globalErr && globalErr.message ? globalErr.message : String(globalErr));
    _eb.classList.add("visible");
  }
}
</script>
</body>
</html>"""
