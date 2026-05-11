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
.fd-header-reset-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0;
  max-width: 22rem;
}
.fd-btn-dashboard-reset {
  border: 1px solid rgba(248, 113, 113, 0.35);
  background: rgba(120, 40, 40, 0.15);
  color: #fecaca;
}
.fd-btn-dashboard-reset:hover:not(:disabled) {
  background: rgba(120, 40, 40, 0.28);
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
.fd-guided-flow {
  margin-bottom: 1.35rem;
  padding: 1.1rem 1.25rem 1.15rem;
  border-radius: 12px;
  border: 1px solid rgba(42, 51, 73, 0.95);
  background: linear-gradient(165deg, rgba(26, 34, 52, 0.92) 0%, rgba(18, 24, 38, 0.98) 100%);
  box-shadow: var(--vp-card-shadow);
}
.fd-guided-flow-head {
  margin-bottom: 0.85rem;
}
.fd-guided-flow-head h2 {
  margin: 0 0 0.2rem;
  font-size: 1.05rem;
  font-weight: 650;
  letter-spacing: -0.02em;
}
.fd-guided-flow-sub {
  margin: 0;
  font-size: 0.82rem;
  color: rgba(160, 176, 198, 0.88);
}
.fd-guided-flow-microcopy-help {
  margin: 0 0 0.75rem;
  font-size: 0.78rem;
  line-height: 1.45;
  color: rgba(160, 176, 198, 0.88);
}
.fd-guided-flow-step-detail {
  font-size: 0.68rem;
  line-height: 1.38;
  color: rgba(139, 156, 179, 0.92);
  margin: 0 0 0.4rem;
}
.fp-handoff-after {
  margin: 0.45rem 0 0;
  font-size: 0.76rem;
  line-height: 1.45;
}
.fd-guided-flow-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem 0.65rem;
  align-items: stretch;
  margin-bottom: 1rem;
}
@media (max-width: 767px) {
  .fd-guided-flow-steps {
    flex-direction: column;
  }
}
.fd-guided-flow-step {
  flex: 1 1 108px;
  min-width: 0;
  padding: 0.45rem 0.55rem;
  border-radius: 8px;
  border: 1px solid rgba(48, 58, 78, 0.95);
  background: rgba(0, 0, 0, 0.2);
}
.fd-guided-flow-step--current {
  border-color: rgba(0, 70, 255, 0.55);
  box-shadow: 0 0 0 1px rgba(0, 70, 255, 0.12);
}
.fd-guided-flow-step-num {
  font-size: 0.68rem;
  font-weight: 600;
  color: rgba(139, 156, 179, 0.85);
  margin-bottom: 0.15rem;
}
.fd-guided-flow-step-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(224, 232, 245, 0.92);
  margin-bottom: 0.35rem;
  line-height: 1.25;
}
.fd-guided-step-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 650;
  padding: 0.12rem 0.38rem;
  border-radius: 5px;
  letter-spacing: 0.02em;
}
.fd-guided-step-badge--done {
  background: rgba(34, 197, 94, 0.18);
  color: #86efac;
  border: 1px solid rgba(34, 197, 94, 0.35);
}
.fd-guided-step-badge--pending {
  background: rgba(148, 163, 184, 0.15);
  color: rgba(203, 213, 225, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.28);
}
.fd-guided-step-badge--warning {
  background: rgba(251, 191, 36, 0.14);
  color: #fcd34d;
  border: 1px solid rgba(251, 191, 36, 0.35);
}
.fd-guided-step-badge--blocked {
  background: rgba(248, 113, 113, 0.14);
  color: #fecaca;
  border: 1px solid rgba(248, 113, 113, 0.35);
}
.fd-guided-step-badge--locked {
  background: rgba(100, 116, 139, 0.2);
  color: rgba(203, 213, 225, 0.85);
  border: 1px solid rgba(100, 116, 139, 0.45);
}
.fd-guided-step-badge--active {
  background: rgba(59, 130, 246, 0.18);
  color: #93c5fd;
  border: 1px solid rgba(59, 130, 246, 0.4);
}
.fd-guided-flow-next {
  padding: 0.75rem 0.9rem;
  border-radius: 9px;
  border: 1px solid rgba(0, 70, 255, 0.28);
  background: rgba(0, 35, 120, 0.18);
}
.fd-guided-flow-next-kicker {
  font-size: 0.72rem;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(147, 197, 253, 0.85);
  margin-bottom: 0.28rem;
}
.fd-guided-flow-next-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(224, 232, 245, 0.88);
  margin-bottom: 0.35rem;
}
.fd-guided-flow-next-action {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.45;
  color: rgba(248, 250, 252, 0.95);
  font-weight: 520;
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
.fp-exec-next-btn {
  margin-top: 0.55rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  border: 1px solid rgba(100, 150, 255, 0.35);
  background: rgba(0, 70, 255, 0.08);
  color: rgba(200, 220, 255, 0.95);
}
.fp-exec-next-btn:hover:not(:disabled) { filter: brightness(1.06); }
.fp-exec-next-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.fd-vg-result-card {
  margin-top: 0.65rem;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(42, 51, 73, 0.75);
  background: rgba(12, 16, 26, 0.55);
}
.fd-vg-result-head {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
  align-items: center;
  justify-content: space-between;
}
.fd-vg-result-title { margin: 0; font-size: 0.95rem; }
.fd-vg-result-sub { margin: 0.25rem 0 0; font-size: 0.8rem; color: rgba(139, 156, 179, 0.9); }
.fd-vg-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  border: 1px solid rgba(54, 65, 88, 0.9);
  background: rgba(18, 24, 38, 0.75);
  color: rgba(210, 220, 235, 0.95);
}
.fd-vg-badge--ok { border-color: rgba(34, 197, 94, 0.45); background: rgba(34, 197, 94, 0.12); color: #bbf7d0; }
.fd-vg-badge--blocked { border-color: rgba(248, 113, 113, 0.55); background: rgba(248, 113, 113, 0.12); color: #fecaca; }
.fd-vg-badge--neutral { border-color: rgba(100, 150, 255, 0.35); background: rgba(0, 70, 255, 0.06); color: rgba(200, 220, 255, 0.95); }
.fd-vg-badge--fallback { border-color: rgba(245, 158, 11, 0.55); background: rgba(245, 158, 11, 0.10); color: rgba(253, 230, 138, 0.95); }
.fd-vg-kv { margin-top: 0.65rem; display: grid; gap: 0.35rem; }
.fd-vg-kv-row { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: baseline; }
.fd-vg-k { font-size: 0.72rem; color: rgba(139, 156, 179, 0.9); min-width: 130px; }
.fd-vg-v { font-size: 0.78rem; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; color: var(--text); word-break: break-word; }
.fd-vg-list { margin: 0.35rem 0 0; padding-left: 1.1rem; }
.fd-vg-cta { margin-top: 0.75rem; font-size: 0.82rem; }
.fd-vg-raw details { margin-top: 0.6rem; }

/* BA 32.91 — Founder Dashboard Production Timeline Preview Layer. */
.fd-vg-production-timeline {
  margin-top: 0.9rem;
  padding: 0.95rem;
  border: 1px solid rgba(94, 134, 255, 0.30);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(8, 19, 36, 0.72), rgba(3, 9, 18, 0.62));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}
.fd-vg-timeline-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.65rem;
}
.fd-vg-timeline-title { margin: 0; font-size: 0.92rem; letter-spacing: -0.015em; }
.fd-vg-timeline-meta { margin: 0.2rem 0 0; color: rgba(160, 176, 198, 0.92); font-size: 0.78rem; }
.fd-vg-timeline-duration {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  border: 1px solid rgba(94, 134, 255, 0.36);
  color: #d7e4ff;
  background: rgba(0, 70, 255, 0.10);
  font-size: 0.72rem;
  font-weight: 800;
  white-space: nowrap;
}
.fd-vg-timeline-shell { overflow-x: auto; padding: 0.15rem 0 0.2rem; }
.fd-vg-timeline-scale {
  min-width: 640px;
  display: flex;
  justify-content: space-between;
  color: rgba(139, 156, 179, 0.92);
  font-size: 0.68rem;
  margin: 0 0 0.35rem;
}
.fd-vg-timeline-track {
  min-width: 640px;
  display: flex;
  gap: 0.4rem;
  align-items: stretch;
  padding: 0.4rem;
  border: 1px solid rgba(64, 83, 113, 0.38);
  border-radius: 14px;
  background: rgba(2, 8, 18, 0.40);
}
.fd-vg-timeline-seg {
  position: relative;
  min-width: 118px;
  border: 1px solid rgba(105, 130, 169, 0.40);
  border-radius: 13px;
  padding: 0.55rem 0.6rem;
  background: rgba(18, 29, 47, 0.88);
  color: #edf4ff;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.12s ease, transform 0.12s ease, background 0.12s ease;
}
.fd-vg-timeline-seg:hover,
.fd-vg-timeline-seg.is-selected {
  border-color: rgba(94, 134, 255, 0.78);
  background: rgba(28, 45, 74, 0.96);
  transform: translateY(-1px);
}
.fd-vg-timeline-seg--motion {
  border-color: rgba(45, 212, 191, 0.58);
  background: linear-gradient(145deg, rgba(20, 184, 166, 0.20), rgba(17, 29, 47, 0.92));
  box-shadow: inset 0 0 0 1px rgba(45, 212, 191, 0.08);
}
.fd-vg-timeline-seg--placeholder { border-color: rgba(245, 158, 11, 0.56); }
.fd-vg-timeline-seg--missing,
.fd-vg-timeline-seg--failed { border-color: rgba(248, 113, 113, 0.58); }
.fd-vg-timeline-seg-label { display: block; font-weight: 850; font-size: 0.78rem; line-height: 1.25; }
.fd-vg-timeline-seg-time { display: block; margin-top: 0.18rem; color: rgba(190, 204, 224, 0.9); font-size: 0.68rem; }
.fd-vg-timeline-seg-type { display: block; margin-top: 0.3rem; color: rgba(139, 156, 179, 0.95); font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.08em; }
.fd-vg-timeline-status {
  display: inline-flex;
  margin-top: 0.42rem;
  padding: 0.14rem 0.45rem;
  border-radius: 999px;
  border: 1px solid rgba(139, 156, 179, 0.32);
  font-size: 0.63rem;
  font-weight: 850;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.fd-vg-timeline-status--ready { color: #bbf7d0; border-color: rgba(74, 222, 128, 0.42); background: rgba(74, 222, 128, 0.10); }
.fd-vg-timeline-status--placeholder,
.fd-vg-timeline-status--skipped { color: #fde68a; border-color: rgba(245, 158, 11, 0.48); background: rgba(245, 158, 11, 0.10); }
.fd-vg-timeline-status--missing,
.fd-vg-timeline-status--failed { color: #fecaca; border-color: rgba(248, 113, 113, 0.50); background: rgba(248, 113, 113, 0.10); }
.fd-vg-timeline-detail {
  margin-top: 0.75rem;
  display: grid;
  grid-template-columns: minmax(220px, 0.85fr) minmax(260px, 1.15fr);
  gap: 0.8rem;
}
@media (max-width: 820px) { .fd-vg-timeline-detail { grid-template-columns: 1fr; } }
.fd-vg-timeline-detail-card,
.fd-vg-timeline-preview {
  border: 1px solid rgba(64, 83, 113, 0.46);
  border-radius: 13px;
  background: rgba(3, 10, 20, 0.34);
  padding: 0.72rem;
}
.fd-vg-timeline-detail-title { margin: 0; font-size: 0.86rem; }
.fd-vg-timeline-detail-copy { margin: 0.35rem 0 0; color: rgba(190, 204, 224, 0.92); font-size: 0.78rem; }
.fd-vg-timeline-media-empty {
  min-height: 150px;
  display: grid;
  place-items: center;
  border: 1px dashed rgba(139, 156, 179, 0.32);
  border-radius: 12px;
  color: rgba(160, 176, 198, 0.86);
  text-align: center;
  padding: 0.9rem;
  background: rgba(2, 8, 18, 0.32);
}
.fd-vg-timeline-preview video,
.fd-vg-timeline-preview img {
  display: block;
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  border-radius: 11px;
  background: #020817;
}
.fd-vg-advanced-artifacts {
  margin-top: 0.75rem;
  border: 1px solid rgba(64, 83, 113, 0.46);
  border-radius: 13px;
  padding: 0.35rem 0.75rem 0.75rem;
  background: rgba(3, 10, 20, 0.22);
}
.fd-vg-advanced-artifacts > summary {
  cursor: pointer;
  color: rgba(160, 176, 198, 0.94);
  font-size: 0.8rem;
  font-weight: 750;
  padding: 0.35rem 0;
}
/* BA 32.70 — Founder Dashboard Visual Redesign V1: cockpit-style hierarchy. */
.fd-header-hero {
  z-index: 20;
  backdrop-filter: blur(18px);
}
.fd-header-actions { align-items: flex-start; }
.fd-app-shell {
  background:
    linear-gradient(90deg, rgba(0, 42, 118, 0.22) 0, rgba(0, 0, 0, 0) 250px),
    linear-gradient(180deg, rgba(9, 16, 30, 0.45), rgba(4, 8, 15, 0));
}
.fd-sidebar {
  background: linear-gradient(180deg, rgba(3, 14, 31, 0.96), rgba(2, 9, 20, 0.98));
  border-color: rgba(64, 83, 113, 0.7);
}
button.fd-sidebar-link {
  min-height: 2.4rem;
  padding: 0.55rem 0.72rem;
  border-color: transparent;
  background: transparent;
}
button.fd-sidebar-link:hover:not(:disabled), button.fd-sidebar-link:focus-visible {
  background: linear-gradient(90deg, rgba(0, 70, 255, 0.28), rgba(0, 70, 255, 0.08));
  border-color: rgba(78, 128, 255, 0.35);
}
.fd-exec-row {
  border: 1px solid rgba(64, 83, 113, 0.72);
  border-radius: 16px;
  padding: 0.75rem;
  background: linear-gradient(160deg, rgba(19, 31, 52, 0.74), rgba(8, 15, 27, 0.88));
  box-shadow: var(--vp-card-shadow);
}
.fp-exec-strip { grid-template-columns: repeat(4, minmax(0, 1fr)); }
@media (max-width: 1100px) { .fp-exec-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .fp-exec-strip { grid-template-columns: 1fr; } }
.fp-exec-cell {
  position: relative;
  overflow: hidden;
  border-color: rgba(78, 99, 132, 0.78);
  background: linear-gradient(150deg, rgba(30, 44, 68, 0.9), rgba(11, 19, 33, 0.94));
}
.fp-exec-cell::after {
  content: "";
  position: absolute;
  right: -2rem;
  top: -2.5rem;
  width: 6rem;
  height: 6rem;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(0, 70, 255, 0.16), transparent 68%);
  pointer-events: none;
}
.panel {
  border-color: rgba(64, 83, 113, 0.72);
  background: linear-gradient(160deg, rgba(24, 36, 56, 0.88), rgba(10, 17, 30, 0.96));
  border-radius: 16px;
}
.panel--video-generate {
  border-color: rgba(78, 128, 255, 0.38);
  box-shadow: var(--vp-card-shadow), 0 0 0 1px rgba(0, 70, 255, 0.08);
}
.panel-section-head h2 {
  font-size: clamp(1.15rem, 1.8vw, 1.55rem);
  color: var(--text);
  text-transform: none;
  letter-spacing: -0.03em;
}
.fd-vg-operator-brief {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0 0 1rem;
}
@media (max-width: 860px) { .fd-vg-operator-brief { grid-template-columns: 1fr; } }
.fd-vg-brief-card {
  padding: 0.85rem 0.95rem;
  border-radius: 13px;
  border: 1px solid rgba(67, 87, 118, 0.78);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.02));
}
.fd-vg-brief-k {
  display: block;
  margin-bottom: 0.28rem;
  color: rgba(160, 176, 198, 0.92);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.fd-vg-brief-v {
  display: block;
  color: rgba(244, 247, 251, 0.96);
  font-size: 0.92rem;
  font-weight: 650;
  line-height: 1.35;
}
.fd-vg-pipeline-steps {
  display: grid;
  grid-template-columns: repeat(6, minmax(90px, 1fr));
  gap: 0.55rem;
  margin: 0 0 1rem;
  padding: 0.75rem;
  border: 1px solid rgba(64, 83, 113, 0.62);
  border-radius: 14px;
  background: rgba(2, 8, 18, 0.26);
}
@media (max-width: 960px) { .fd-vg-pipeline-steps { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 560px) { .fd-vg-pipeline-steps { grid-template-columns: 1fr 1fr; } }
.fd-vg-step {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
  color: rgba(214, 224, 238, 0.92);
  font-size: 0.76rem;
  font-weight: 600;
}
.fd-vg-step-dot {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid rgba(90, 119, 160, 0.9);
  background: rgba(0, 70, 255, 0.14);
  color: #bcd0ff;
  font-size: 0.72rem;
}
.fd-vg-step--warn .fd-vg-step-dot {
  border-color: rgba(251, 191, 36, 0.82);
  color: #facc15;
  background: rgba(251, 191, 36, 0.08);
}
#fd-video-generate-form {
  gap: 0.9rem 1.15rem;
  align-items: start;
}
#fd-video-generate-form > div,
#fd-video-generate-form > details {
  min-width: 0;
}
#fd-video-generate-form label {
  font-weight: 650;
  letter-spacing: 0.01em;
}
.fd-vg-primary-note {
  grid-column: 1 / -1;
  margin: -0.2rem 0 0.1rem;
  padding: 0.72rem 0.85rem;
  border: 1px solid rgba(78, 128, 255, 0.28);
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(0, 70, 255, 0.10), rgba(3, 10, 20, 0.20));
  color: rgba(207, 219, 238, 0.94);
  font-size: 0.82rem;
  line-height: 1.45;
}
.fd-vg-advanced-params {
  grid-column: 1 / -1;
  margin: 0.15rem 0 0;
  padding: 0.35rem 0.85rem 0.85rem;
  border: 1px solid rgba(64, 83, 113, 0.62);
  border-radius: 14px;
  background: rgba(2, 8, 18, 0.24);
}
.fd-vg-advanced-params > summary {
  cursor: pointer;
  padding: 0.45rem 0;
  color: rgba(237, 244, 255, 0.96);
  font-size: 0.86rem;
  font-weight: 800;
  letter-spacing: -0.01em;
}
.fd-vg-advanced-params > summary::marker { color: rgba(94, 134, 255, 0.95); }
.fd-vg-advanced-copy {
  margin: 0 0 0.75rem;
  color: rgba(160, 176, 198, 0.94);
  font-size: 0.8rem;
  line-height: 1.45;
}
.fd-vg-advanced-grid { gap: 0.75rem 1rem; }
.fd-vg-primary-action {
  margin-top: 0.35rem;
  padding: 0.8rem;
  border: 1px solid rgba(78, 128, 255, 0.34);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(0, 70, 255, 0.12), rgba(3, 10, 20, 0.28));
}
button.fd-vg-main-cta {
  min-height: 3rem;
  padding: 0.78rem 1.45rem;
  font-size: 0.98rem;
  font-weight: 850;
  border-radius: 12px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.14) inset, 0 12px 34px rgba(0, 70, 255, 0.34);
}
input[type="text"], input[type="number"], input[type="url"], input[type="password"], textarea, select {
  min-height: 2.55rem;
  border-radius: 10px;
  border-color: rgba(67, 87, 118, 0.95);
  background: rgba(4, 12, 24, 0.62);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}
input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: rgba(69, 132, 255, 0.95);
  box-shadow: 0 0 0 3px rgba(0, 70, 255, 0.18);
}
.fp-dry-run-checks {
  padding: 0.75rem 0.85rem;
  border: 1px solid rgba(64, 83, 113, 0.62);
  border-radius: 12px;
  background: rgba(2, 8, 18, 0.24);
}
.fd-vg-section-title {
  margin: 0.9rem 0 0.45rem;
  color: rgba(238, 243, 249, 0.96);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.fd-vg-result-card {
  border-color: rgba(67, 87, 118, 0.78);
  background: linear-gradient(145deg, rgba(19, 30, 48, 0.94), rgba(7, 13, 24, 0.94));
}
.fd-vg-kv {
  padding: 0.65rem 0.75rem;
  border: 1px solid rgba(64, 83, 113, 0.52);
  border-radius: 12px;
  background: rgba(3, 10, 20, 0.28);
}
.fd-vg-kv-row {
  padding: 0.24rem 0;
  border-bottom: 1px solid rgba(64, 83, 113, 0.25);
}
.fd-vg-kv-row:last-child { border-bottom: 0; }
.fd-vg-list {
  padding: 0.6rem 0.75rem 0.6rem 1.5rem;
  border: 1px solid rgba(64, 83, 113, 0.52);
  border-radius: 12px;
  background: rgba(3, 10, 20, 0.28);
}
.fd-vg-raw summary {
  color: rgba(160, 176, 198, 0.94);
  cursor: pointer;
}
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
.fp-operator-review-card {
  margin: 0 0 1rem;
  padding: 0.95rem 1.05rem;
  border-radius: 11px;
  border: 1px solid rgba(54, 65, 88, 0.85);
  background: rgba(0, 0, 0, 0.14);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}
.fp-review-head { margin-bottom: 0.55rem; }
.fp-review-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.75rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 650;
  letter-spacing: 0.04em;
  border: 1px solid rgba(54, 65, 88, 0.9);
}
.fp-review-badge--approve {
  border-color: rgba(45, 160, 140, 0.45);
  background: rgba(34, 90, 78, 0.35);
  color: #a7f3d0;
}
.fp-review-badge--rework {
  border-color: rgba(217, 165, 70, 0.45);
  background: rgba(110, 85, 40, 0.22);
  color: #fde68a;
}
.fp-review-badge--blocked {
  border-color: rgba(220, 110, 110, 0.45);
  background: rgba(95, 45, 45, 0.22);
  color: #fecaca;
}
.fp-review-badge--pending {
  border-color: rgba(118, 132, 155, 0.4);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(196, 206, 220, 0.92);
}
.fp-review-reasons {
  margin: 0.45rem 0 0.35rem;
  padding-left: 1.15rem;
  font-size: 0.82rem;
  line-height: 1.45;
  color: rgba(224, 232, 245, 0.88);
}
.fp-review-next {
  margin: 0.5rem 0 0;
  font-size: 0.88rem;
  line-height: 1.5;
  font-weight: 520;
  color: rgba(236, 241, 248, 0.94);
}
.fp-final-render-gate-card {
  margin: 0 0 1rem;
  padding: 0.95rem 1.05rem;
  border-radius: 11px;
  border: 1px solid rgba(54, 65, 88, 0.85);
  background: rgba(0, 0, 0, 0.14);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}
.fp-fr-gate-head { margin-bottom: 0.55rem; }
.fp-fr-gate-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.75rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 650;
  letter-spacing: 0.04em;
  border: 1px solid rgba(54, 65, 88, 0.9);
}
.fp-fr-gate-badge--ready {
  border-color: rgba(45, 160, 140, 0.45);
  background: rgba(34, 90, 78, 0.35);
  color: #a7f3d0;
}
.fp-fr-gate-badge--locked {
  border-color: rgba(118, 132, 155, 0.4);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(196, 206, 220, 0.92);
}
.fp-fr-gate-badge--blocked {
  border-color: rgba(220, 110, 110, 0.45);
  background: rgba(95, 45, 45, 0.22);
  color: #fecaca;
}
.fp-fr-gate-badge--rework {
  border-color: rgba(217, 165, 70, 0.45);
  background: rgba(110, 85, 40, 0.22);
  color: #fde68a;
}
.fp-fr-gate-reasons {
  margin: 0.45rem 0 0.35rem;
  padding-left: 1.15rem;
  font-size: 0.82rem;
  line-height: 1.45;
  color: rgba(224, 232, 245, 0.88);
}
.fp-fr-gate-next {
  margin: 0.5rem 0 0;
  font-size: 0.88rem;
  line-height: 1.5;
  font-weight: 520;
  color: rgba(236, 241, 248, 0.94);
}
.fp-fr-gate-future-hint {
  margin: 0.55rem 0 0;
  font-size: 0.76rem;
  line-height: 1.45;
  color: rgba(139, 156, 179, 0.88);
}
.fp-fr-input-checklist-card {
  margin: 0 0 1rem;
  padding: 0.95rem 1.05rem;
  border-radius: 11px;
  border: 1px solid rgba(54, 65, 88, 0.85);
  background: rgba(0, 0, 0, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}
.fp-fr-input-head { margin-bottom: 0.55rem; }
.fp-fr-input-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.32rem 0.75rem;
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 650;
  letter-spacing: 0.04em;
  border: 1px solid rgba(54, 65, 88, 0.9);
}
.fp-fr-input-badge--ready {
  border-color: rgba(45, 160, 140, 0.45);
  background: rgba(34, 90, 78, 0.35);
  color: #a7f3d0;
}
.fp-fr-input-badge--pending {
  border-color: rgba(118, 132, 155, 0.4);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(196, 206, 220, 0.92);
}
.fp-fr-input-badge--warning {
  border-color: rgba(217, 165, 70, 0.45);
  background: rgba(110, 85, 40, 0.22);
  color: #fde68a;
}
.fp-fr-input-badge--blocked {
  border-color: rgba(220, 110, 110, 0.45);
  background: rgba(95, 45, 45, 0.22);
  color: #fecaca;
}
.fp-final-render-input-items {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  margin: 0.35rem 0 0.5rem;
}
.fp-fr-input-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(0, 2fr) auto auto;
  gap: 0.35rem 0.5rem;
  align-items: start;
  font-size: 0.78rem;
  padding: 0.4rem 0.45rem;
  border-radius: 8px;
  border: 1px solid rgba(48, 58, 78, 0.75);
  background: rgba(0, 0, 0, 0.15);
}
@media (max-width: 720px) {
  .fp-fr-input-row {
    grid-template-columns: 1fr;
  }
}
.fp-fr-input-row-label { font-weight: 600; color: rgba(224, 232, 245, 0.92); }
.fp-fr-input-row-meta { font-size: 0.68rem; color: rgba(139, 156, 179, 0.88); }
.fp-fr-input-row-path {
  word-break: break-all;
  color: rgba(196, 206, 220, 0.85);
  font-family: ui-monospace, monospace;
  font-size: 0.68rem;
}
.fp-fr-input-item-status {
  font-size: 0.65rem;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.fp-fr-input-item-status--present { color: #86efac; }
.fp-fr-input-item-status--missing { color: #fecaca; }
.fp-fr-input-item-status--unknown { color: rgba(148, 163, 184, 0.95); }
.fp-fr-input-item-status--optional { color: rgba(251, 191, 36, 0.95); }
.fp-fr-input-next {
  margin: 0.45rem 0 0;
  font-size: 0.86rem;
  line-height: 1.5;
  font-weight: 520;
  color: rgba(236, 241, 248, 0.94);
}
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
.fp-safe-final-handoff-card { margin-top: 0.85rem; }
#fp-safe-final-render-cli { margin: 0.5rem 0; max-height: 220px; font-size: 0.72rem; white-space: pre-wrap; word-break: break-word; }

/* BA 32.90 — Founder Dashboard Visual Skin V1: controlled UI skin from ChatGPT Image PNG reference. */
:root {
  --vp-blue: #0046FF;
  --fd-skin-bg: #050a13;
  --fd-skin-bg-2: #0b1424;
  --fd-skin-shell: #081426;
  --fd-skin-surface: #121c2d;
  --fd-skin-card: #182437;
  --fd-skin-card-soft: #1d2b41;
  --fd-skin-card-lift: #23324a;
  --fd-skin-border: rgba(111, 137, 176, 0.36);
  --fd-skin-border-strong: rgba(94, 134, 255, 0.52);
  --fd-skin-text: #f6f8fc;
  --fd-skin-muted: #9fb0c8;
  --fd-skin-faint: #708199;
  --fd-skin-accent: #0046FF;
  --fd-skin-accent-2: #2f6bff;
  --fd-skin-accent-soft: rgba(0, 70, 255, 0.14);
  --fd-skin-ok: #32d583;
  --fd-skin-warn: #f7c948;
  --fd-skin-danger: #ff7a7a;
  --fd-skin-radius-xl: 22px;
  --fd-skin-radius-lg: 16px;
  --fd-skin-radius-md: 12px;
  --fd-skin-shadow: 0 28px 80px rgba(0, 0, 0, 0.34), 0 1px 0 rgba(255, 255, 255, 0.05) inset;
  --bg: var(--fd-skin-bg);
  --surface: var(--fd-skin-surface);
  --border: var(--fd-skin-border);
  --text: var(--fd-skin-text);
  --muted: var(--fd-skin-muted);
  --accent: var(--fd-skin-accent);
  --ok: var(--fd-skin-ok);
  --warn: var(--fd-skin-warn);
  --danger: var(--fd-skin-danger);
  --vp-card-shadow: var(--fd-skin-shadow);
}
html { background: var(--fd-skin-bg); }
body[data-ba3290-visual-skin="1"] {
  min-height: 100vh;
  background:
    radial-gradient(ellipse 78% 46% at 42% -12%, rgba(0, 70, 255, 0.20), transparent 58%),
    radial-gradient(circle at 84% 14%, rgba(47, 107, 255, 0.12), transparent 28%),
    linear-gradient(180deg, #111827 0%, #08101e 38%, #050a13 100%);
  color: var(--fd-skin-text);
  letter-spacing: -0.01em;
}
body[data-ba3290-visual-skin="1"] .fd-header-hero {
  min-height: 152px;
  padding: 1.75rem clamp(1.35rem, 3.2vw, 2.75rem) 1.85rem;
  border-bottom: 1px solid rgba(113, 134, 168, 0.24);
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.96), rgba(10, 16, 29, 0.90));
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.18);
}
body[data-ba3290-visual-skin="1"] .fd-logo-mark {
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 13px;
  background: linear-gradient(145deg, #1261ff 0%, #0046FF 62%, #0032b8 100%);
  box-shadow: 0 18px 42px rgba(0, 70, 255, 0.34), inset 0 1px 0 rgba(255,255,255,0.24);
}
body[data-ba3290-visual-skin="1"] .fd-header-brand h1 {
  font-size: clamp(1.75rem, 2.7vw, 2.35rem);
  font-weight: 800;
  letter-spacing: -0.055em;
}
body[data-ba3290-visual-skin="1"] .fd-header-sub {
  color: rgba(238, 244, 255, 0.92);
  font-size: 1.04rem;
}
body[data-ba3290-visual-skin="1"] .fd-header-tech,
body[data-ba3290-visual-skin="1"] .muted {
  color: var(--fd-skin-muted);
}
body[data-ba3290-visual-skin="1"] .fd-header-actions {
  gap: 0.7rem 0.8rem;
}
body[data-ba3290-visual-skin="1"] .fd-app-shell {
  max-width: 1690px;
  background:
    linear-gradient(90deg, rgba(0, 70, 255, 0.13) 0, rgba(0, 70, 255, 0.055) 7rem, transparent 22rem),
    linear-gradient(180deg, rgba(7, 14, 27, 0.72), rgba(5, 10, 19, 0));
}
@media (min-width: 960px) {
  body[data-ba3290-visual-skin="1"] .fd-app-shell {
    gap: 1.7rem;
    padding: 0 clamp(1.2rem, 3vw, 2.15rem) 3.5rem;
  }
}
body[data-ba3290-visual-skin="1"] .fd-sidebar {
  padding: 1.35rem 1.15rem 1.2rem;
  border-radius: 0 0 18px 18px;
  border-color: rgba(95, 124, 165, 0.44);
  background:
    linear-gradient(180deg, rgba(4, 18, 39, 0.98), rgba(3, 11, 23, 0.99)),
    var(--fd-skin-shell);
  box-shadow: 16px 0 70px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.045);
}
@media (min-width: 960px) {
  body[data-ba3290-visual-skin="1"] .fd-sidebar {
    width: 280px;
    min-width: 280px;
    border-radius: 18px;
  }
}
body[data-ba3290-visual-skin="1"] .fd-sidebar-logo {
  font-size: 1.06rem;
  font-weight: 850;
}
body[data-ba3290-visual-skin="1"] .fd-sidebar-nav {
  gap: 0.32rem;
  margin-top: 1.05rem;
}
body[data-ba3290-visual-skin="1"] button.fd-sidebar-link {
  min-height: 2.5rem;
  padding: 0.68rem 0.82rem;
  border-radius: 12px;
  color: rgba(238, 244, 255, 0.92);
  font-weight: 700;
  border: 1px solid transparent;
}
body[data-ba3290-visual-skin="1"] button.fd-sidebar-link:hover:not(:disabled),
body[data-ba3290-visual-skin="1"] button.fd-sidebar-link:focus-visible {
  background: linear-gradient(90deg, rgba(0, 70, 255, 0.30), rgba(0, 70, 255, 0.08));
  border-color: rgba(94, 134, 255, 0.44);
  transform: translateX(2px);
}
body[data-ba3290-visual-skin="1"] .fd-sidebar-score,
body[data-ba3290-visual-skin="1"] .fd-vg-brief-card,
body[data-ba3290-visual-skin="1"] .fk-card,
body[data-ba3290-visual-skin="1"] .opp-card,
body[data-ba3290-visual-skin="1"] .exec-scorecard,
body[data-ba3290-visual-skin="1"] .fd-vg-result-card,
body[data-ba3290-visual-skin="1"] details.fd-coll,
body[data-ba3290-visual-skin="1"] .lp-section,
body[data-ba3290-visual-skin="1"] .fp-dry-run-checks {
  border-color: var(--fd-skin-border);
  background: linear-gradient(145deg, rgba(35, 50, 74, 0.90), rgba(16, 26, 42, 0.94));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.045);
}
body[data-ba3290-visual-skin="1"] .fd-dashboard-main {
  padding-top: 1.55rem;
}
body[data-ba3290-visual-skin="1"] .fd-exec-row,
body[data-ba3290-visual-skin="1"] .fd-guided-flow,
body[data-ba3290-visual-skin="1"] .panel,
body[data-ba3290-visual-skin="1"] .panel--fresh-preview,
body[data-ba3290-visual-skin="1"] .fp-cockpit-primary {
  border-radius: var(--fd-skin-radius-xl);
  border: 1px solid var(--fd-skin-border);
  background:
    linear-gradient(160deg, rgba(31, 44, 65, 0.94) 0%, rgba(17, 27, 44, 0.97) 58%, rgba(12, 20, 34, 0.99) 100%);
  box-shadow: var(--fd-skin-shadow);
}
body[data-ba3290-visual-skin="1"] .fd-exec-row {
  padding: 0.85rem;
  margin-bottom: 1.45rem;
}
body[data-ba3290-visual-skin="1"] .fp-exec-strip {
  gap: 0.72rem;
}
body[data-ba3290-visual-skin="1"] .fp-exec-cell {
  min-height: 112px;
  padding: 1rem 1rem 0.95rem;
  border-radius: 15px;
  border-color: rgba(110, 137, 179, 0.34);
  background:
    linear-gradient(155deg, rgba(40, 57, 84, 0.92), rgba(18, 29, 47, 0.96));
}
body[data-ba3290-visual-skin="1"] .fp-exec-label,
body[data-ba3290-visual-skin="1"] .fd-vg-brief-k,
body[data-ba3290-visual-skin="1"] .fp-module-title,
body[data-ba3290-visual-skin="1"] .fd-vg-section-title,
body[data-ba3290-visual-skin="1"] .fk-label,
body[data-ba3290-visual-skin="1"] .fp-next-step-label {
  color: #a9bcda !important;
  letter-spacing: 0.095em !important;
  font-weight: 850 !important;
}
body[data-ba3290-visual-skin="1"] .fp-exec-val,
body[data-ba3290-visual-skin="1"] .fd-vg-brief-v,
body[data-ba3290-visual-skin="1"] .fk-val,
body[data-ba3290-visual-skin="1"] .score {
  color: #ffffff;
  font-weight: 850;
}
body[data-ba3290-visual-skin="1"] .panel {
  padding: clamp(1.15rem, 2.4vw, 1.55rem);
  margin-bottom: 1.55rem;
}
body[data-ba3290-visual-skin="1"] .panel-section-head,
body[data-ba3290-visual-skin="1"] .fp-cockpit-panel-head {
  border-bottom-color: rgba(123, 148, 185, 0.22);
  margin-bottom: 1rem;
}
body[data-ba3290-visual-skin="1"] .panel h2,
body[data-ba3290-visual-skin="1"] .panel-section-head h2,
body[data-ba3290-visual-skin="1"] .fd-guided-flow-head h2 {
  color: #fff;
  font-weight: 850;
  letter-spacing: -0.045em;
}
body[data-ba3290-visual-skin="1"] .fd-vg-operator-brief {
  gap: 0.85rem;
  margin-bottom: 1.05rem;
}
body[data-ba3290-visual-skin="1"] .fd-vg-brief-card {
  min-height: 108px;
  border-radius: 15px;
  padding: 1rem 1.08rem;
}
body[data-ba3290-visual-skin="1"] .fd-vg-pipeline-steps,
body[data-ba3290-visual-skin="1"] .fd-guided-flow-steps {
  border-color: rgba(121, 147, 187, 0.30);
  background: rgba(5, 12, 24, 0.36);
  border-radius: 16px;
}
body[data-ba3290-visual-skin="1"] .fd-vg-step-dot,
body[data-ba3290-visual-skin="1"] .fd-guided-flow-step-num {
  border-color: rgba(94, 134, 255, 0.62);
  background: rgba(0, 70, 255, 0.18);
  color: #d7e4ff;
  font-weight: 850;
}
body[data-ba3290-visual-skin="1"] .fd-guided-flow-step {
  border-color: rgba(105, 130, 169, 0.34);
  background: rgba(16, 26, 42, 0.68);
  border-radius: 13px;
}
body[data-ba3290-visual-skin="1"] .fd-guided-flow-next,
body[data-ba3290-visual-skin="1"] .fp-next-step-box,
body[data-ba3290-visual-skin="1"] .nba-card {
  border-color: rgba(94, 134, 255, 0.44);
  background: linear-gradient(145deg, rgba(0, 70, 255, 0.18), rgba(17, 29, 55, 0.92));
  border-radius: 15px;
}
body[data-ba3290-visual-skin="1"] .vp-status-pill,
body[data-ba3290-visual-skin="1"] .fd-vg-badge,
body[data-ba3290-visual-skin="1"] .fd-guided-step-badge,
body[data-ba3290-visual-skin="1"] .strat-badge {
  border-radius: 999px;
  border-color: rgba(105, 130, 169, 0.40);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.055);
}
body[data-ba3290-visual-skin="1"] .vp-status-pill--ok,
body[data-ba3290-visual-skin="1"] .fd-vg-badge--ok,
body[data-ba3290-visual-skin="1"] .fd-guided-step-badge--done {
  border-color: rgba(50, 213, 131, 0.48);
  background: rgba(50, 213, 131, 0.12);
  color: #c7f9dd;
}
body[data-ba3290-visual-skin="1"] .vp-status-pill--pipeline,
body[data-ba3290-visual-skin="1"] .fd-vg-badge--neutral,
body[data-ba3290-visual-skin="1"] .fd-guided-step-badge--active {
  border-color: rgba(94, 134, 255, 0.48);
  background: rgba(0, 70, 255, 0.12);
  color: #cfe0ff;
}
body[data-ba3290-visual-skin="1"] button,
body[data-ba3290-visual-skin="1"] a.fp-open-artifact {
  border-radius: 11px;
  border-color: rgba(109, 134, 171, 0.42);
  background: rgba(22, 34, 53, 0.94);
  color: #edf4ff;
  font-weight: 700;
  transition: transform 0.12s ease, border-color 0.12s ease, background 0.12s ease, box-shadow 0.12s ease;
}
body[data-ba3290-visual-skin="1"] button:hover:not(:disabled),
body[data-ba3290-visual-skin="1"] a.fp-open-artifact:hover {
  border-color: rgba(94, 134, 255, 0.65);
  background: rgba(31, 48, 74, 0.98);
  transform: translateY(-1px);
}
body[data-ba3290-visual-skin="1"] button.primary,
body[data-ba3290-visual-skin="1"] button.fd-header-cta.primary,
body[data-ba3290-visual-skin="1"] .fp-btn-dry-run.primary {
  background: linear-gradient(180deg, #2f6bff 0%, #0046FF 100%);
  border-color: rgba(126, 164, 255, 0.62);
  color: #fff;
  box-shadow: 0 14px 36px rgba(0, 70, 255, 0.30), inset 0 1px 0 rgba(255,255,255,0.22);
}
body[data-ba3290-visual-skin="1"] .fd-btn-dashboard-reset {
  border-color: rgba(255, 122, 122, 0.42);
  background: rgba(255, 122, 122, 0.10);
  color: #ffd4d4;
}
body[data-ba3290-visual-skin="1"] input[type="text"],
body[data-ba3290-visual-skin="1"] input[type="number"],
body[data-ba3290-visual-skin="1"] input[type="url"],
body[data-ba3290-visual-skin="1"] input[type="password"],
body[data-ba3290-visual-skin="1"] textarea,
body[data-ba3290-visual-skin="1"] select {
  min-height: 2.75rem;
  border-radius: 12px;
  border-color: rgba(112, 142, 184, 0.52);
  background: rgba(5, 12, 24, 0.72);
  color: #f6f8fc;
}
body[data-ba3290-visual-skin="1"] input:focus,
body[data-ba3290-visual-skin="1"] textarea:focus,
body[data-ba3290-visual-skin="1"] select:focus {
  border-color: rgba(47, 107, 255, 0.98);
  box-shadow: 0 0 0 4px rgba(0, 70, 255, 0.18), 0 10px 28px rgba(0, 0, 0, 0.22);
}
body[data-ba3290-visual-skin="1"] pre.out,
body[data-ba3290-visual-skin="1"] .fp-path-value,
body[data-ba3290-visual-skin="1"] .script-box {
  border: 1px solid rgba(106, 132, 168, 0.34);
  border-radius: 13px;
  background: rgba(4, 10, 20, 0.70);
  color: #dbe7fb;
}
body[data-ba3290-visual-skin="1"] .fd-vg-kv,
body[data-ba3290-visual-skin="1"] .fd-vg-list,
body[data-ba3290-visual-skin="1"] .esc-cell {
  border-color: rgba(106, 132, 168, 0.32);
  background: rgba(5, 12, 24, 0.42);
  border-radius: 13px;
}
body[data-ba3290-visual-skin="1"] .founder-kpi-grid {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.85rem;
}
body[data-ba3290-visual-skin="1"] .fk-card {
  min-height: 92px;
  padding: 0.85rem 0.95rem;
}
body[data-ba3290-visual-skin="1"] .opp-grid {
  gap: 0.9rem;
}
@media (max-width: 760px) {
  body[data-ba3290-visual-skin="1"] .fd-header-hero,
  body[data-ba3290-visual-skin="1"] .fd-header-actions,
  body[data-ba3290-visual-skin="1"] .fd-header-reset-wrap {
    align-items: stretch;
  }
  body[data-ba3290-visual-skin="1"] .fd-header-actions > * {
    width: 100%;
    justify-content: center;
  }
}

</style>
</head>
<body data-ba3290-visual-skin="1">
  <header class="fd-header-hero" id="fd-overview-anchor">
    <div class="fd-header-brand">
      <div class="fd-logo-mark" aria-hidden="true">▶</div>
      <div>
        <h1>VideoPipe Founder Cockpit</h1>
        <p class="fd-header-sub">Starte und prüfe Vorschau-Prüfläufe aus einem ruhigen Operator-Cockpit.</p>
        <p class="fd-header-tech">Lokaler Stand · Struktur-Test ohne Live-Provider · read-only</p>
      </div>
    </div>
    <div class="fd-header-actions">
      <span class="vp-status-pill vp-status-pill--ok" title="Lokaler Produktions- und Preview-Pfad vorbereitet">Production Ready</span>
      <span class="vp-status-pill vp-status-pill--pipeline" title="Lokale Preview-Pipeline ohne externe Provider-Calls">Local Preview Pipeline</span>
      <div class="fd-header-reset-wrap" data-ba323b-dashboard-reset-wrap="1">
        <button type="button" class="sm fd-btn-dashboard-reset" id="fd-btn-dashboard-reset" data-ba323b-dashboard-reset="1">Dashboard zurücksetzen</button>
        <p class="fd-reset-hint muted" style="margin:0.35rem 0 0;font-size:0.72rem;max-width:22rem;line-height:1.35">Setzt nur die Ansicht zurück. Dateien im output-Ordner bleiben erhalten.</p>
      </div>
      <button type="button" class="primary fd-header-cta" id="fd-header-cta-local-preview" data-ba306-header-cta="1">Zum Vorschau-Panel</button>
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
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="panel-ba323-video-generate">Video generieren</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="fd-video-generate-result">Ergebnis prüfen</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="panel-ba303-fresh-preview">Vorschau-Prüflauf</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="fp-btn-refresh">Status aktualisieren / Readiness</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="fp-dry-run-handoff">Befehl kopieren</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="panel-ba22-local-preview">Local Preview</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="founder-strategic-summary">Founder Summary</button>
      <button type="button" class="fd-sidebar-link" data-fd-nav-scroll="coll-legacy-debug">Legacy / Debug</button>
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
      <p class="fd-sidebar-score-footnote">Score aus dem Readiness-Check des Vorschau-Prüflaufs</p>
    </div>
  </aside>
  <div class="fd-main-column">
<main class="fd-dashboard-main">
  <div id="error-bar" role="alert"></div>

  <div class="fd-exec-row" data-ba306b-exec-row="1">
    <div class="fp-exec-strip" id="fp-exec-strip" data-ba306-exec-strip="1" aria-label="Executive Kurzüberblick Vorschau">
      <div class="fp-exec-cell"><div class="fp-exec-label">Vorschau-Status</div><div class="fp-exec-val" id="fp-exec-fresh-status">Warte auf Daten …</div><div class="fp-exec-hint" id="fp-exec-hint-fresh"></div></div>
      <div class="fp-exec-cell"><div class="fp-exec-label">Readiness Score</div><div class="fp-exec-readiness-body"><div class="fp-exec-mini-gauge fd-score-gauge fd-score-gauge--small" aria-hidden="true"><div class="fd-score-gauge-ring fd-score-gauge-ring--neutral" id="fp-exec-readiness-ring" style="--fd-sg-pct: 0"><div class="fd-score-gauge-inner"></div></div></div><div class="fp-exec-readiness-copy"><div class="fp-exec-val" id="fp-exec-readiness-score">Nicht bewertet</div><div class="fp-exec-hint" id="fp-exec-hint-score">Wird nach „Status aktualisieren“ berechnet</div></div></div></div>
      <div class="fp-exec-cell"><div class="fp-exec-label">Letzter Lauf</div><div class="fp-exec-val" id="fp-exec-latest-run">Noch kein Run</div><div class="fp-exec-hint" id="fp-exec-hint-run"></div></div>
      <div class="fp-exec-cell"><div class="fp-exec-label">Nächster Schritt</div><div class="fp-exec-val" id="fp-exec-next-step-short">Gib eine URL ein und starte Video generieren.</div><div class="fp-exec-hint" id="fp-exec-hint-next"></div><button type="button" class="sm fp-exec-next-btn" id="fp-exec-next-step-btn" data-fd-exec-next-target="fd-video-generate-url">Zum nächsten Schritt</button></div>
    </div>
  </div>

  <section class="fd-guided-flow" id="fd-guided-production-flow" data-ba311-guided-flow="1" aria-labelledby="fd-guided-flow-h">
    <div class="fd-guided-flow-head">
      <h2 id="fd-guided-flow-h">Production Flow</h2>
      <p class="fd-guided-flow-sub">Geführter Ablauf vom Input bis zum Final Render</p>
    </div>
    <p class="fd-guided-flow-microcopy-help muted" id="fd-guided-flow-microcopy-help"><strong>Status aktualisieren</strong> liest den aktuellen Projektstand aus dem Ordner <code class="fp-inline-path">output/</code> neu ein. Nutze das nach einem lokalen Vorschau-Prüflauf im Terminal.</p>
    <div id="fd-guided-flow-steps" class="fd-guided-flow-steps" aria-label="Produktionsschritte"></div>
    <div class="fd-guided-flow-next">
      <div class="fd-guided-flow-next-kicker">Nächster Schritt</div>
      <div id="fd-guided-flow-next-label" class="fd-guided-flow-next-label"></div>
      <p id="fd-guided-flow-next-action" class="fd-guided-flow-next-action">—</p>
    </div>
  </section>

  <section class="panel panel--video-generate" id="panel-ba323-video-generate" data-ba323-video-generate="1" aria-labelledby="vg-video-generate-h">
    <div class="panel-section-head">
      <h2 id="vg-video-generate-h">Video generieren</h2>
      <p class="panel-section-desc muted">URL eingeben und einen kontrollierten 10-Minuten-Produktionslauf starten.</p>
    </div>
    <div class="fd-vg-operator-brief" aria-label="Operator-Kurzüberblick Video Generate">
      <div class="fd-vg-brief-card">
        <span class="fd-vg-brief-k">Current production state</span>
        <span class="fd-vg-brief-v">Kontrollierter URL → Longform-Render bis <code class="fp-inline-path">final_video.mp4</code>.</span>
      </div>
      <div class="fd-vg-brief-card">
        <span class="fd-vg-brief-k">Next operator step</span>
        <span class="fd-vg-brief-v">URL eintragen, Kosten bewusst bestätigen und danach Ergebnis, Pfade und Warnungen prüfen.</span>
      </div>
      <div class="fd-vg-brief-card">
        <span class="fd-vg-brief-k">Safety mode</span>
        <span class="fd-vg-brief-v">Ohne Aktivierung wird eine Fallback-Preview mit Platzhaltern erstellt; Live-Motion blockt ohne echten Connector.</span>
      </div>
    </div>
    <div class="fd-vg-pipeline-steps" aria-label="Video Generate Produktionsgates">
      <div class="fd-vg-step"><span class="fd-vg-step-dot">1</span><span>Input</span></div>
      <div class="fd-vg-step"><span class="fd-vg-step-dot">2</span><span>Script</span></div>
      <div class="fd-vg-step"><span class="fd-vg-step-dot">3</span><span>Assets</span></div>
      <div class="fd-vg-step"><span class="fd-vg-step-dot">4</span><span>Motion</span></div>
      <div class="fd-vg-step"><span class="fd-vg-step-dot">5</span><span>Preview</span></div>
      <div class="fd-vg-step fd-vg-step--warn"><span class="fd-vg-step-dot">6</span><span>Review / Render</span></div>
    </div>
    <div id="fd-video-generate-form" class="fp-dry-run-grid" data-ba323-video-generate="1">
      <div style="grid-column:1/-1">
        <label for="fd-video-generate-url">URL</label>
        <input type="url" id="fd-video-generate-url" name="url" placeholder="https://…" autocomplete="off" inputmode="url"/>
      </div>
      <div>
        <label for="fd-vg-duration">Dauer (Sekunden)</label>
        <input type="number" id="fd-vg-duration" min="60" max="1800" value="600"/>
      </div>
      <div style="grid-column:1/-1">
        <label for="fd-vg-image-provider">Image-Provider Override (optional, BA 32.72)</label>
        <select id="fd-vg-image-provider">
          <option value="">— Server-Default (IMAGE_PROVIDER) —</option>
          <option value="leonardo">leonardo</option>
          <option value="openai_image">openai_image</option>
          <option value="gemini_image">gemini_image</option>
          <option value="placeholder">placeholder</option>
        </select>
      </div>
      <p class="fd-vg-primary-note"><strong>Standardwerte reichen für normale Tests.</strong><br/>Advanced nur ändern, wenn du bewusst Provider-Kosten/Renderlast steuerst.</p>
      <div style="grid-column:1/-1">
        <label for="fd-vg-voice-mode">Voice-Modus</label>
        <select id="fd-vg-voice-mode">
          <option value="dummy">Dummy Voice / Testmodus</option>
          <option value="none">Keine Voice</option>
          <option value="elevenlabs">ElevenLabs</option>
          <option value="openai">OpenAI TTS</option>
        </select>
        <p class="muted" id="fd-vg-voice-mode-hint" style="margin:0.25rem 0 0;font-size:0.78rem">Dummy Voice aktiv – geeignet für Tests.</p>
      </div>
      <div style="grid-column:1/-1" class="fp-dry-run-checks">
        <label><input type="checkbox" id="fd-vg-live-assets"/> Echte Assets erzeugen</label>
        <label><input type="checkbox" id="fd-vg-live-motion"/> Live-Motion erlauben (Runway — nur mit Connector)</label>
        <label><input type="checkbox" id="fd-vg-confirm-costs"/> Mögliche Provider-Kosten bestätigen</label>
      </div>
      <div style="grid-column:1/-1" class="fp-dry-run-checks" data-ba3278-thumbnail-pack="1">
        <label><input type="checkbox" id="fd-vg-generate-thumbnail-pack"/> Thumbnail Pack erzeugen (BA 32.78)</label>
        <span class="muted" style="font-size:0.78rem;display:block;margin:0.25rem 0 0">Erzeugt nach erfolgreichem Video-Lauf zusätzliche <strong>OpenAI-Bilder</strong> (Kandidaten) und lokale Text-Overlays. Erfordert OpenAI-Key und <strong>Kostenbestätigung</strong>.</span>
      </div>
      <details class="fd-vg-advanced-params" id="fd-vg-advanced-production-params" data-ba3292-video-generate-polish="1">
        <summary>Erweiterte Produktionsparameter</summary>
        <p class="fd-vg-advanced-copy"><strong>Standardwerte reichen für normale Tests.</strong> Advanced nur ändern, wenn du bewusst Provider-Kosten/Renderlast steuerst.</p>
        <div class="fp-dry-run-grid fd-vg-advanced-grid">
          <div>
            <label for="fd-vg-max-scenes">Max. Szenen</label>
            <input type="number" id="fd-vg-max-scenes" min="1" max="80" value="24"/>
          </div>
          <div>
            <label for="fd-vg-max-live">Max. Live-Assets</label>
            <input type="number" id="fd-vg-max-live" min="0" max="80" value="24"/>
          </div>
          <div>
            <label for="fd-vg-motion-every">Motion Clip alle (Sek.)</label>
            <input type="number" id="fd-vg-motion-every" min="15" max="600" value="60"/>
          </div>
          <div>
            <label for="fd-vg-motion-dur">Motion-Clip-Dauer (Sek.)</label>
            <input type="number" id="fd-vg-motion-dur" min="1" max="120" value="10"/>
          </div>
          <div>
            <label for="fd-vg-max-motion">Max. Motion-Clips</label>
            <input type="number" id="fd-vg-max-motion" min="0" max="30" value="10"/>
          </div>
          <div>
            <label for="fd-vg-openai-image-model">OpenAI Bild-Modell (optional)</label>
            <input type="text" id="fd-vg-openai-image-model" placeholder="gpt-image-2" maxlength="128" autocomplete="off"/>
          </div>
          <div>
            <label for="fd-vg-openai-image-size">OpenAI Bildgröße (optional)</label>
            <input type="text" id="fd-vg-openai-image-size" placeholder="1024x1024" maxlength="64" autocomplete="off"/>
          </div>
          <div>
            <label for="fd-vg-openai-image-timeout">OpenAI Timeout (Sek., optional)</label>
            <input type="number" id="fd-vg-openai-image-timeout" min="15" max="600" placeholder="z. B. 120"/>
          </div>
          <div>
            <label for="fd-vg-thumb-cand-count">Thumbnail-Kandidaten (1–3)</label>
            <input type="number" id="fd-vg-thumb-cand-count" min="1" max="3" value="3"/>
          </div>
          <div>
            <label for="fd-vg-thumb-max-out">Max. Overlay-Outputs (1–6)</label>
            <input type="number" id="fd-vg-thumb-max-out" min="1" max="6" value="6"/>
          </div>
          <div>
            <label for="fd-vg-thumb-model">Thumbnail OpenAI-Modell (optional)</label>
            <input type="text" id="fd-vg-thumb-model" placeholder="gpt-image-2" maxlength="128" autocomplete="off"/>
          </div>
          <div>
            <label for="fd-vg-thumb-size">Thumbnail Bildgröße (optional)</label>
            <input type="text" id="fd-vg-thumb-size" placeholder="1024x1024" maxlength="64" autocomplete="off"/>
          </div>
          <div style="grid-column:1/-1">
            <label for="fd-vg-thumb-presets">Style-Presets (optional, kommagetrennt)</label>
            <input type="text" id="fd-vg-thumb-presets" placeholder="impact_youtube, urgent_mystery" maxlength="120" autocomplete="off"/>
          </div>
        </div>
        <details class="muted" style="margin-top:0.65rem" id="fd-vg-dev-keys" data-ba3272b-dev-keys="1">
          <summary><strong>Provider Keys / Local Test (dev-only)</strong> — nur im Request, nie speichern</summary>
          <p class="muted" style="margin:0.35rem 0 0;font-size:0.78rem;line-height:1.35">
            Diese Felder werden <strong>nur</strong> im aktuellen <code>POST /founder/dashboard/video/generate</code> übertragen.
            Es gibt <strong>keine</strong> Speicherung (kein localStorage/sessionStorage), <strong>kein</strong> Echo im Ergebnis-JSON, <strong>kein</strong> OPEN_ME und <strong>keine</strong> Logs.
          </p>
          <div class="fp-dry-run-grid" style="margin-top:0.6rem">
            <div style="grid-column:1/-1">
              <label for="fd-vg-dev-openai-api-key">OPENAI_API_KEY (Request Override)</label>
              <input type="password" id="fd-vg-dev-openai-api-key" placeholder="sk-…" autocomplete="off" spellcheck="false"/>
            </div>
            <div>
              <label for="fd-vg-dev-elevenlabs-api-key">ELEVENLABS_API_KEY (optional)</label>
              <input type="password" id="fd-vg-dev-elevenlabs-api-key" placeholder="…" autocomplete="off" spellcheck="false"/>
            </div>
            <div>
              <label for="fd-vg-dev-runway-api-key">RUNWAY_API_KEY (optional)</label>
              <input type="password" id="fd-vg-dev-runway-api-key" placeholder="…" autocomplete="off" spellcheck="false"/>
            </div>
            <div style="grid-column:1/-1">
              <label for="fd-vg-dev-leonardo-api-key">LEONARDO_API_KEY (optional)</label>
              <input type="password" id="fd-vg-dev-leonardo-api-key" placeholder="…" autocomplete="off" spellcheck="false"/>
            </div>
          </div>
          <p class="muted" id="fd-vg-dev-keys-hint" style="margin:0.35rem 0 0;font-size:0.78rem"></p>
        </details>
      </details>
      <div style="grid-column:1/-1">
        <p class="muted" id="fd-vg-assets-mode-hint" style="margin:0.15rem 0 0;font-size:0.82rem"><strong>Preview/Fallback-Modus</strong> — keine Live-Provider, Platzhalter sind erwartbar.</p>
      </div>
      <div style="grid-column:1/-1">
        <div class="fd-vg-section-title">Readiness Audit · Provider-Readiness</div>
        <div id="fd-vg-provider-readiness" class="fd-vg-kv" aria-label="Provider-Readiness">
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Live Assets</span><span class="fd-vg-v" id="fd-vg-pr-live-assets">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">ElevenLabs Voice</span><span class="fd-vg-v" id="fd-vg-pr-eleven">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">OpenAI TTS</span><span class="fd-vg-v" id="fd-vg-pr-openai">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Runway Motion</span><span class="fd-vg-v" id="fd-vg-pr-runway">Unbekannt</span></div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;margin-top:0.45rem;flex-wrap:wrap">
          <button type="button" class="sm" id="fd-vg-provider-refresh">Status aktualisieren</button>
          <span class="muted" style="font-size:0.78rem">lädt nur Readiness (keine Provider-Calls)</span>
        </div>
        <p class="muted" id="fd-vg-provider-readiness-hint" style="margin:0.35rem 0 0;font-size:0.78rem"></p>

        <div class="fd-vg-section-title">Current Production State · Preflight</div>
        <div class="fd-vg-kv" aria-label="Preflight">
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Status</span><span class="fd-vg-v" id="fd-vg-preflight-status">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Hinweis</span><span class="fd-vg-v" id="fd-vg-preflight-text">—</span></div>
        </div>

        <div class="fd-vg-section-title">Warning / Blocking Reasons · Fix Checklist</div>
        <div id="fd-vg-fix-checklist" class="fd-vg-kv" aria-label="Fix Checklist">
          <div class="fd-vg-kv-row"><span class="fd-vg-k">—</span><span class="fd-vg-v">Noch keine Readiness geladen.</span></div>
        </div>

        <div class="fd-vg-section-title">Next Operator Step · Real Production Smoke</div>
        <p class="muted" style="margin:0 0 0.35rem;font-size:0.78rem">Checkliste für einen echten Lauf mit realen Assets und echter Voice.</p>
        <div style="display:flex;gap:8px;align-items:center;margin:0 0 0.45rem;flex-wrap:wrap">
          <button type="button" class="sm" id="fd-vg-real-smoke-preset">Real Production Smoke Preset</button>
          <span class="muted" style="font-size:0.78rem">setzt Live Assets + bestmögliche Voice (kein Blocker)</span>
        </div>
        <div style="display:flex;gap:8px;align-items:center;margin:0.35rem 0 0;flex-wrap:wrap">
          <button type="button" class="sm" id="fd-vg-openai-image-mini-preset" data-ba372-openai-image-smoke="1">OpenAI gpt-image-2 Mini-Preset</button>
          <span class="muted" style="font-size:0.78rem">BA 32.72 — 1 Szene, 1 Live-Asset, Live + Kostenbestätigung, Voice aus</span>
        </div>
        <p class="muted" id="fd-vg-real-smoke-preset-hint" style="margin:0 0 0.35rem;font-size:0.78rem"></p>
        <details class="muted" style="margin:0.55rem 0 0;font-size:0.78rem" id="fd-vg-leonardo-smoke-details">
          <summary><strong>Real Leonardo Live Smoke</strong> — Operator-Checkliste (manuell, kostenpflichtig)</summary>
          <ul style="margin:0.35rem 0 0;padding-left:1.1rem;line-height:1.45">
            <li><code>LEONARDO_API_KEY</code> in der Runtime gesetzt (niemals Werte im UI/Chat loggen)</li>
            <li>Provider-Readiness: <strong>Live Assets = Bereit</strong></li>
            <li><strong>Echte Assets erzeugen</strong> aktiv</li>
            <li><strong>Mögliche Provider-Kosten bestätigen</strong> aktiv</li>
            <li>Voice-Modus: <strong>Keine Voice</strong> (<code>voice_mode=none</code>) oder Dummy</li>
            <li><strong>Max. Szenen = 1</strong>, <strong>Max. Live-Assets = 1</strong>, optional <strong>Max. Motion-Clips = 0</strong></li>
            <li>Motion: Dashboard sendet <code>motion_mode=basic</code>; für rein statisches Rendering <code>motion_mode=static</code> per API nutzen (siehe Runbook)</li>
          </ul>
          <p style="margin:0.4rem 0 0">Nach dem Lauf: <code>asset_artifact.generation_modes</code> enthält <strong>leonardo_live</strong>; <code>asset_quality_gate.status</code> möglichst <code>production_ready</code> oder <code>mixed_assets</code>; keine Warning <code>leonardo_env_missing_fallback_placeholder</code>. Runbook: <code>docs/runbooks/real_leonardo_live_smoke.md</code></p>
        </details>
        <details class="muted" style="margin:0.55rem 0 0;font-size:0.78rem" id="fd-vg-openai-image-smoke-details" data-ba372-openai-image-smoke="1">
          <summary><strong>Founder OpenAI Image Smoke (BA 32.72)</strong> — Dashboard-Integration mit <code>gpt-image-2</code>, maximal <strong>1 Szene</strong></summary>
          <ul style="margin:0.35rem 0 0;padding-left:1.1rem;line-height:1.45">
            <li><code>OPENAI_API_KEY</code> in der <strong>Server</strong>-Runtime (nicht loggen)</li>
            <li>Optional Request: <code>image_provider=openai_image</code> oder gleichwertig Env <code>IMAGE_PROVIDER=openai_image</code></li>
            <li>Optional: <code>openai_image_model=gpt-image-2</code>, <code>openai_image_size</code>, <code>openai_image_timeout_seconds</code></li>
            <li><strong>Echte Assets erzeugen</strong> + <strong>Kosten bestätigen</strong>; <strong>Max. Szenen = 1</strong>, <strong>Max. Live-Assets = 1</strong></li>
            <li>Empfehlung: <code>raw_text</code> statt URL für stabile Provider-Smokes (siehe Runbook)</li>
          </ul>
          <p style="margin:0.4rem 0 0">Nach dem Lauf: JSON-Feld <code>image_asset_audit</code> und OPEN_ME-Abschnitt <strong>Image Asset Audit</strong>; bei <strong>403</strong> weiterhin <code>openai_image_http_403</code> und <code>openai_image_model_access_denied:</code> plus Modell-Slug in <code>warnings</code>. Runbook: <code>docs/runbooks/real_image_provider_smoke.md</code> (BA 32.72). <strong>Budget:</strong> Live-Bilder sind kostenpflichtig — Mini-Smoke klein halten.</p>
        </details>
        <div id="fd-vg-real-smoke-checklist" class="fd-vg-kv" aria-label="Real Production Smoke">
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Live Assets angefordert</span><span class="fd-vg-v" id="fd-vg-rs-live-assets">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-live-assets-b">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Kosten bestätigt</span><span class="fd-vg-v" id="fd-vg-rs-costs">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-costs-b">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Asset Provider bereit</span><span class="fd-vg-v" id="fd-vg-rs-asset-provider">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-asset-provider-b">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Asset Quality strict/loose</span><span class="fd-vg-v" id="fd-vg-rs-asset-quality">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-asset-quality-b">Nicht verfügbar</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Voice-Modus produktiv gewählt</span><span class="fd-vg-v" id="fd-vg-rs-voice-mode">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-voice-mode-b">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Voice Provider bereit</span><span class="fd-vg-v" id="fd-vg-rs-voice-provider">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-voice-provider-b">Unbekannt</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Timing / Voice Fit</span><span class="fd-vg-v" id="fd-vg-rs-timing">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-timing-b">Nicht verfügbar</span></div>
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Motion optional</span><span class="fd-vg-v" id="fd-vg-rs-motion">—</span><span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-rs-motion-b">Unbekannt</span></div>
        </div>
        <div class="fd-vg-kv" style="margin-top:0.45rem" aria-label="Smoke Empfehlung">
          <div class="fd-vg-kv-row"><span class="fd-vg-k">Empfehlung</span><span class="fd-vg-v" id="fd-vg-rs-reco">Unbekannt</span></div>
        </div>
      </div>
      <div style="grid-column:1/-1" class="fp-dry-run-actions fd-vg-primary-action">
        <button type="button" class="primary fd-vg-main-cta" id="fd-video-generate-submit" data-ba323-video-generate="1">Video generieren</button>
        <button type="button" class="sm" id="fd-video-generate-clear" data-ba323-video-generate="1">Zurücksetzen</button>
      </div>
      <div style="grid-column:1/-1">
        <p class="muted" id="fd-vg-inline-422-hint" style="margin:0.35rem 0 0;font-size:0.78rem"></p>
        <button type="button" class="sm" id="fd-vg-go-confirm-costs" style="display:none;margin-top:0.35rem">Zur Kostenbestätigung</button>
      </div>
    </div>
    <p class="muted" id="fd-video-generate-status" aria-live="polite"></p>
    <div class="fd-vg-result-card" id="fd-vg-last-run-summary" style="display:none;margin-top:0.75rem" aria-live="polite">
      <div class="fd-vg-result-head">
        <div>
          <h3 class="fd-vg-result-title">Letzter gespeicherter Video-Lauf</h3>
          <p class="fd-vg-result-sub">Aus lokalem Browser-Speicher.</p>
        </div>
        <span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-last-run-badge">LOCAL</span>
      </div>
      <div class="fd-vg-kv" id="fd-vg-last-run-kv" aria-label="Letzter gespeicherter Video-Lauf"></div>
      <div style="margin-top:0.55rem;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <button type="button" class="sm" id="fd-vg-forget-last-run">Letzten Lauf vergessen</button>
      </div>
    </div>
    <div class="fd-vg-result-card" id="fd-vg-operator-result" style="display:none" aria-live="polite">
      <div class="fd-vg-result-head">
        <div>
          <h3 class="fd-vg-result-title" id="fd-vg-result-headline">Ergebnis</h3>
          <p class="fd-vg-result-sub" id="fd-vg-result-subline">—</p>
        </div>
        <span class="fd-vg-badge fd-vg-badge--neutral" id="fd-vg-result-badge">OFFEN</span>
      </div>
      <div class="fd-vg-kv" id="fd-vg-result-kv">
        <div class="fd-vg-kv-row"><span class="fd-vg-k">run_id</span><span class="fd-vg-v" id="fd-vg-run-id">—</span></div>
      </div>
      <div id="fd-vg-blockers-wrap" style="display:none">
        <div class="fd-vg-section-title">Blocking Reasons</div>
        <ul class="fd-vg-list" id="fd-vg-blockers"></ul>
      </div>
      <div id="fd-vg-warnings-wrap" style="display:none">
        <div class="fd-vg-section-title">Warnings</div>
        <ul class="fd-vg-list" id="fd-vg-warnings"></ul>
      </div>
      <p class="fd-vg-cta" id="fd-vg-next-cta">—</p>
      <div id="fd-vg-voice-wrap" style="display:none">
        <div class="fd-vg-section-title">Voice Status</div>
        <div id="fd-vg-voice-kv" class="fd-vg-kv" aria-label="Voice Artifact"></div>
      </div>
      <p class="muted" id="fd-vg-smoke-result" style="display:none;margin:0.5rem 0 0;font-size:0.78rem"><strong>Smoke-Ergebnis</strong>: —</p>
      <div id="fd-vg-quality-wrap" style="display:none">
        <div class="fd-vg-section-title">Readiness Audit · Produktions-Check</div>
        <div id="fd-vg-quality-checklist" class="fd-vg-kv" aria-label="Produktions-Checkliste"></div>
      </div>
      <section class="fd-vg-production-timeline" id="fd-vg-production-timeline" data-ba3291-production-timeline="1" aria-labelledby="fd-vg-production-timeline-h" style="display:none">
        <div class="fd-vg-timeline-head">
          <div>
            <h3 class="fd-vg-timeline-title" id="fd-vg-production-timeline-h">Production Timeline</h3>
            <p class="fd-vg-timeline-meta" id="fd-vg-timeline-meta">0:00 bis Ende · Script, Bilder, Motion, Preview und Render.</p>
          </div>
          <span class="fd-vg-timeline-duration" id="fd-vg-timeline-duration">0:00 → —</span>
        </div>
        <div class="fd-vg-timeline-shell" aria-label="Production Timeline Segmente">
          <div class="fd-vg-timeline-scale" id="fd-vg-timeline-scale"></div>
          <div class="fd-vg-timeline-track" id="fd-vg-timeline-track"></div>
        </div>
        <div class="fd-vg-timeline-detail" id="fd-vg-timeline-detail">
          <div class="fd-vg-timeline-detail-card" id="fd-vg-timeline-detail-copy"></div>
          <div class="fd-vg-timeline-preview" id="fd-vg-timeline-preview"></div>
        </div>
      </section>
      <p class="muted" id="fd-vg-fallback-explain" style="display:none;margin:0.35rem 0 0;font-size:0.78rem">Dieser Lauf nutzt Platzhalter/Fallbacks, weil echte Assets, echte Voice oder Motion-Clips fehlen.</p>
      <details class="fd-vg-advanced-artifacts" id="fd-vg-advanced-artifacts">
        <summary>Advanced artifacts & debug details</summary>
        <div id="fd-vg-paths-wrap" style="display:none">
          <div class="fd-vg-section-title">Output Artifacts · Pfade</div>
          <div id="fd-vg-paths" class="fd-vg-kv" aria-label="Video Generate Pfade"></div>
        </div>
        <div id="fd-vg-thumbnail-pack-wrap" style="display:none;margin-top:0.75rem" data-ba3277-thumbnail-pack="1">
          <div class="fd-vg-section-title">Output Artifacts · Thumbnail Pack (BA 32.77)</div>
          <div id="fd-vg-thumbnail-pack-kv" class="fd-vg-kv" aria-label="Thumbnail Pack"></div>
        </div>
        <div id="fd-vg-production-bundle-wrap" style="display:none;margin-top:0.75rem" data-ba3279-production-bundle="1">
          <div class="fd-vg-section-title">Output Artifacts · Production Bundle (BA 32.79)</div>
          <div id="fd-vg-production-bundle-kv" class="fd-vg-kv" aria-label="Production Bundle"></div>
        </div>
        <div class="fd-vg-raw">
          <details id="fd-vg-raw-details">
            <summary>Raw JSON (Debug)</summary>
            <pre class="out out-empty" id="fd-video-generate-result" style="max-height:260px;display:none"></pre>
          </details>
        </div>
      </details>
    </div>
  </section>

  <section class="panel panel--fresh-preview fp-cockpit-primary" id="panel-ba303-fresh-preview" aria-labelledby="fp-snapshot-h">
    <div class="panel-section-head fp-cockpit-panel-head">
      <h2 id="fp-snapshot-h">Vorschau-Prüflauf (BA 30.3–30.8)</h2>
      <p class="panel-section-desc muted">Read-only unter <code class="fp-inline-path">output/fresh_topic_preview/</code> · Ready, Warning oder Blocked auf einen Blick · <strong>Struktur-Test</strong> und <strong>Status aktualisieren</strong> an einem Ort. <em>Vorschau-Prüflauf:</em> erzeugt eine prüfbare Vorschau vor dem finalen Video.</p>
    </div>
    <div class="fp-cockpit-split">
      <div class="fp-cockpit-col fp-cockpit-col--actions">
        <div class="fp-dry-run-card" id="fp-dry-run-panel" data-ba307-dry-run-panel="1" aria-labelledby="fp-dry-run-h">
          <h3 class="subh fp-module-title" id="fp-dry-run-h">Vorschau starten</h3>
          <p class="fp-dry-run-meta">Struktur-Test: prüft, ob Script, Szenen und Assets vorbereitet werden können — ohne Live-Provider und ohne externe Asset-Kosten.</p>
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
            <button type="button" class="primary fp-btn-dry-run" id="fp-btn-start-dry-run" data-label="Struktur-Test starten" data-ba307-start-dry-run="1">Struktur-Test starten</button>
          </div>
          <p class="muted" id="fp-dry-run-status" aria-live="polite"></p>
          <pre class="out out-empty" id="fp-dry-run-result" style="display:none;max-height:180px" data-ba307-dry-run-result="1"></pre>
          <div id="fp-dry-run-handoff" class="fp-dry-run-handoff" style="display:none" data-ba308-handoff="1" aria-labelledby="fp-handoff-heading">
            <h4 class="subh fp-handoff-h" id="fp-handoff-heading">Nächster Schritt: vollen Vorschau-Prüflauf lokal starten (Befehl zum Kopieren)</h4>
            <p class="fp-handoff-note muted" id="fp-handoff-note"></p>
            <p class="fp-handoff-warning" id="fp-handoff-warning"></p>
            <pre class="out" id="fp-dry-run-handoff-ps"></pre>
            <p class="fp-handoff-after muted" id="fp-handoff-after-run">Nach erfolgreichem Lauf: zurück ins Dashboard und <strong>Status aktualisieren</strong> wählen.</p>
            <button type="button" class="sm fp-copy-path" id="fp-btn-copy-handoff-cli" data-ba308-copy-handoff="1">Befehl zum Kopieren</button>
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
            <p class="fd-score-gauge-footnote">Score aus dem Readiness-Check des Vorschau-Prüflaufs</p>
          </div>
          <div class="fp-readiness-row" id="fp-readiness-row" data-ba304-readiness-marker="1">
            <span id="fp-readiness-badge" class="fp-readiness-badge fp-readiness-unknown" title="BA 30.4 Readiness Gate">OFFEN</span>
            <span id="fp-readiness-score" class="fp-readiness-score-wrap">Wird nach „Status aktualisieren“ berechnet</span>
          </div>
          <p class="fp-readiness-footnote muted">Score aus dem Readiness-Check des Vorschau-Prüflaufs</p>
        </div>
        <div class="fp-operator-review-card" id="fp-operator-review-card" data-ba310-operator-review="1" aria-labelledby="fp-operator-review-h">
          <h3 class="subh fp-module-title" id="fp-operator-review-h">Operator Review</h3>
          <div class="fp-review-head">
            <span id="fp-review-decision-badge" class="fp-review-badge fp-review-badge--pending" data-review-decision-marker="pending">Ausstehend</span>
          </div>
          <ul id="fp-review-reasons" class="fp-review-reasons"></ul>
          <p id="fp-review-next-action" class="fp-review-next muted">Nach einem Vorschau-Prüflauf erscheinen hier Hinweise.</p>
        </div>
        <div class="fp-final-render-gate-card" id="fp-final-render-gate" data-ba312-final-render-gate="1" aria-labelledby="fp-final-render-gate-h">
          <h3 class="subh fp-module-title" id="fp-final-render-gate-h">Final Render Preparation</h3>
          <div class="fp-fr-gate-head">
            <span id="fp-final-render-gate-status" class="fp-fr-gate-badge fp-fr-gate-badge--locked" data-final-render-gate-marker="locked">—</span>
          </div>
          <ul id="fp-final-render-gate-reasons" class="fp-fr-gate-reasons"></ul>
          <p id="fp-final-render-next-action" class="fp-fr-gate-next muted">—</p>
          <p class="fp-fr-gate-future-hint">Der sichere Final-Render-Start im Dashboard folgt in einer späteren BA.</p>
        </div>
        <div class="fp-fr-input-checklist-card" id="fp-final-render-input-checklist" data-ba313-final-render-input-checklist="1" aria-labelledby="fp-final-render-input-checklist-h">
          <h3 class="subh fp-module-title" id="fp-final-render-input-checklist-h">Final Render Input Checklist</h3>
          <div class="fp-fr-input-head">
            <span id="fp-final-render-input-checklist-status" class="fp-fr-input-badge fp-fr-input-badge--pending" data-fr-input-checklist-marker="pending">—</span>
          </div>
          <div id="fp-final-render-input-items" class="fp-final-render-input-items" aria-label="Render-Input-Positionen"></div>
          <p id="fp-final-render-input-next-action" class="fp-fr-input-next muted">—</p>
        </div>
        <div class="fp-safe-final-handoff-card fp-dry-run-handoff" id="fp-safe-final-render-handoff" data-ba314-safe-final-render-handoff="1" aria-labelledby="fp-safe-fr-h">
          <h3 class="subh fp-module-title fp-handoff-h" id="fp-safe-fr-h">Safe Final Render Handoff</h3>
          <p id="fp-safe-fr-availability" class="fp-fr-input-row-meta">—</p>
          <p id="fp-safe-fr-locked-msg" class="muted" style="display:none">Final Render Handoff ist gesperrt, bis Gate und Input Checklist bereit sind.</p>
          <ul id="fp-safe-fr-reasons" class="fp-fr-gate-reasons" style="display:none"></ul>
          <p id="fp-safe-fr-note" class="fp-handoff-note muted" style="display:none"></p>
          <p id="fp-safe-fr-warning" class="fp-handoff-warning" style="display:none"></p>
          <pre class="out" id="fp-safe-final-render-cli" style="display:none"></pre>
          <button type="button" class="sm fp-copy-path" id="fp-safe-final-render-copy" style="display:none" data-ba314-copy-safe-fr="1">Final-Render-Befehl kopieren</button>
        </div>
        <div class="fp-toolbar">
          <button type="button" class="primary" id="fp-btn-refresh" data-label="Status aktualisieren" data-ba305-refresh="1">Status aktualisieren</button>
        </div>
        <p class="muted" id="fp-snapshot-status" style="margin:0.25rem 0 0.5rem;font-size:0.82rem">Lade Projektstand …</p>
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
        <pre class="out out-empty" id="out-fp-snapshot" style="max-height:200px" data-fp-snapshot-marker="ba303">Noch kein Vorschau-Prüflauf geladen. Starte einen Struktur-Test oder wähle „Status aktualisieren“, um den letzten Stand aus <code class="fp-inline-path">output/</code> einzublenden. <em>Prüfbericht:</em> zeigt, was erzeugt wurde und was als Nächstes zu prüfen ist (Datei OPEN_PREVIEW_SMOKE.md).</pre>
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

  <details class="fd-coll" id="coll-legacy-debug" style="margin-top:1rem">
    <summary>Legacy Source Intake / Debug (BA 11.0)</summary>
    <div class="coll-body">
      <p class="muted">Dieser ältere Bereich bleibt für Debug/alte Pipeline-Pfade erhalten. Für neue Produktionen nutze oben „Video generieren“.</p>
      <section class="panel" id="coll-source-intake" style="margin-top:0.75rem">
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

      <section class="panel" id="coll-full-pipeline" style="margin-top:0.75rem">
        <h2>Run Full Pipeline (BA 11.1)</h2>
        <p class="muted">Orchestrierung: Generate → Export → Preview → Readiness → Optimize → CTR → Founder Summary → Production Bundle (Downloads). Bei Fehler: Schritt rot, Pipeline stoppt. Ende: Session Snapshot speichern.</p>
        <ol id="pipeline-timeline" class="pipe-timeline" aria-label="Pipeline Timeline">
          <li class="pipe-step pending" data-pi="0"><span class="ps-label">1. Generate (Quelle)</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="1"><span class="ps-label">2. Export Package</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="2"><span class="ps-label">3. Storyboard Plan</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="3"><span class="ps-label">4. Storyboard Readiness</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="4"><span class="ps-label">5. Asset Plan</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="5"><span class="ps-label">6. Asset Execution Stub</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="6"><span class="ps-label">7. Preview</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="7"><span class="ps-label">8. Readiness</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="8"><span class="ps-label">9. Optimize</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="9"><span class="ps-label">10. Thumbnail CTR</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="10"><span class="ps-label">11. Founder Summary</span><span class="ps-msg"></span></li>
          <li class="pipe-step pending" data-pi="11"><span class="ps-label">12. Production Bundle</span><span class="ps-msg"></span></li>
        </ol>
        <div class="actions">
          <button type="button" class="primary" id="btn-full-pipeline" data-label="Run Full Pipeline">Run Full Pipeline</button>
        </div>
      </section>
    </div>
  </details>

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
        <button type="button" id="btn-storyboard-plan" data-label="Storyboard erstellen">Storyboard erstellen</button>
        <button type="button" id="btn-storyboard-readiness" data-label="Storyboard prüfen">Storyboard prüfen</button>
        <button type="button" id="btn-asset-generation-plan" data-label="Asset Plan erstellen">Asset Plan erstellen</button>
        <button type="button" id="btn-asset-execution-stub" data-label="Asset Tasks simulieren">Asset Tasks simulieren</button>
        <button type="button" id="btn-openai-image-live" data-label="OpenAI Bild erzeugen">OpenAI Bild erzeugen</button>
        <button type="button" id="btn-elevenlabs-voice-live" data-label="ElevenLabs Voice erzeugen">ElevenLabs Voice erzeugen</button>
        <button type="button" id="btn-preview" data-label="Preview Founder Metrics">Preview Founder Metrics</button>
        <button type="button" id="btn-readiness" data-label="Provider Readiness">Provider Readiness</button>
        <button type="button" id="btn-optimize" data-label="Optimize Provider Prompts">Optimize Provider Prompts</button>
        <button type="button" id="btn-ctr" data-label="Thumbnail CTR">Thumbnail CTR</button>
        <button type="button" id="btn-formats" data-label="Export Formats">Export Formats</button>
      </div>
      <p class="muted" style="margin-top:0.75rem">Batch Template Compare lädt alle IDs aus dem Template-Selector und ruft nacheinander Preview + Readiness auf.</p>
      <div class="row-check" style="margin-top:0.65rem">
        <input type="checkbox" id="storyboard-openai-confirm-costs"/>
        <label for="storyboard-openai-confirm-costs" style="margin:0">OpenAI Image Kosten bestätigen (max. 10 Bilder)</label>
      </div>
      <div class="row-check" style="margin-top:0.35rem">
        <input type="checkbox" id="storyboard-elevenlabs-confirm-costs"/>
        <label for="storyboard-elevenlabs-confirm-costs" style="margin:0">ElevenLabs Voice Kosten bestätigen (max. 10 Voice Tasks)</label>
      </div>
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

  <details class="fd-coll" open id="coll-storyboard">
    <summary>Storyboard Plan</summary>
    <div class="coll-body">
      <div id="storyboard-plan-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem" data-storyboard-plan-panel="1">
        <strong>Storyboard Plan</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Storyboard — zuerst „Storyboard erstellen“.</p>
      </div>
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-storyboard-plan">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-storyboard-plan" data-dlname="storyboard-plan.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-storyboard-plan" data-dlname="storyboard-plan.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-storyboard-plan">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-storyboard-readiness">
    <summary>Storyboard Readiness</summary>
    <div class="coll-body">
      <div id="storyboard-readiness-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem" data-storyboard-readiness-panel="1">
        <strong>Storyboard Readiness</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Prüfung — zuerst „Storyboard prüfen“.</p>
      </div>
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-storyboard-readiness">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-storyboard-readiness" data-dlname="storyboard-readiness.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-storyboard-readiness" data-dlname="storyboard-readiness.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-storyboard-readiness">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-asset-generation-plan">
    <summary>Asset Plan</summary>
    <div class="coll-body">
      <div id="asset-generation-plan-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem" data-asset-generation-plan-panel="1">
        <strong>Asset Plan</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Asset Plan — zuerst „Asset Plan erstellen“.</p>
      </div>
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-asset-generation-plan">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-asset-generation-plan" data-dlname="asset-generation-plan.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-asset-generation-plan" data-dlname="asset-generation-plan.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-asset-generation-plan">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-asset-execution-stub">
    <summary>Asset Execution Stub</summary>
    <div class="coll-body">
      <div id="asset-execution-stub-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem" data-asset-execution-stub-panel="1">
        <strong>Asset Execution Stub</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Simulation — zuerst „Asset Tasks simulieren“.</p>
      </div>
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-asset-execution-stub">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-asset-execution-stub" data-dlname="asset-execution-stub.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-asset-execution-stub" data-dlname="asset-execution-stub.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-asset-execution-stub">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-openai-image-live">
    <summary>OpenAI Image Live</summary>
    <div class="coll-body">
      <div id="openai-image-live-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem" data-openai-image-live-panel="1">
        <strong>OpenAI Image Live</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Live-Bild — Kosten bestätigen und „OpenAI Bild erzeugen“ klicken.</p>
      </div>
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-openai-image-live">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-openai-image-live" data-dlname="openai-image-live.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-openai-image-live" data-dlname="openai-image-live.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-openai-image-live">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
    </div>
  </details>

  <details class="fd-coll" open id="coll-elevenlabs-voice-live">
    <summary>ElevenLabs Voice Live</summary>
    <div class="coll-body">
      <div id="elevenlabs-voice-live-summary" class="panel" style="margin:0 0 0.75rem;padding:0.55rem 0.65rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.88rem" data-elevenlabs-voice-live-panel="1">
        <strong>ElevenLabs Voice Live</strong>
        <p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Live-Voice — Kosten bestätigen und „ElevenLabs Voice erzeugen“ klicken.</p>
      </div>
      <div class="out-toolbar">
        <button type="button" class="sm tb-copy" data-pre="out-elevenlabs-voice-live">Copy</button>
        <button type="button" class="sm tb-json" data-pre="out-elevenlabs-voice-live" data-dlname="elevenlabs-voice-live.json">JSON</button>
        <button type="button" class="sm tb-txt" data-pre="out-elevenlabs-voice-live" data-dlname="elevenlabs-voice-live.txt">TXT</button>
      </div>
      <pre class="out out-empty" id="out-elevenlabs-voice-live">Noch kein Ergebnis. Klicke auf den passenden Action-Button.</pre>
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
  let lastStoryboard = null;
  let lastStoryboardReadiness = null;
  let lastAssetPlan = null;
  let lastAssetExecutionStub = null;
  let lastOpenAIImageLive = null;
  let lastElevenLabsVoiceLive = null;
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

  function clearStoryboardPlanSummary() {
    var box = $("storyboard-plan-summary");
    if (!box) return;
    box.innerHTML = '<strong>Storyboard Plan</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Storyboard — zuerst „Storyboard erstellen“.</p>';
  }

  function renderStoryboardPlanSummary(plan) {
    var box = $("storyboard-plan-summary");
    if (!box || !plan) return;
    var scenes = Array.isArray(plan.scenes) ? plan.scenes : [];
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "Storyboard Plan";
    box.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "muted";
    meta.style.margin = "0.25rem 0 0.55rem";
    meta.style.fontSize = "0.8rem";
    meta.textContent = "Status: " + String(plan.status || "—") + " · Szenen: " + String(scenes.length) + " · Dauer: " + String(plan.total_duration_seconds || 0) + "s";
    box.appendChild(meta);
    scenes.forEach(function(scene) {
      var card = document.createElement("div");
      card.style.borderTop = "1px solid var(--border)";
      card.style.padding = "0.55rem 0 0";
      card.style.margin = "0.55rem 0 0";
      var title = document.createElement("strong");
      title.textContent = "Szene " + String(scene.scene_number || "?") + " · " + String(scene.chapter_title || scene.title || "Ohne Titel");
      card.appendChild(title);
      var rows = [
        ["visual_intent", scene.visual_intent],
        ["voice_text", scene.voice_text],
        ["image_prompt", scene.image_prompt],
        ["video_prompt", scene.video_prompt],
        ["duration_seconds", scene.duration_seconds],
        ["transition", scene.transition],
        ["asset_type", scene.asset_type],
        ["provider_hints", Array.isArray(scene.provider_hints) ? scene.provider_hints.join(", ") : scene.provider_hints]
      ];
      rows.forEach(function(row) {
        var p = document.createElement("p");
        p.style.margin = "0.28rem 0 0";
        p.style.fontSize = "0.78rem";
        p.style.whiteSpace = "pre-wrap";
        p.textContent = row[0] + ": " + String(row[1] == null || row[1] === "" ? "—" : row[1]);
        card.appendChild(p);
      });
      box.appendChild(card);
    });
  }

  function clearStoryboardReadinessSummary() {
    var box = $("storyboard-readiness-summary");
    if (!box) return;
    box.innerHTML = '<strong>Storyboard Readiness</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Prüfung — zuerst „Storyboard prüfen“.</p>';
  }

  function renderStoryboardReadinessSummary(result) {
    var box = $("storyboard-readiness-summary");
    if (!box || !result) return;
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "Storyboard Readiness";
    box.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "muted";
    meta.style.margin = "0.25rem 0 0.55rem";
    meta.style.fontSize = "0.8rem";
    meta.textContent = "Gesamtstatus: " + String(result.overall_status || "—") + " · Score: " + String(result.score != null ? result.score : "—");
    box.appendChild(meta);
    [
      ["Blocker", result.blocking_issues || []],
      ["Warnings", result.warnings || []]
    ].forEach(function(row) {
      var p = document.createElement("p");
      p.style.margin = "0.28rem 0 0";
      p.style.fontSize = "0.78rem";
      var arr = Array.isArray(row[1]) ? row[1] : [];
      p.textContent = row[0] + ": " + (arr.length ? arr.join(", ") : "—");
      box.appendChild(p);
    });
    var rec = document.createElement("p");
    rec.style.margin = "0.45rem 0 0";
    rec.style.fontSize = "0.8rem";
    rec.textContent = "Empfehlung: " + String(result.production_recommendation || "—");
    box.appendChild(rec);
    (result.scene_results || []).forEach(function(scene) {
      var p = document.createElement("p");
      p.style.margin = "0.35rem 0 0";
      p.style.fontSize = "0.78rem";
      p.textContent = "Szene " + String(scene.scene_number || "?") + " · " + String(scene.status || "—") + " · Score " + String(scene.score != null ? scene.score : "—") + " · " + (scene.issues && scene.issues.length ? scene.issues.join(", ") : "OK");
      box.appendChild(p);
    });
  }

  function clearAssetGenerationPlanSummary() {
    var box = $("asset-generation-plan-summary");
    if (!box) return;
    box.innerHTML = '<strong>Asset Plan</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Asset Plan — zuerst „Asset Plan erstellen“.</p>';
  }

  function renderAssetGenerationPlanSummary(plan) {
    var box = $("asset-generation-plan-summary");
    if (!box || !plan) return;
    var tasks = Array.isArray(plan.tasks) ? plan.tasks : [];
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "Asset Plan";
    box.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "muted";
    meta.style.margin = "0.25rem 0 0.55rem";
    meta.style.fontSize = "0.8rem";
    meta.textContent = "Status: " + String(plan.plan_status || "—") + " · Tasks: " + String(plan.total_tasks || tasks.length) + " · Readiness: " + String(plan.readiness_status || "—");
    box.appendChild(meta);
    if (plan.blocking_issues && plan.blocking_issues.length) {
      var b = document.createElement("p");
      b.style.margin = "0.28rem 0 0";
      b.style.fontSize = "0.78rem";
      b.textContent = "Blocker: " + plan.blocking_issues.join(", ");
      box.appendChild(b);
    }
    tasks.forEach(function(task) {
      var card = document.createElement("div");
      card.style.borderTop = "1px solid var(--border)";
      card.style.padding = "0.55rem 0 0";
      card.style.margin = "0.55rem 0 0";
      var title = document.createElement("strong");
      title.textContent = String(task.task_id || "asset_task") + " · Szene " + String(task.scene_number || "—") + " · " + String(task.asset_type || "—");
      card.appendChild(title);
      var prompt = String(task.prompt || "");
      if (prompt.length > 240) prompt = prompt.slice(0, 237).trim() + "...";
      [
        ["provider_hint", task.provider_hint],
        ["prompt", prompt],
        ["output_path", task.output_path],
        ["dependencies", Array.isArray(task.dependencies) ? task.dependencies.join(", ") : task.dependencies],
        ["warnings", Array.isArray(task.warnings) ? task.warnings.join(", ") : task.warnings]
      ].forEach(function(row) {
        var p = document.createElement("p");
        p.style.margin = "0.28rem 0 0";
        p.style.fontSize = "0.78rem";
        p.style.whiteSpace = "pre-wrap";
        p.textContent = row[0] + ": " + String(row[1] == null || row[1] === "" ? "—" : row[1]);
        card.appendChild(p);
      });
      box.appendChild(card);
    });
  }

  function clearAssetExecutionStubSummary() {
    var box = $("asset-execution-stub-summary");
    if (!box) return;
    box.innerHTML = '<strong>Asset Execution Stub</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Simulation — zuerst „Asset Tasks simulieren“.</p>';
  }

  function renderAssetExecutionStubSummary(result) {
    var box = $("asset-execution-stub-summary");
    if (!box || !result) return;
    var rows = Array.isArray(result.task_results) ? result.task_results : [];
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "Asset Execution Stub";
    box.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "muted";
    meta.style.margin = "0.25rem 0 0.55rem";
    meta.style.fontSize = "0.8rem";
    meta.textContent = "Status: " + String(result.execution_status || "—") + " · Provider Calls geschätzt: " + String(result.estimated_provider_calls || 0) + " · Outputs: " + String((result.estimated_outputs || []).length);
    box.appendChild(meta);
    [
      ["Warnings", result.warnings || []],
      ["Blocker", result.blocking_issues || []],
      ["Geplante Outputs", result.estimated_outputs || []]
    ].forEach(function(row) {
      var p = document.createElement("p");
      p.style.margin = "0.28rem 0 0";
      p.style.fontSize = "0.78rem";
      p.textContent = row[0] + ": " + (row[1] && row[1].length ? row[1].join(", ") : "—");
      box.appendChild(p);
    });
    rows.forEach(function(task) {
      var p = document.createElement("p");
      p.style.margin = "0.35rem 0 0";
      p.style.fontSize = "0.78rem";
      p.textContent = String(task.task_id || "task") + " · " + String(task.asset_type || "—") + " · " + String(task.execution_status || "—") + " · " + String(task.planned_output_path || "—");
      box.appendChild(p);
    });
  }

  function clearOpenAIImageLiveSummary() {
    var box = $("openai-image-live-summary");
    if (!box) return;
    box.innerHTML = '<strong>OpenAI Image Live</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch kein Live-Bild — Kosten bestätigen und „OpenAI Bild erzeugen“ klicken.</p>';
  }

  function renderOpenAIImageLiveSummary(result) {
    var box = $("openai-image-live-summary");
    if (!box || !result) return;
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "OpenAI Image Live";
    box.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "muted";
    meta.style.margin = "0.25rem 0 0.55rem";
    meta.style.fontSize = "0.8rem";
    meta.textContent = "Status: " + String(result.execution_status || "—") + " · Provider Calls: " + String(result.estimated_provider_calls || 0);
    box.appendChild(meta);
    var outs = result.estimated_outputs || [];
    var out = document.createElement("p");
    out.style.margin = "0.28rem 0 0";
    out.style.fontSize = "0.78rem";
    out.textContent = "Output: " + (outs.length ? outs.join(", ") : "—");
    box.appendChild(out);
    (result.task_results || []).forEach(function(task) {
      var p = document.createElement("p");
      p.style.margin = "0.35rem 0 0";
      p.style.fontSize = "0.78rem";
      var path = String(task.output_path || task.planned_output_path || "—");
      var exists = task.output_exists === true;
      var size = task.file_size_bytes || 0;
      var provider = String(task.provider || task.provider_hint || "—");
      var model = String(task.model || "—");
      p.textContent = String(task.task_id || "task") + " · Szene " + String(task.scene_number || "—") + " · " + String(task.execution_status || "—") + " · " + provider + " · " + model + " · output_path: " + path + (exists ? " · Bilddatei gespeichert" : " · output_exists=false") + (size ? " · file_size_bytes=" + String(size) : "");
      box.appendChild(p);
    });
    if (result.warnings && result.warnings.length) {
      var w = document.createElement("p");
      w.style.margin = "0.35rem 0 0";
      w.style.fontSize = "0.78rem";
      w.textContent = "Warnings / Write failed: " + result.warnings.join(", ");
      box.appendChild(w);
    }
    if (result.blocking_issues && result.blocking_issues.length) {
      var b = document.createElement("p");
      b.style.margin = "0.35rem 0 0";
      b.style.fontSize = "0.78rem";
      b.textContent = "Blocker: " + result.blocking_issues.join(", ");
      box.appendChild(b);
    }
  }

  function clearElevenLabsVoiceLiveSummary() {
    var box = $("elevenlabs-voice-live-summary");
    if (!box) return;
    box.innerHTML = '<strong>ElevenLabs Voice Live</strong><p class="muted" style="margin:0.25rem 0 0;font-size:0.8rem">Noch keine Live-Voice — Kosten bestätigen und „ElevenLabs Voice erzeugen“ klicken.</p>';
  }

  function renderElevenLabsVoiceLiveSummary(result) {
    var box = $("elevenlabs-voice-live-summary");
    if (!box || !result) return;
    box.innerHTML = "";
    var head = document.createElement("strong");
    head.textContent = "ElevenLabs Voice Live";
    box.appendChild(head);
    var meta = document.createElement("p");
    meta.className = "muted";
    meta.style.margin = "0.25rem 0 0.55rem";
    meta.style.fontSize = "0.8rem";
    meta.textContent = "Status: " + String(result.execution_status || "—") + " · Provider Calls: " + String(result.estimated_provider_calls || 0);
    box.appendChild(meta);
    (result.task_results || []).forEach(function(task) {
      var p = document.createElement("p");
      p.style.margin = "0.35rem 0 0";
      p.style.fontSize = "0.78rem";
      var path = String(task.output_path || task.planned_output_path || "—");
      var exists = task.output_exists === true;
      var size = task.file_size_bytes || 0;
      p.textContent = String(task.task_id || "task") + " · Szene " + String(task.scene_number || "—") + " · " + String(task.execution_status || "—") + " · ElevenLabs · " + String(task.model || "—") + " · output_path: " + path + (exists ? " · Voice-Datei gespeichert" : " · output_exists=false") + (size ? " · file_size_bytes=" + String(size) : "");
      box.appendChild(p);
    });
    if (result.warnings && result.warnings.length) {
      var w = document.createElement("p");
      w.style.margin = "0.35rem 0 0";
      w.style.fontSize = "0.78rem";
      w.textContent = "Warnings / Voice failed: " + result.warnings.join(", ");
      box.appendChild(w);
    }
    if (result.blocking_issues && result.blocking_issues.length) {
      var b = document.createElement("p");
      b.style.margin = "0.35rem 0 0";
      b.style.fontSize = "0.78rem";
      b.textContent = "Blocker: " + result.blocking_issues.join(", ");
      box.appendChild(b);
    }
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

  function buildStoryboardRequestFromDashboardState() {
    var base = buildCurrentExportRequestFromForm();
    var hookText = "";
    if (lastExport && lastExport.hook && lastExport.hook.hook_text) hookText = lastExport.hook.hook_text;
    if (!hookText) hookText = base.source_summary || base.title || "";
    var scenePrompts = [];
    if (lastExport && lastExport.scene_prompts && Array.isArray(lastExport.scene_prompts.scenes)) {
      scenePrompts = lastExport.scene_prompts.scenes.map(function(s) {
        return String((s && s.positive_expanded) || "");
      }).filter(function(x) { return !!x.trim(); });
    }
    return {
      hook: hookText,
      chapters: base.chapters,
      scene_prompts: scenePrompts,
      video_template: base.video_template,
      voice_style: "dashboard_orchestration"
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
    } else if (kind === "storyboard") {
      if (!Array.isArray(data.scenes)) {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (scenes)");
      }
    } else if (kind === "storyboard_readiness") {
      if (typeof data.score !== "number" || !Array.isArray(data.scene_results)) {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (score/scene_results)");
      }
    } else if (kind === "asset_plan") {
      if (!Array.isArray(data.tasks) || typeof data.total_tasks !== "number") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (tasks)");
      }
    } else if (kind === "asset_execution_stub") {
      if (!Array.isArray(data.task_results) || typeof data.estimated_provider_calls !== "number") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (task_results)");
      }
    } else if (kind === "openai_image_live") {
      if (!Array.isArray(data.task_results) || typeof data.estimated_provider_calls !== "number") {
        throw new Error("Endpoint antwortet leer oder unvollständig: " + endpoint + " (openai image live)");
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
    if (lastStoryboard && lastStoryboard.warnings) addList(lastStoryboard.warnings);
    if (lastStoryboardReadiness) {
      addList(lastStoryboardReadiness.warnings);
      addList(lastStoryboardReadiness.blocking_issues);
    }
    if (lastAssetPlan) {
      addList(lastAssetPlan.warnings);
      addList(lastAssetPlan.blocking_issues);
    }
    if (lastAssetExecutionStub) {
      addList(lastAssetExecutionStub.warnings);
      addList(lastAssetExecutionStub.blocking_issues);
    }
    if (lastOpenAIImageLive) {
      addList(lastOpenAIImageLive.warnings);
      addList(lastOpenAIImageLive.blocking_issues);
    }
    if (lastElevenLabsVoiceLive) {
      addList(lastElevenLabsVoiceLive.warnings);
      addList(lastElevenLabsVoiceLive.blocking_issues);
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
    host.textContent = lines.join("\\n");
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
      lastStoryboard: lastStoryboard,
      lastStoryboardReadiness: lastStoryboardReadiness,
      lastAssetPlan: lastAssetPlan,
      lastAssetExecutionStub: lastAssetExecutionStub,
      lastOpenAIImageLive: lastOpenAIImageLive,
      lastElevenLabsVoiceLive: lastElevenLabsVoiceLive,
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
        lastStoryboard: lastStoryboard,
        lastStoryboardReadiness: lastStoryboardReadiness,
        lastAssetPlan: lastAssetPlan,
        lastAssetExecutionStub: lastAssetExecutionStub,
        lastOpenAIImageLive: lastOpenAIImageLive,
        lastElevenLabsVoiceLive: lastElevenLabsVoiceLive,
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
    lastStoryboard = null;
    lastStoryboardReadiness = null;
    lastAssetPlan = null;
    lastAssetExecutionStub = null;
    lastOpenAIImageLive = null;
    lastElevenLabsVoiceLive = null;
    lastPreview = null;
    lastReadiness = null;
    lastOptimize = null;
    lastCtrPayload = null;
    lastNumericPq = null;
    setOut("out-export-full", null);
    setOut("out-storyboard-plan", null);
    setOut("out-storyboard-readiness", null);
    setOut("out-asset-generation-plan", null);
    setOut("out-asset-execution-stub", null);
    setOut("out-openai-image-live", null);
    setOut("out-elevenlabs-voice-live", null);
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
    clearStoryboardPlanSummary();
    clearStoryboardReadinessSummary();
    clearAssetGenerationPlanSummary();
    clearAssetExecutionStubSummary();
    clearOpenAIImageLiveSummary();
    clearElevenLabsVoiceLiveSummary();
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

  async function runStoryboardOnlyInternal() {
    const body = buildStoryboardRequestFromDashboardState();
    var nc = body.chapters && body.chapters.length ? body.chapters.length : 0;
    setStoryEngineRequestDebug("Storyboard Request gebaut: Template=" + body.video_template + " | Kapitel=" + nc + " | Scene Prompts=" + String((body.scene_prompts || []).length));
    const data = await fetchJson("/story-engine/storyboard-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    assertCompleteStoryResponse("/story-engine/storyboard-plan", data, "storyboard");
    lastStoryboard = data;
    setOut("out-storyboard-plan", data);
    renderStoryboardPlanSummary(data);
    mergeWarnings(data.warnings || []);
    openPanelAndScroll("coll-storyboard", "storyboard-plan-summary");
    return data;
  }

  async function runStoryboardReadinessOnlyInternal() {
    if (!lastStoryboard) {
      await runStoryboardOnlyInternal();
    }
    const data = await fetchJson("/story-engine/storyboard-readiness", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ storyboard_plan: lastStoryboard })
    });
    assertCompleteStoryResponse("/story-engine/storyboard-readiness", data, "storyboard_readiness");
    lastStoryboardReadiness = data;
    setOut("out-storyboard-readiness", data);
    renderStoryboardReadinessSummary(data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    openPanelAndScroll("coll-storyboard-readiness", "storyboard-readiness-summary");
    if (data.overall_status === "blocked") {
      throw new Error(data.production_recommendation || "Storyboard Readiness blockiert.");
    }
    return data;
  }

  async function runAssetGenerationPlanOnlyInternal() {
    if (!lastStoryboard) {
      await runStoryboardOnlyInternal();
    }
    if (!lastStoryboardReadiness) {
      await runStoryboardReadinessOnlyInternal();
    }
    if (lastStoryboardReadiness && lastStoryboardReadiness.overall_status === "blocked") {
      throw new Error(lastStoryboardReadiness.production_recommendation || "Asset Plan blockiert: Storyboard Readiness ist blocked.");
    }
    const data = await fetchJson("/story-engine/asset-generation-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ storyboard_plan: lastStoryboard, readiness_result: lastStoryboardReadiness })
    });
    assertCompleteStoryResponse("/story-engine/asset-generation-plan", data, "asset_plan");
    lastAssetPlan = data;
    setOut("out-asset-generation-plan", data);
    renderAssetGenerationPlanSummary(data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    openPanelAndScroll("coll-asset-generation-plan", "asset-generation-plan-summary");
    if (data.plan_status === "blocked") {
      throw new Error((data.blocking_issues && data.blocking_issues.join(", ")) || "Asset Generation Plan blockiert.");
    }
    return data;
  }

  async function runAssetExecutionStubOnlyInternal() {
    if (!lastAssetPlan) {
      await runAssetGenerationPlanOnlyInternal();
    }
    const data = await fetchJson("/story-engine/asset-execution-stub", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset_generation_plan: lastAssetPlan, dry_run: true })
    });
    assertCompleteStoryResponse("/story-engine/asset-execution-stub", data, "asset_execution_stub");
    lastAssetExecutionStub = data;
    setOut("out-asset-execution-stub", data);
    renderAssetExecutionStubSummary(data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    openPanelAndScroll("coll-asset-execution-stub", "asset-execution-stub-summary");
    if (data.execution_status === "failed") {
      throw new Error((data.blocking_issues && data.blocking_issues.join(", ")) || "Asset Execution Stub fehlgeschlagen.");
    }
    return data;
  }

  async function runOpenAIImageLiveOnlyInternal() {
    if (!lastAssetPlan) {
      await runAssetGenerationPlanOnlyInternal();
    }
    var cb = $("storyboard-openai-confirm-costs");
    var confirmed = !!(cb && cb.checked);
    const data = await fetchJson("/story-engine/openai-image-live-execution", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset_generation_plan: lastAssetPlan,
        confirm_provider_costs: confirmed,
        max_live_image_tasks: 10,
        run_id: "dashboard_storyboard_openai_image",
        output_root: "output",
        openai_image_model: "gpt-image-2",
        openai_image_size: "1024x1024",
        openai_image_timeout_seconds: 120
      })
    });
    assertCompleteStoryResponse("/story-engine/openai-image-live-execution", data, "openai_image_live");
    lastOpenAIImageLive = data;
    setOut("out-openai-image-live", data);
    renderOpenAIImageLiveSummary(data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    openPanelAndScroll("coll-openai-image-live", "openai-image-live-summary");
    if (data.execution_status === "failed") {
      throw new Error((data.blocking_issues && data.blocking_issues.join(", ")) || "OpenAI Image Live fehlgeschlagen.");
    }
    return data;
  }

  async function runElevenLabsVoiceLiveOnlyInternal() {
    if (!lastAssetPlan) {
      await runAssetGenerationPlanOnlyInternal();
    }
    var cb = $("storyboard-elevenlabs-confirm-costs");
    var confirmed = !!(cb && cb.checked);
    const data = await fetchJson("/story-engine/elevenlabs-voice-live-execution", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset_generation_plan: lastAssetPlan,
        confirm_provider_costs: confirmed,
        max_live_voice_tasks: 10,
        run_id: "dashboard_storyboard_elevenlabs_voice",
        output_root: "output",
        elevenlabs_voice_id: "",
        elevenlabs_model_id: "eleven_multilingual_v2",
        elevenlabs_timeout_seconds: 120
      })
    });
    assertCompleteStoryResponse("/story-engine/elevenlabs-voice-live-execution", data, "elevenlabs_voice_live");
    lastElevenLabsVoiceLive = data;
    setOut("out-elevenlabs-voice-live", data);
    renderElevenLabsVoiceLiveSummary(data);
    mergeWarnings(data.warnings || []);
    mergeWarnings(data.blocking_issues || []);
    openPanelAndScroll("coll-elevenlabs-voice-live", "elevenlabs-voice-live-summary");
    if (data.execution_status === "failed") {
      throw new Error((data.blocking_issues && data.blocking_issues.join(", ")) || "ElevenLabs Voice Live fehlgeschlagen.");
    }
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
      await runStoryboardOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 3;
      setPipelineStep(stepIdx, "active", "");
      await runStoryboardReadinessOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 4;
      setPipelineStep(stepIdx, "active", "");
      await runAssetGenerationPlanOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 5;
      setPipelineStep(stepIdx, "active", "");
      await runAssetExecutionStubOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 6;
      setPipelineStep(stepIdx, "active", "");
      await runPreviewOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 7;
      setPipelineStep(stepIdx, "active", "");
      await runReadinessOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 8;
      setPipelineStep(stepIdx, "active", "");
      await runOptimizeOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 9;
      setPipelineStep(stepIdx, "active", "");
      await runCtrOnlyInternal();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 10;
      setPipelineStep(stepIdx, "active", "");
      refreshFounderInterpretation();
      setPipelineStep(stepIdx, "done", "");

      stepIdx = 11;
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
    if (lastStoryboard) {
      setOut("out-storyboard-plan", lastStoryboard);
      renderStoryboardPlanSummary(lastStoryboard);
      mergeWarnings(lastStoryboard.warnings || []);
    } else {
      setOut("out-storyboard-plan", null);
      clearStoryboardPlanSummary();
    }
    if (lastStoryboardReadiness) {
      setOut("out-storyboard-readiness", lastStoryboardReadiness);
      renderStoryboardReadinessSummary(lastStoryboardReadiness);
      mergeWarnings(lastStoryboardReadiness.warnings || []);
      mergeWarnings(lastStoryboardReadiness.blocking_issues || []);
    } else {
      setOut("out-storyboard-readiness", null);
      clearStoryboardReadinessSummary();
    }
    if (lastAssetPlan) {
      setOut("out-asset-generation-plan", lastAssetPlan);
      renderAssetGenerationPlanSummary(lastAssetPlan);
      mergeWarnings(lastAssetPlan.warnings || []);
      mergeWarnings(lastAssetPlan.blocking_issues || []);
    } else {
      setOut("out-asset-generation-plan", null);
      clearAssetGenerationPlanSummary();
    }
    if (lastAssetExecutionStub) {
      setOut("out-asset-execution-stub", lastAssetExecutionStub);
      renderAssetExecutionStubSummary(lastAssetExecutionStub);
      mergeWarnings(lastAssetExecutionStub.warnings || []);
      mergeWarnings(lastAssetExecutionStub.blocking_issues || []);
    } else {
      setOut("out-asset-execution-stub", null);
      clearAssetExecutionStubSummary();
    }
    if (lastOpenAIImageLive) {
      setOut("out-openai-image-live", lastOpenAIImageLive);
      renderOpenAIImageLiveSummary(lastOpenAIImageLive);
      mergeWarnings(lastOpenAIImageLive.warnings || []);
      mergeWarnings(lastOpenAIImageLive.blocking_issues || []);
    } else {
      setOut("out-openai-image-live", null);
      clearOpenAIImageLiveSummary();
    }
    if (lastElevenLabsVoiceLive) {
      setOut("out-elevenlabs-voice-live", lastElevenLabsVoiceLive);
      renderElevenLabsVoiceLiveSummary(lastElevenLabsVoiceLive);
      mergeWarnings(lastElevenLabsVoiceLive.warnings || []);
      mergeWarnings(lastElevenLabsVoiceLive.blocking_issues || []);
    } else {
      setOut("out-elevenlabs-voice-live", null);
      clearElevenLabsVoiceLiveSummary();
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
    return /\\.(md|json|txt)$/.test(s);
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

  function fdClearVideoGenerateForm() {
    var urlEl = document.getElementById("fd-video-generate-url");
    if (urlEl) urlEl.value = "";
    var d = document.getElementById("fd-vg-duration");
    if (d) d.value = "600";
    var ms = document.getElementById("fd-vg-max-scenes");
    if (ms) ms.value = "24";
    var ml = document.getElementById("fd-vg-max-live");
    if (ml) ml.value = "24";
    var me = document.getElementById("fd-vg-motion-every");
    if (me) me.value = "60";
    var md = document.getElementById("fd-vg-motion-dur");
    if (md) md.value = "10";
    var mm = document.getElementById("fd-vg-max-motion");
    if (mm) mm.value = "10";
    var la = document.getElementById("fd-vg-live-assets");
    if (la) la.checked = false;
    var lm = document.getElementById("fd-vg-live-motion");
    if (lm) lm.checked = false;
    var cc = document.getElementById("fd-vg-confirm-costs");
    if (cc) cc.checked = false;
    var st = document.getElementById("fd-video-generate-status");
    if (st) {
      st.textContent = "";
      st.classList.remove("intake-status-err", "intake-status-success");
    }
    fdRenderVideoGenerateOperatorResult(null, "neutral");
    var res = document.getElementById("fd-video-generate-result");
    if (res) {
      res.textContent = "";
      res.style.display = "none";
      res.classList.add("out-empty");
    }
    var btn = document.getElementById("fd-video-generate-submit");
    if (btn) {
      btn.disabled = false;
      btn.classList.remove("is-loading", "is-success", "is-error");
      btn.textContent = "Video generieren";
    }
    fdUpdateVideoGenerateExecutiveState(null, "neutral");
    fdExecSetNextStep("Gib eine URL ein und starte Video generieren.", "fd-video-generate-url", "");
    fdSetGuidedFlowVideoGenerateState("neutral", "Gib eine URL ein und starte Video generieren.");
  }

  function fdVgListFill(listEl, items) {
    if (!listEl) return;
    listEl.innerHTML = "";
    if (!items || !items.length) return;
    items.forEach(function(x) {
      var li = document.createElement("li");
      li.textContent = String(x);
      listEl.appendChild(li);
    });
  }

  function fdVgBuildPathRow(label, pathVal) {
    var wrap = document.createElement("div");
    wrap.className = "fd-vg-kv-row";
    var k = document.createElement("span");
    k.className = "fd-vg-k";
    k.textContent = String(label);
    var v = document.createElement("span");
    v.className = "fd-vg-v";
    var p = String(pathVal || "").trim();
    var short = p;
    if (p && p.length > 90) short = "…" + p.slice(p.length - 90);
    v.textContent = p ? short : "—";
    if (p) v.setAttribute("title", p);
    var isWin = /^[a-zA-Z]:\\\\/.test(p) || /^\\\\\\\\/.test(p);
    var canOpen = /^https?:\\/\\//i.test(p) || p.startsWith("/founder/");
    var openEl = document.createElement("span");
    openEl.className = "muted";
    openEl.style.fontSize = "0.72rem";
    openEl.style.marginLeft = "0.25rem";
    if (p && canOpen) {
      var a = document.createElement("a");
      a.href = p;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.className = "fp-open-artifact";
      a.textContent = "Öffnen";
      openEl = a;
    } else if (p && isWin) {
      openEl.textContent = "lokaler Pfad";
    } else {
      openEl.textContent = "";
      openEl.setAttribute("aria-hidden", "true");
    }
    var b = document.createElement("button");
    b.type = "button";
    b.className = "sm fp-copy-path";
    b.textContent = "Kopieren";
    b.disabled = !p;
    if (p) {
      b.addEventListener("click", function() { fdFpCopyToClipboard(p, b); });
    }
    wrap.appendChild(k);
    wrap.appendChild(v);
    wrap.appendChild(openEl);
    wrap.appendChild(b);
    return wrap;
  }

  function fdVgTimelineFmt(sec) {
    var n = parseFloat(sec);
    if (!isFinite(n) || n < 0) n = 0;
    n = Math.round(n);
    var h = Math.floor(n / 3600);
    var m = Math.floor((n % 3600) / 60);
    var ss = n % 60;
    if (h > 0) return String(h) + ":" + String(m).padStart(2, "0") + ":" + String(ss).padStart(2, "0");
    return String(m) + ":" + String(ss).padStart(2, "0");
  }

  function fdVgTimelineNumberish(v, fallback) {
    var n = parseFloat(v);
    return isFinite(n) ? n : fallback;
  }

  function fdVgTimelineMediaUrl(pathVal) {
    var p = String(pathVal || "").trim();
    if (!p) return "";
    if (new RegExp("^https?://", "i").test(p) || p.indexOf("/founder/") === 0) return p;
    return "";
  }

  function fdVgTimelinePathFromSegment(seg) {
    if (!seg || typeof seg !== "object") return "";
    return String(seg.video_path || seg.preview_path || seg.render_path || seg.image_path || seg.path || "").trim();
  }

  function fdVgTimelineStatus(seg, fallback) {
    var raw = String((seg && (seg.status || seg.state || seg.readiness || seg.generation_mode || seg.mode)) || fallback || "").toLowerCase();
    if (raw.indexOf("fail") >= 0 || raw.indexOf("error") >= 0 || raw.indexOf("blocked") >= 0) return "failed";
    if (raw.indexOf("skip") >= 0) return "skipped";
    if (raw.indexOf("missing") >= 0 || raw.indexOf("absent") >= 0) return "missing";
    if (raw.indexOf("placeholder") >= 0 || raw.indexOf("fallback") >= 0 || raw.indexOf("dummy") >= 0) return "placeholder";
    if (raw.indexOf("ready") >= 0 || raw.indexOf("ok") >= 0 || raw.indexOf("complete") >= 0 || raw.indexOf("rendered") >= 0 || raw.indexOf("live") >= 0) return "ready";
    return String(fallback || "ready");
  }

  function fdVgTimelineSegment(payload, opts) {
    opts = opts || {};
    var start = fdVgTimelineNumberish(opts.start, 0);
    var dur = fdVgTimelineNumberish(opts.duration, 0);
    var end = fdVgTimelineNumberish(opts.end, start + Math.max(0, dur));
    if (!(end > start)) end = start + Math.max(1, dur || 1);
    var type = String(opts.type || "segment").toLowerCase();
    var path = String(opts.path || "").trim();
    var status = fdVgTimelineStatus(opts.raw || {}, opts.status || (path ? "ready" : "missing"));
    return {
      label: String(opts.label || type || "Segment"),
      type: type,
      start: start,
      end: end,
      duration: Math.max(1, end - start),
      status: status,
      path: path,
      media_kind: String(opts.media_kind || (type === "image" ? "image" : (type === "motion" || type === "preview" || type === "render" ? "video" : ""))).toLowerCase(),
      detail: String(opts.detail || ""),
      is_motion: !!opts.is_motion,
      raw: opts.raw || {}
    };
  }

  function fdVgTimelineArraysFromPayload(j) {
    var out = [];
    function add(arr, source) {
      if (Array.isArray(arr) && arr.length) out.push({ source: source, rows: arr });
    }
    if (!j || typeof j !== "object") return out;
    add(j.timeline, "timeline");
    add(j.scenes, "scenes");
    var tm = j.timeline_manifest || j.motion_timeline_manifest || null;
    if (tm && typeof tm === "object") {
      add(tm.segments, "timeline_manifest.segments");
      add(tm.timeline, "timeline_manifest.timeline");
      add(tm.scenes, "timeline_manifest.scenes");
    }
    var rm = j.render_manifest || null;
    if (rm && typeof rm === "object") {
      add(rm.segments, "render_manifest.segments");
      add(rm.timeline, "render_manifest.timeline");
      add(rm.scenes, "render_manifest.scenes");
      add(rm.clips, "render_manifest.clips");
    }
    return out;
  }

  function fdVgBuildProductionTimeline(j) {
    j = j || {};
    var ta = (j.timing_audit && typeof j.timing_audit === "object") ? j.timing_audit : {};
    var ms = (j.motion_strategy && typeof j.motion_strategy === "object") ? j.motion_strategy : {};
    var aa = (j.asset_artifact && typeof j.asset_artifact === "object") ? j.asset_artifact : {};
    var ra = (j.readiness_audit && typeof j.readiness_audit === "object") ? j.readiness_audit : {};
    var duration = fdVgTimelineNumberish(j.duration_target_seconds, 0) || fdVgTimelineNumberish(ta.requested_duration_seconds, 0) || fdVgTimelineNumberish(ta.voice_duration_seconds, 0) || 60;
    var rows = fdVgTimelineArraysFromPayload(j);
    var segments = [];
    if (rows.length) {
      rows[0].rows.forEach(function(row, idx) {
        if (!row || typeof row !== "object") return;
        var st = fdVgTimelineNumberish(row.start_time, fdVgTimelineNumberish(row.start, idx * 5));
        var en = fdVgTimelineNumberish(row.end_time, fdVgTimelineNumberish(row.end, NaN));
        var du = fdVgTimelineNumberish(row.duration_seconds, fdVgTimelineNumberish(row.duration, 5));
        if (!isFinite(en)) en = st + du;
        var mediaPath = fdVgTimelinePathFromSegment(row);
        var mt = String(row.media_type || row.type || (row.video_path ? "motion" : (row.image_path ? "image" : "segment"))).toLowerCase();
        var isMotion = !!(row.video_path || mt.indexOf("motion") >= 0 || mt.indexOf("video") >= 0 || row.motion_clip_playback_seconds != null);
        segments.push(fdVgTimelineSegment(j, {
          label: row.label || row.title || ("Scene " + String(row.scene_number || idx + 1)),
          type: isMotion ? "motion" : (mt.indexOf("image") >= 0 ? "image" : mt),
          start: st,
          end: en,
          duration: du,
          path: mediaPath,
          media_kind: row.video_path ? "video" : (row.image_path ? "image" : ""),
          status: fdVgTimelineStatus(row, mediaPath ? "ready" : "missing"),
          detail: rows[0].source,
          is_motion: isMotion,
          raw: row
        }));
      });
      var maxEnd = segments.reduce(function(mx, x) { return Math.max(mx, x.end || 0); }, 0);
      if (maxEnd > 0) duration = Math.max(duration, maxEnd);
    }
    if (!segments.length) {
      var finalPath = String(j.final_video_path || (j.production_bundle && j.production_bundle.final_video_bundle_path) || "").trim();
      var previewPath = String(j.preview_with_subtitles_path || j.local_preview_video_path || "").trim();
      var scriptReady = !!String(j.script_path || "").trim() || !!ra.script_ready;
      var assetsReady = !!ra.real_assets_ready || !!(aa.real_asset_file_count && parseInt(aa.real_asset_file_count, 10) > 0);
      var placeholders = !!(aa.placeholder_asset_count && parseInt(aa.placeholder_asset_count, 10) > 0) || String((aa.asset_quality_gate || {}).status || "").indexOf("placeholder") >= 0;
      segments.push(fdVgTimelineSegment(j, { label: "Script", type: "script", start: 0, end: duration, status: scriptReady ? "ready" : "missing", path: String(j.script_path || ""), media_kind: "", detail: "Skript-Artefakt" }));
      segments.push(fdVgTimelineSegment(j, { label: "Images", type: "image", start: 0, end: duration, status: assetsReady ? (placeholders ? "placeholder" : "ready") : (placeholders ? "placeholder" : "missing"), path: "", media_kind: "image", detail: "Asset Manifest / Bildstatus" }));
      var planned = fdVgTimelineNumberish(ms.planned_motion_slot_count, fdVgTimelineNumberish(j.motion_slot_count, 0));
      var rendered = fdVgTimelineNumberish(ms.runway_motion_rendered_count, 0);
      var clipEvery = Math.max(15, fdVgTimelineNumberish(ms.motion_clip_every_seconds, 60));
      var clipDur = Math.max(1, fdVgTimelineNumberish(ms.motion_clip_duration_seconds, 10));
      var motionRequested = !!(ms.motion_requested || ra.motion_requested || planned > 0);
      var motionArtifact = j.motion_clip_artifact || {};
      var motionPaths = Array.isArray(motionArtifact.video_clip_paths) ? motionArtifact.video_clip_paths : [];
      if (motionRequested || planned > 0) {
        var slots = Math.max(1, Math.min(12, planned || fdVgTimelineNumberish(ms.max_motion_clips, 1)));
        for (var i = 0; i < slots; i++) {
          var st = Math.min(Math.max(0, i * clipEvery), Math.max(0, duration - clipDur));
          var clipPath = String(motionPaths[i] || "").trim();
          var hasClip = !!clipPath;
          segments.push(fdVgTimelineSegment(j, { label: "Motion " + String(i + 1), type: "motion", start: st, end: Math.min(duration, st + clipDur), status: hasClip ? "ready" : "skipped", path: clipPath, media_kind: hasClip ? "video" : "", detail: hasClip ? "Live-Motion gerendert" : "Motion übersprungen / Fallback auf Bild · motion_requested_but_no_clip_fallback_to_image", is_motion: true }));
        }
      } else {
        segments.push(fdVgTimelineSegment(j, { label: "Motion", type: "motion", start: 0, end: Math.min(duration, 10), status: "skipped", path: "", media_kind: "", detail: "Motion nicht angefordert oder nicht verfügbar", is_motion: true }));
      }
      segments.push(fdVgTimelineSegment(j, { label: "Preview", type: "preview", start: 0, end: duration, status: previewPath ? "ready" : (finalPath ? "skipped" : "missing"), path: previewPath, media_kind: "video", detail: "Vorschau-/Loop-Medium" }));
      segments.push(fdVgTimelineSegment(j, { label: "Render", type: "render", start: 0, end: duration, status: finalPath ? "ready" : (!!j.ok ? "missing" : "failed"), path: finalPath, media_kind: "video", detail: "Finaler Render" }));
    }
    segments.sort(function(a, b) { return (a.start - b.start) || (a.end - b.end) || String(a.label).localeCompare(String(b.label)); });
    return { duration: Math.max(1, duration), segments: segments };
  }

  function fdVgRenderTimelineDetail(seg) {
    var copy = document.getElementById("fd-vg-timeline-detail-copy");
    var prev = document.getElementById("fd-vg-timeline-preview");
    if (!copy || !prev || !seg) return;
    copy.innerHTML = "";
    prev.innerHTML = "";
    var h = document.createElement("h4");
    h.className = "fd-vg-timeline-detail-title";
    h.textContent = seg.label;
    copy.appendChild(h);
    var p = document.createElement("p");
    p.className = "fd-vg-timeline-detail-copy";
    p.textContent = fdVgTimelineFmt(seg.start) + " → " + fdVgTimelineFmt(seg.end) + " · " + seg.type + " · " + seg.status;
    copy.appendChild(p);
    var d = document.createElement("p");
    d.className = "fd-vg-timeline-detail-copy";
    d.textContent = seg.detail || (seg.path ? seg.path : "Kein direkter Medienpfad im aktuellen Ergebnisobjekt.");
    copy.appendChild(d);
    if (seg.path) {
      var pathLine = document.createElement("p");
      pathLine.className = "fd-vg-timeline-detail-copy";
      pathLine.textContent = "Pfad: " + seg.path;
      copy.appendChild(pathLine);
    }
    var url = fdVgTimelineMediaUrl(seg.path);
    if (url && seg.media_kind === "video") {
      var v = document.createElement("video");
      v.controls = true;
      v.loop = true;
      v.muted = true;
      v.playsInline = true;
      v.src = url;
      prev.appendChild(v);
    } else if (url && seg.media_kind === "image") {
      var img = document.createElement("img");
      img.alt = seg.label;
      img.src = url;
      prev.appendChild(img);
    } else {
      var empty = document.createElement("div");
      empty.className = "fd-vg-timeline-media-empty";
      empty.textContent = seg.path ? "Medienpfad vorhanden, aber nicht direkt im Browser abspielbar (lokaler Pfad)." : "Noch kein Medienpfad für dieses Segment vorhanden.";
      prev.appendChild(empty);
    }
  }

  function fdVgRenderProductionTimeline(payload, mode) {
    var host = document.getElementById("fd-vg-production-timeline");
    var track = document.getElementById("fd-vg-timeline-track");
    var scale = document.getElementById("fd-vg-timeline-scale");
    var durEl = document.getElementById("fd-vg-timeline-duration");
    var meta = document.getElementById("fd-vg-timeline-meta");
    if (!host || !track || !scale) return;
    track.innerHTML = "";
    scale.innerHTML = "";
    if (!payload || String(mode || "").toLowerCase() === "neutral") {
      host.style.display = "none";
      return;
    }
    host.style.display = "block";
    var tl = fdVgBuildProductionTimeline(payload);
    var duration = tl.duration || 1;
    if (durEl) durEl.textContent = "0:00 → " + fdVgTimelineFmt(duration);
    var ready = 0, placeholder = 0, missing = 0, skipped = 0, motion = 0;
    (tl.segments || []).forEach(function(seg) {
      if (seg.status === "ready") ready += 1;
      if (seg.status === "placeholder") placeholder += 1;
      if (seg.status === "missing" || seg.status === "failed") missing += 1;
      if (seg.status === "skipped") skipped += 1;
      if (seg.is_motion || seg.type === "motion") motion += 1;
    });
    if (meta) meta.textContent = String((tl.segments || []).length) + " Segmente · " + String(ready) + " ready · " + String(placeholder) + " placeholder · " + String(skipped) + " skipped · " + String(missing) + " missing/failed · " + String(motion) + " Motion";
    [0, duration / 2, duration].forEach(function(t, idx) {
      var sp = document.createElement("span");
      sp.textContent = idx === 0 ? "0:00" : fdVgTimelineFmt(t);
      scale.appendChild(sp);
    });
    var selected = null;
    (tl.segments || []).forEach(function(seg, idx) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "fd-vg-timeline-seg fd-vg-timeline-seg--" + seg.status + ((seg.is_motion || seg.type === "motion") ? " fd-vg-timeline-seg--motion" : "");
      b.style.flex = String(Math.max(0.65, Math.min(3.2, (seg.duration || 1) / Math.max(1, duration) * 8))) + " 0 118px";
      b.setAttribute("data-fd-vg-timeline-segment", String(idx));
      b.innerHTML = '<span class="fd-vg-timeline-seg-label"></span><span class="fd-vg-timeline-seg-time"></span><span class="fd-vg-timeline-seg-type"></span><span class="fd-vg-timeline-status fd-vg-timeline-status--' + seg.status + '"></span>';
      b.querySelector(".fd-vg-timeline-seg-label").textContent = seg.label;
      b.querySelector(".fd-vg-timeline-seg-time").textContent = fdVgTimelineFmt(seg.start) + "–" + fdVgTimelineFmt(seg.end);
      b.querySelector(".fd-vg-timeline-seg-type").textContent = seg.type;
      b.querySelector(".fd-vg-timeline-status").textContent = seg.status;
      b.addEventListener("click", function() {
        Array.prototype.forEach.call(track.querySelectorAll(".fd-vg-timeline-seg"), function(x) { x.classList.remove("is-selected"); });
        b.classList.add("is-selected");
        fdVgRenderTimelineDetail(seg);
      });
      track.appendChild(b);
      if (!selected && (seg.path || seg.is_motion || seg.status === "ready")) selected = { seg: seg, btn: b };
    });
    if (!selected && tl.segments && tl.segments.length) selected = { seg: tl.segments[0], btn: track.querySelector(".fd-vg-timeline-seg") };
    if (selected) {
      if (selected.btn) selected.btn.classList.add("is-selected");
      fdVgRenderTimelineDetail(selected.seg);
    }
  }

  function fdRenderVideoGenerateOperatorResult(payload, mode) {
    var host = document.getElementById("fd-vg-operator-result");
    if (!host) return;
    var badge = document.getElementById("fd-vg-result-badge");
    var h = document.getElementById("fd-vg-result-headline");
    var sub = document.getElementById("fd-vg-result-subline");
    var runIdEl = document.getElementById("fd-vg-run-id");
    var blockersWrap = document.getElementById("fd-vg-blockers-wrap");
    var blockersEl = document.getElementById("fd-vg-blockers");
    var warnsWrap = document.getElementById("fd-vg-warnings-wrap");
    var warnsEl = document.getElementById("fd-vg-warnings");
    var pathsWrap = document.getElementById("fd-vg-paths-wrap");
    var pathsEl = document.getElementById("fd-vg-paths");
    var thumbWrap = document.getElementById("fd-vg-thumbnail-pack-wrap");
    var thumbKv = document.getElementById("fd-vg-thumbnail-pack-kv");
    var bundleWrap = document.getElementById("fd-vg-production-bundle-wrap");
    var bundleKv = document.getElementById("fd-vg-production-bundle-kv");
    var cta = document.getElementById("fd-vg-next-cta");
    var fbExplain = document.getElementById("fd-vg-fallback-explain");
    var vWrap = document.getElementById("fd-vg-voice-wrap");
    var vHost = document.getElementById("fd-vg-voice-kv");
    var smokeEl = document.getElementById("fd-vg-smoke-result");
    var qWrap = document.getElementById("fd-vg-quality-wrap");
    var qHost = document.getElementById("fd-vg-quality-checklist");
    var rawDet = document.getElementById("fd-vg-raw-details");
    var rawPre = document.getElementById("fd-video-generate-result");

    var j = payload || null;
    var st = String(mode || "").toLowerCase();
    var ok = !!(j && j.ok);
    var rid = (j && j.run_id) ? String(j.run_id) : "";
    var blocking = (j && j.blocking_reasons && j.blocking_reasons.length) ? j.blocking_reasons : [];
    var warnings = (j && j.warnings && j.warnings.length) ? j.warnings : [];
    var liveMotionAvailable = !!(j && j.motion_strategy && j.motion_strategy.live_motion_available);

    // default hide lists
    if (blockersWrap) blockersWrap.style.display = "none";
    if (warnsWrap) warnsWrap.style.display = "none";
    if (pathsWrap) pathsWrap.style.display = "none";
    if (pathsEl) pathsEl.innerHTML = "";
    if (thumbWrap) thumbWrap.style.display = "none";
    if (thumbKv) thumbKv.innerHTML = "";
    if (bundleWrap) bundleWrap.style.display = "none";
    if (bundleKv) bundleKv.innerHTML = "";
    if (cta) cta.textContent = "—";
    if (fbExplain) fbExplain.style.display = "none";
    if (vWrap) vWrap.style.display = "none";
    if (vHost) vHost.innerHTML = "";
    if (smokeEl) { smokeEl.style.display = "none"; smokeEl.textContent = "Smoke-Ergebnis: —"; }
    if (qWrap) qWrap.style.display = "none";
    if (qHost) qHost.innerHTML = "";

    if (st === "neutral" || !j) {
      fdVgRenderProductionTimeline(null, "neutral");
      host.style.display = "none";
      if (rawPre) {
        rawPre.textContent = "";
        rawPre.style.display = "none";
        rawPre.classList.add("out-empty");
      }
      if (rawDet) rawDet.open = false;
      return;
    }

    host.style.display = "block";
    if (runIdEl) runIdEl.textContent = rid || "—";

    if (st === "running") {
      if (h) h.textContent = "Video-Generierung läuft …";
      if (sub) sub.textContent = "Bitte warten. Nach Abschluss erscheinen Ergebnis, Pfade und Warnungen hier.";
      if (badge) {
        badge.textContent = "RUNNING";
        badge.className = "fd-vg-badge fd-vg-badge--neutral";
      }
      if (cta) cta.textContent = "Nächster Schritt: Warte auf Abschluss und prüfe danach das Ergebnis.";
      if (rawDet) rawDet.open = false;
      if (rawPre) {
        rawPre.textContent = "";
        rawPre.style.display = "none";
        rawPre.classList.add("out-empty");
      }
      fdVgRenderProductionTimeline(null, "neutral");
      return;
    }

    function _kvRow(hostEl, kText, vText) {
      if (!hostEl) return;
      var row = document.createElement("div");
      row.className = "fd-vg-kv-row";
      var k = document.createElement("span");
      k.className = "fd-vg-k";
      k.textContent = String(kText || "");
      var v = document.createElement("span");
      v.className = "fd-vg-v";
      v.textContent = String(vText || "—");
      row.appendChild(k);
      row.appendChild(v);
      hostEl.appendChild(row);
    }

    // Voice Artifact (best effort)
    try {
      var va = (j && j.voice_artifact) ? j.voice_artifact : null;
      if (vWrap && vHost) {
        vWrap.style.display = "block";
        var reqVm = va && va.requested_voice_mode ? String(va.requested_voice_mode) : (j && j.readiness_audit && j.readiness_audit.requested_voice_mode ? String(j.readiness_audit.requested_voice_mode) : "—");
        var effVm = va && va.effective_voice_mode ? String(va.effective_voice_mode) : (j && j.readiness_audit && j.readiness_audit.effective_voice_mode ? String(j.readiness_audit.effective_voice_mode) : "—");
        _kvRow(vHost, "Modus", reqVm + " → " + effVm);
        var isDummy = !!(va && va.is_dummy);
        var voiceReady = !!(va && va.voice_ready);
        var voicePath = va && va.voice_file_path ? String(va.voice_file_path) : "";
        var dur = (va && va.duration_seconds != null) ? String(va.duration_seconds) : "";
        var statusText = "—";
        if (effVm === "none") statusText = "Keine Voice ausgewählt";
        else if (isDummy) statusText = "Dummy Voice verwendet";
        else if (voiceReady) statusText = "Echte Voice-Datei vorhanden";
        else if (voicePath) statusText = "Voice-Datei fehlt";
        _kvRow(vHost, "Status", statusText);
        if (voicePath) {
          var row = fdVgBuildPathRow("Voice-Datei", voicePath);
          if (row) vHost.appendChild(row);
        }
        if (dur) _kvRow(vHost, "Dauer (Sek.)", dur);
      }
    } catch (eVa) {}

    // Asset Quality (small, operator-friendly)
    try {
      // Keep status strings in bundle for tests + operator hints.
      var FD_VG_ASSET_QUALITY_STATUSES = ["production_ready", "mixed_assets", "placeholder_only", "missing_assets", "unknown"];
      var FD_VG_ASSET_QUALITY_SUMMARY_HINTS = {
        production_ready: "Asset Manifest enthält echte Assets ohne Placeholder.",
        mixed_assets: "Echte Assets vorhanden, aber noch Placeholder im Manifest.",
        placeholder_only: "Nur Placeholder-Assets im Manifest.",
        missing_assets: "Keine Asset-Dateien im Manifest gefunden.",
        unknown: "Asset-Qualität unklar."
      };
      var aa = (j && j.asset_artifact) ? j.asset_artifact : null;
      if (aa && typeof aa === "object") {
        var gate = aa.asset_quality_gate || {};
        var stA = gate && gate.status ? String(gate.status) : "";
        var sumA = gate && gate.summary ? String(gate.summary) : "";
        if (!sumA && FD_VG_ASSET_QUALITY_SUMMARY_HINTS[stA]) sumA = FD_VG_ASSET_QUALITY_SUMMARY_HINTS[stA];
        // Put into warnings box if present, else into voice kv as a minimal carrier.
        if (warnsWrap && warnsEl) {
          var line = "Asset Quality: " + (stA || "unknown") + (sumA ? (" — " + sumA) : "");
          warnsWrap.style.display = "block";
          var extraW = [line].concat(warnings || []);
          fdVgListFill(warnsEl, extraW);
        } else if (vHost) {
          _kvRow(vHost, "Asset Quality", (stA || "unknown") + (sumA ? (" — " + sumA) : ""));
        }
      }
    } catch (eAa) {}

    function _qcRow(label, statusText, detail) {
      if (!qHost) return;
      var row = document.createElement("div");
      row.className = "fd-vg-kv-row";
      var k = document.createElement("span");
      k.className = "fd-vg-k";
      k.textContent = String(label);
      var v = document.createElement("span");
      v.className = "fd-vg-v";
      v.style.fontFamily = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif";
      v.style.fontSize = "0.82rem";
      v.textContent = String(detail || "");
      var badge = document.createElement("span");
      badge.className = "fd-vg-badge " + (statusText === "OK" ? "fd-vg-badge--ok" : (statusText === "Prüfen" ? "fd-vg-badge--fallback" : "fd-vg-badge--neutral"));
      badge.textContent = String(statusText);
      row.appendChild(k);
      row.appendChild(v);
      row.appendChild(badge);
      qHost.appendChild(row);
    }

    // Quality checklist (defensive) — Asset-Gate getrennt von Render-Layer (BA 32.27)
    var joined = fdVgWarnJoinedLower(warnings);
    var hasVoiceFallback = fdVgHasAnySignal(joined, ["dummy", "voice_mode_fallback", "no_elevenlabs_key"]);
    var hasScript = !!(j && j.script_path);
    var hasPack = !!(j && j.scene_asset_pack_path);
    var hasManifest = !!(j && j.asset_manifest_path);
    var hasFinalVideo = !!(j && j.final_video_path);
    var motionFieldPresent = (j && j.motion_strategy && typeof j.motion_strategy.live_motion_available === "boolean");
    var motionOk = motionFieldPresent ? !!j.motion_strategy.live_motion_available : null;
    var raQc = (j && j.readiness_audit && typeof j.readiness_audit === "object") ? j.readiness_audit : {};
    var gateQc = (j && j.asset_artifact && j.asset_artifact.asset_quality_gate && typeof j.asset_artifact.asset_quality_gate === "object")
      ? j.asset_artifact.asset_quality_gate : {};
    var assetStrictQc = !!(raQc.asset_strict_ready || gateQc.strict_ready);
    var gStatusQc = gateQc.status ? String(gateQc.status) : "";
    var hasAaQc = !!(j && j.asset_artifact && typeof j.asset_artifact === "object");
    var assetRowStatus = "Prüfen";
    var assetRowDetail = "Asset-Gate unklar";
    if (assetStrictQc) {
      assetRowStatus = "OK";
      assetRowDetail = "Asset Quality Gate strict_ready (Manifest) — unabhängig von Render-Warnungen";
    } else if (!hasAaQc || !gStatusQc) {
      assetRowStatus = "Prüfen";
      assetRowDetail = "kein vollständiges asset_artifact / Gate";
    } else if (gStatusQc === "mixed_assets" || gStatusQc === "placeholder_only" || gStatusQc === "missing_assets" || gStatusQc === "unknown") {
      assetRowStatus = "Prüfen";
      assetRowDetail = "Asset-Gate: " + gStatusQc;
    } else if (gStatusQc === "production_ready") {
      assetRowStatus = "OK";
      assetRowDetail = "asset_quality_gate production_ready";
    }
    var renderHitQc = fdVgRenderLayerPlaceholderHit(joined, raQc, j);
    var renderRowStatus = "OK";
    var renderRowDetail = "Render-Layer nutzt keine Placeholder-Signale.";
    if (!hasFinalVideo) {
      renderRowStatus = "Nicht verfügbar";
      renderRowDetail = "final_video_path fehlt — keine Renderdaten";
    } else if (renderHitQc) {
      renderRowStatus = "Prüfen";
      renderRowDetail = "Render-Layer nutzt noch Placeholder/Cinematic-Fallback.";
    }

    if (qWrap && qHost) {
      qWrap.style.display = "block";
      _qcRow("Script erstellt", hasScript ? "OK" : "Nicht verfügbar", hasScript ? "script_path vorhanden" : "script_path fehlt");
      _qcRow("Scene Asset Pack erstellt", hasPack ? "OK" : "Nicht verfügbar", hasPack ? "scene_asset_pack_path vorhanden" : "scene_asset_pack_path fehlt");
      _qcRow("Asset Manifest vorhanden", hasManifest ? "OK" : "Nicht verfügbar", hasManifest ? "asset_manifest_path vorhanden" : "asset_manifest_path fehlt");
      _qcRow("Final Video Pfad vorhanden", hasFinalVideo ? "OK" : "Nicht verfügbar", hasFinalVideo ? "final_video_path vorhanden" : "final_video_path fehlt");
      _qcRow("Echte Assets verwendet", assetRowStatus, assetRowDetail);
      _qcRow("Render-Layer", renderRowStatus, renderRowDetail);
      var vq = fdVgVoiceQcRowTuple(j, raQc, hasVoiceFallback);
      _qcRow(vq[0], vq[1], vq[2]);
      if (!motionFieldPresent) _qcRow("Live Motion verfügbar", "Nicht verfügbar", "motion_strategy.live_motion_available fehlt");
      else _qcRow("Live Motion verfügbar", motionOk ? "OK" : "Prüfen", motionOk ? "live_motion_available=true" : "live_motion_available=false");
    }

    if (ok) {
      var warnJoined = "";
      try { warnJoined = joined; } catch (eW2) { warnJoined = ""; }
      var hasFallbackSignal = fdVgIsOkRunFallbackPreview(j, warnJoined);
      var op = j && j.video_generate_operator && typeof j.video_generate_operator === "object" ? j.video_generate_operator : null;

      if (op && op.headline) {
        if (h) h.textContent = String(op.headline || "");
        if (sub) sub.textContent = String(op.subline || "");
        if (badge) {
          badge.textContent = String(op.badge || "Ready");
          var bcls = String(op.badge_class || "ok");
          if (bcls === "bad") badge.className = "fd-vg-badge fd-vg-badge--blocked";
          else if (bcls === "warn") badge.className = "fd-vg-badge fd-vg-badge--fallback";
          else badge.className = "fd-vg-badge fd-vg-badge--ok";
        }
        if (cta) cta.textContent = hasFallbackSignal ? "Nächster Schritt: Provider/Assets prüfen oder Preview öffnen." : "Finales Video prüfen";
        if (fbExplain) fbExplain.style.display = hasFallbackSignal ? "block" : "none";
        if (smokeEl) {
          smokeEl.style.display = "block";
          var slOp = op.smoke_line ? String(op.smoke_line) : "";
          smokeEl.innerHTML = slOp ? ("<strong>Smoke-Ergebnis</strong>: " + slOp) : "<strong>Smoke-Ergebnis</strong>: —";
        }
      } else if (hasFallbackSignal) {
        if (h) h.textContent = "Fallback-Preview erstellt";
        if (sub) {
          if (assetStrictQc || gStatusQc === "production_ready") {
            sub.textContent = "Live Asset erfolgreich, aber Render/Audio nutzt noch Fallbacks.";
          } else {
            sub.textContent = "Der Lauf ist technisch abgeschlossen, aber echte Assets, echte Voice oder Motion-Clips fehlen noch.";
          }
        }
        if (badge) {
          badge.textContent = "Fallback / Preview";
          badge.className = "fd-vg-badge fd-vg-badge--fallback";
        }
        if (cta) cta.textContent = "Nächster Schritt: Provider/Assets prüfen oder Preview öffnen.";
        if (fbExplain) fbExplain.style.display = "block";
        if (smokeEl) { smokeEl.style.display = "block"; smokeEl.innerHTML = "<strong>Smoke-Ergebnis</strong>: Smoke lief, aber Fallbacks wurden genutzt"; }
      } else {
        if (h) h.textContent = "Video-Generierung abgeschlossen";
        var silentOnlyOk = fdVgAudioSilentIsExpectedFallback(j) && warnJoined.indexOf("audio_missing_silent_render") >= 0 && !fdVgWarnTriggersFallbackPreview(j, warnJoined);
        if (sub) {
          sub.textContent = silentOnlyOk
            ? "Keine Voice ausgewählt; Silent Render ist erwartet. Finales Ergebnis prüfen und Preview öffnen."
            : "Finales Ergebnis prüfen und Preview öffnen.";
        }
        if (badge) {
          badge.textContent = "Ready";
          badge.className = "fd-vg-badge fd-vg-badge--ok";
        }
        if (cta) cta.textContent = "Finales Video prüfen";
        if (smokeEl) {
          smokeEl.style.display = "block";
          smokeEl.innerHTML = silentOnlyOk
            ? "<strong>Smoke-Ergebnis</strong>: Smoke erfolgreich; Silent Render erwartet."
            : "<strong>Smoke-Ergebnis</strong>: Real Production Smoke erfolgreich prüfen";
        }
      }

      var motionReqUi = !!(raQc && raQc.motion_requested);
      var allowLiveUi = !!(raQc && raQc.allow_live_motion_requested);
      if (!liveMotionAvailable && (motionReqUi || allowLiveUi)) {
        if (warnsWrap && warnsEl) {
          var extra = ["Keine Live-Motion-Clips verfügbar."].concat(warnings || []);
          warnsWrap.style.display = "block";
          fdVgListFill(warnsEl, extra);
        }
      } else if (warnings && warnings.length && warnsWrap && warnsEl) {
        warnsWrap.style.display = "block";
        fdVgListFill(warnsEl, warnings);
      }
    } else {
      if (h) h.textContent = "Video konnte nicht erzeugt werden";
      if (sub) sub.textContent = "Blocker prüfen und Lauf erneut starten.";
      if (badge) {
        badge.textContent = "BLOCKED";
        badge.className = "fd-vg-badge fd-vg-badge--blocked";
      }
      if (cta) cta.textContent = "Blocker beheben und erneut starten";
      if (smokeEl) { smokeEl.style.display = "block"; smokeEl.innerHTML = "<strong>Smoke-Ergebnis</strong>: Smoke fehlgeschlagen"; }
      if (blocking && blocking.length && blockersWrap && blockersEl) {
        blockersWrap.style.display = "block";
        fdVgListFill(blockersEl, blocking);
      }
      if (warnings && warnings.length && warnsWrap && warnsEl) {
        warnsWrap.style.display = "block";
        fdVgListFill(warnsEl, warnings);
      }
    }

    // Production Timeline (BA 32.91) — client-side from existing result/manifest/artifact fields.
    try { fdVgRenderProductionTimeline(j, st); } catch (eTl) {}

    // Paths (best effort)
    var paths = [];
    var tpPack = null;
    if (j) {
      if (j.final_video_path) paths.push(["Final Video", j.final_video_path]);
      if (j.output_dir) paths.push(["Output-Ordner", j.output_dir]);
      if (j.script_path) paths.push(["Script", j.script_path]);
      if (j.scene_asset_pack_path) paths.push(["Scene Asset Pack", j.scene_asset_pack_path]);
      if (j.asset_manifest_path) paths.push(["Asset Manifest", j.asset_manifest_path]);
      if (j.voice_artifact && j.voice_artifact.voice_file_path) paths.push(["Voice-Datei", j.voice_artifact.voice_file_path]);
      if (j.open_me_report_path) paths.push(["OPEN_ME Ergebnisbericht", j.open_me_report_path]);
      tpPack = (j.thumbnail_pack && typeof j.thumbnail_pack === "object") ? j.thumbnail_pack : null;
      if (tpPack) {
        if (tpPack.thumbnail_recommended_path) paths.push(["Empfohlenes Thumbnail", String(tpPack.thumbnail_recommended_path)]);
        if (tpPack.thumbnail_pack_result_path) paths.push(["Thumbnail Batch Report (JSON)", String(tpPack.thumbnail_pack_result_path)]);
        if (tpPack.thumbnail_pack_path) paths.push(["Thumbnail Pack Ordner", String(tpPack.thumbnail_pack_path)]);
      }
      var pb = (j.production_bundle && typeof j.production_bundle === "object") ? j.production_bundle : null;
      if (pb) {
        if (pb.production_bundle_path) paths.push(["Production Bundle Ordner", String(pb.production_bundle_path)]);
        if (pb.production_bundle_manifest_path) paths.push(["Production Bundle Manifest", String(pb.production_bundle_manifest_path)]);
        if (pb.final_video_bundle_path) paths.push(["Final Video (Bundle)", String(pb.final_video_bundle_path)]);
        if (pb.recommended_thumbnail_bundle_path) paths.push(["Recommended Thumbnail (Bundle)", String(pb.recommended_thumbnail_bundle_path)]);
      }
      var ia = (j.image_asset_audit && typeof j.image_asset_audit === "object") ? j.image_asset_audit : null;
      if (ia) {
        if (ia.effective_image_provider != null && String(ia.effective_image_provider).trim())
          paths.push(["Image Provider (effektiv)", String(ia.effective_image_provider)]);
        if (ia.requested_image_provider != null && String(ia.requested_image_provider).trim())
          paths.push(["Image Provider (angefordert)", String(ia.requested_image_provider)]);
        var ro = ia.openai_image_runner_options;
        if (ro && typeof ro === "object") {
          if (ro.model != null && String(ro.model).trim()) paths.push(["OpenAI Bild-Modell (Runner)", String(ro.model)]);
          if (ro.size != null && String(ro.size).trim()) paths.push(["OpenAI Größe (Runner)", String(ro.size)]);
          if (ro.timeout_seconds != null) paths.push(["OpenAI Timeout Sek. (Runner)", String(ro.timeout_seconds)]);
        }
        if (ia.real_asset_file_count != null) paths.push(["Echte Asset-Dateien (Zähler)", String(ia.real_asset_file_count)]);
        if (ia.asset_manifest_file_count != null) paths.push(["Manifest-Asset-Zeilen", String(ia.asset_manifest_file_count)]);
        try {
          var realN = (ia.real_asset_file_count != null) ? parseInt(String(ia.real_asset_file_count), 10) : NaN;
          var manN = (ia.asset_manifest_file_count != null) ? parseInt(String(ia.asset_manifest_file_count), 10) : NaN;
          if (!isNaN(realN) && !isNaN(manN) && manN > 0 && realN < manN) {
            paths.push([
              "Hinweis",
              "Teilweise Platzhalter, weil Live-Asset-Limit erreicht wurde oder der Provider nicht alle Szenen erzeugt hat."
            ]);
          }
        } catch (eCapHint) {}
      }
    }
    if (paths.length && pathsWrap && pathsEl) {
      pathsWrap.style.display = "block";
      paths.forEach(function(p) { pathsEl.appendChild(fdVgBuildPathRow(p[0], p[1])); });
    }

    try {
      if (tpPack && thumbWrap && thumbKv && st !== "neutral" && st !== "running" && j) {
        thumbKv.innerHTML = "";
        var tstatusTp = tpPack.thumbnail_pack_status != null ? String(tpPack.thumbnail_pack_status) : "—";
        _kvRow(thumbKv, "Thumbnail Pack Status", tstatusTp);
        if (tpPack.thumbnail_generated_count != null) _kvRow(thumbKv, "Generierte Thumbnails", String(tpPack.thumbnail_generated_count));
        if (tpPack.thumbnail_top_score != null) _kvRow(thumbKv, "Top-Score", String(tpPack.thumbnail_top_score));
        if (tpPack.thumbnail_recommended_score != null) _kvRow(thumbKv, "Empfehlungs-Score", String(tpPack.thumbnail_recommended_score));
        var recPTp = tpPack.thumbnail_recommended_path ? String(tpPack.thumbnail_recommended_path) : "";
        if (recPTp) thumbKv.appendChild(fdVgBuildPathRow("Empfohlenes Thumbnail", recPTp));
        var repPTp = tpPack.thumbnail_pack_result_path ? String(tpPack.thumbnail_pack_result_path) : "";
        if (repPTp) thumbKv.appendChild(fdVgBuildPathRow("Thumbnail Batch Report", repPTp));
        var packPTp = tpPack.thumbnail_pack_path ? String(tpPack.thumbnail_pack_path) : "";
        if (packPTp) thumbKv.appendChild(fdVgBuildPathRow("Thumbnail Pack Ordner", packPTp));
        thumbWrap.style.display = "block";
      }
    } catch (eThumb) {}

    try {
      var pbPack = (j && j.production_bundle && typeof j.production_bundle === "object") ? j.production_bundle : null;
      if (pbPack && bundleWrap && bundleKv && st !== "neutral" && st !== "running" && j) {
        bundleKv.innerHTML = "";
        var bst = pbPack.production_bundle_status != null ? String(pbPack.production_bundle_status) : "—";
        _kvRow(bundleKv, "Production Bundle Status", bst);
        var bpDir = pbPack.production_bundle_path ? String(pbPack.production_bundle_path) : "";
        if (bpDir) bundleKv.appendChild(fdVgBuildPathRow("Production Bundle Ordner", bpDir));
        var bmPath = pbPack.production_bundle_manifest_path ? String(pbPack.production_bundle_manifest_path) : "";
        if (bmPath) bundleKv.appendChild(fdVgBuildPathRow("Production Bundle Manifest", bmPath));
        var fvB = pbPack.final_video_bundle_path ? String(pbPack.final_video_bundle_path) : "";
        if (fvB) bundleKv.appendChild(fdVgBuildPathRow("Final Video (Bundle)", fvB));
        var rtB = pbPack.recommended_thumbnail_bundle_path ? String(pbPack.recommended_thumbnail_bundle_path) : "";
        if (rtB) bundleKv.appendChild(fdVgBuildPathRow("Recommended Thumbnail (Bundle)", rtB));
        bundleWrap.style.display = "block";
      }
    } catch (ePb) {}

    // Raw JSON (optional)
    if (rawPre) {
      rawPre.style.display = "block";
      rawPre.classList.remove("out-empty");
      try { rawPre.textContent = JSON.stringify(j, null, 2); } catch (eJ) { rawPre.textContent = String(j); }
    }
  }

  function fdVgDispatchInputChange(el) {
    if (!el || typeof el.dispatchEvent !== "function") return;
    try {
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (eDc) {}
  }

  async function fdSubmitVideoGenerate() {
    var st = document.getElementById("fd-video-generate-status");
    var resEl = document.getElementById("fd-video-generate-result");
    var btn = document.getElementById("fd-video-generate-submit");
    if (!btn) return;
    if (isKillSwitchActive()) {
      if (st) {
        st.textContent = "Kill Switch aktiv — Video-Generierung blockiert.";
        st.classList.add("intake-status-err");
      }
      return;
    }
    var urlEl = document.getElementById("fd-video-generate-url");
    var url = urlEl ? String(urlEl.value || "").trim() : "";
    if (st) {
      st.classList.remove("intake-status-err", "intake-status-success");
    }
    if (!url) {
      if (st) {
        st.textContent = "Bitte eine URL eingeben.";
        st.classList.add("intake-status-err");
      }
      return;
    }
    fdClearDashboardManualResetFlag();
    fdUpdateVideoGenerateExecutiveState(null, "running");
    fdRenderVideoGenerateOperatorResult({ ok: false, run_id: "", blocking_reasons: [], warnings: [] }, "running");
    var dur = parseInt(document.getElementById("fd-vg-duration") && document.getElementById("fd-vg-duration").value, 10);
    var maxSc = parseInt(document.getElementById("fd-vg-max-scenes") && document.getElementById("fd-vg-max-scenes").value, 10);
    var maxLive = parseInt(document.getElementById("fd-vg-max-live") && document.getElementById("fd-vg-max-live").value, 10);
    var motEvery = parseInt(document.getElementById("fd-vg-motion-every") && document.getElementById("fd-vg-motion-every").value, 10);
    var motDur = parseInt(document.getElementById("fd-vg-motion-dur") && document.getElementById("fd-vg-motion-dur").value, 10);
    var maxMot = parseInt(document.getElementById("fd-vg-max-motion") && document.getElementById("fd-vg-max-motion").value, 10);
    if (isNaN(dur) || dur < 60) dur = 600;
    if (isNaN(maxSc) || maxSc < 1) maxSc = 24;
    if (isNaN(maxLive) || maxLive < 0) maxLive = 24;
    if (isNaN(motEvery) || motEvery < 15) motEvery = 60;
    if (isNaN(motDur) || motDur < 1) motDur = 10;
    if (isNaN(maxMot) || maxMot < 0) maxMot = 10;
    var liveAssetsCb = document.getElementById("fd-vg-live-assets");
    var liveMotionCb = document.getElementById("fd-vg-live-motion");
    var confirmCostsCb = document.getElementById("fd-vg-confirm-costs");
    var allowLiveAssets = !!(liveAssetsCb && liveAssetsCb.checked);
    var allowLiveMotion = !!(liveMotionCb && liveMotionCb.checked);
    var confirmCosts = !!(confirmCostsCb && confirmCostsCb.checked);
    var cbThumbPack = document.getElementById("fd-vg-generate-thumbnail-pack");
    var generateThumbPack = !!(cbThumbPack && cbThumbPack.checked);
    var thumbCandEl = document.getElementById("fd-vg-thumb-cand-count");
    var thumbOutEl = document.getElementById("fd-vg-thumb-max-out");
    var thumbModelEl = document.getElementById("fd-vg-thumb-model");
    var thumbSizeEl = document.getElementById("fd-vg-thumb-size");
    var thumbPresetsEl = document.getElementById("fd-vg-thumb-presets");
    var thumbCand = parseInt(thumbCandEl && thumbCandEl.value, 10);
    var thumbMaxOut = parseInt(thumbOutEl && thumbOutEl.value, 10);
    if (isNaN(thumbCand) || thumbCand < 1) thumbCand = 3;
    if (thumbCand > 3) thumbCand = 3;
    if (isNaN(thumbMaxOut) || thumbMaxOut < 1) thumbMaxOut = 6;
    if (thumbMaxOut > 6) thumbMaxOut = 6;
    var thumbModel = thumbModelEl ? String(thumbModelEl.value || "").trim() : "";
    var thumbSize = thumbSizeEl ? String(thumbSizeEl.value || "").trim() : "";
    var thumbPresetsRaw = thumbPresetsEl ? String(thumbPresetsEl.value || "").trim() : "";
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var voiceMode = voiceSel ? String(voiceSel.value || "dummy") : "dummy";
    var imgProvEl = document.getElementById("fd-vg-image-provider");
    var imgProv = imgProvEl ? String(imgProvEl.value || "").trim() : "";
    var oaiModelEl = document.getElementById("fd-vg-openai-image-model");
    var oaiSizeEl = document.getElementById("fd-vg-openai-image-size");
    var oaiToEl = document.getElementById("fd-vg-openai-image-timeout");
    var oaiModel = oaiModelEl ? String(oaiModelEl.value || "").trim() : "";
    var oaiSize = oaiSizeEl ? String(oaiSizeEl.value || "").trim() : "";
    var oaiToRaw = oaiToEl ? String(oaiToEl.value || "").trim() : "";
    var oaiTo = parseFloat(oaiToRaw);
    // BA 32.72b — dev-only key overrides (nur im Request, nie speichern/anzeigen/loggen)
    var devOaiEl = document.getElementById("fd-vg-dev-openai-api-key");
    var devElEl = document.getElementById("fd-vg-dev-elevenlabs-api-key");
    var devRwEl = document.getElementById("fd-vg-dev-runway-api-key");
    var devLeoEl = document.getElementById("fd-vg-dev-leonardo-api-key");
    var devOai = devOaiEl ? String(devOaiEl.value || "").trim() : "";
    var devEl = devElEl ? String(devElEl.value || "").trim() : "";
    var devRw = devRwEl ? String(devRwEl.value || "").trim() : "";
    var devLeo = devLeoEl ? String(devLeoEl.value || "").trim() : "";
    var body = {
      url: url,
      duration_target_seconds: dur,
      max_scenes: maxSc,
      max_live_assets: maxLive,
      motion_clip_every_seconds: motEvery,
      motion_clip_duration_seconds: motDur,
      max_motion_clips: maxMot,
      allow_live_assets: !!allowLiveAssets,
      allow_live_motion: !!allowLiveMotion,
      confirm_provider_costs: !!confirmCosts,
      voice_mode: voiceMode,
      motion_mode: "basic",
      generate_thumbnail_pack: !!generateThumbPack,
      thumbnail_candidate_count: thumbCand,
      thumbnail_max_outputs: thumbMaxOut
    };
    if (generateThumbPack) {
      if (thumbModel) body.thumbnail_model = thumbModel;
      if (thumbSize) body.thumbnail_size = thumbSize;
      if (thumbPresetsRaw) {
        var pp = thumbPresetsRaw.split(",").map(function(x) { return String(x || "").trim(); }).filter(Boolean);
        if (pp.length) body.thumbnail_style_presets = pp;
      }
    }
    if (imgProv) body.image_provider = imgProv;
    if (imgProv === "openai_image") {
      body.openai_image_model = oaiModel || "gpt-image-2";
    } else if (oaiModel) {
      body.openai_image_model = oaiModel;
    }
    if (oaiSize) body.openai_image_size = oaiSize;
    if (!isNaN(oaiTo) && oaiTo >= 15 && oaiTo <= 600) body.openai_image_timeout_seconds = oaiTo;
    if (devOai) body.dev_openai_api_key = devOai;
    if (devEl) body.dev_elevenlabs_api_key = devEl;
    if (devRw) body.dev_runway_api_key = devRw;
    if (devLeo) body.dev_leonardo_api_key = devLeo;
    btn.disabled = true;
    btn.classList.add("is-loading");
    btn.classList.remove("is-success", "is-error");
    btn.textContent = "Generierung läuft…";
    if (resEl) {
      resEl.style.display = "none";
      resEl.textContent = "";
    }
    if (st) st.textContent = "Starte Video-Generierung…";
    try {
      const r = await fetch("/founder/dashboard/video/generate", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body)
      });
      var j = null;
      try { j = await r.json(); } catch (eJ) {}
      if (!r.ok) {
        var det = j && j.detail != null ? j.detail : ("HTTP " + r.status);
        if (st) {
          // Operator-friendly decode for known 422 detail
          if (r.status === 422 && fdVgErrorDetailContains(det, "confirm_provider_costs_required_when_live_flags")) {
            st.textContent = "Kostenbestätigung fehlt: Für Live Assets oder Thumbnail Pack musst du zuerst „Mögliche Provider-Kosten bestätigen“ aktivieren.";
          } else {
            st.textContent = "Video-Generierung: " + String(det);
          }
          st.classList.add("intake-status-err");
        }
        // Inline hint + CTA to checkbox
        if (r.status === 422 && fdVgErrorDetailContains(det, "confirm_provider_costs_required_when_live_flags")) {
          var inline = document.getElementById("fd-vg-inline-422-hint");
          var go = document.getElementById("fd-vg-go-confirm-costs");
          if (inline) inline.textContent = "Kostenbestätigung fehlt: Für Live Assets oder Thumbnail Pack musst du zuerst „Mögliche Provider-Kosten bestätigen“ aktivieren.";
          if (go) go.style.display = "inline-block";
        }
        fdUpdateVideoGenerateExecutiveState(j || null, "done");
        fdRenderVideoGenerateOperatorResult(j || { ok: false, run_id: "", blocking_reasons: [String(det)] }, "done");
        btn.classList.add("is-error");
        btn.textContent = "Video generieren";
        btn.disabled = false;
        btn.classList.remove("is-loading");
        return;
      }
      if (st) {
        st.textContent = (j && j.ok) ? "Fertig — siehe Ergebnis." : "Beendet mit Blockern/Warnungen.";
        st.classList.add((j && j.ok) ? "intake-status-success" : "intake-status-err");
      }
      fdUpdateVideoGenerateExecutiveState(j || null, "done");
      fdRenderVideoGenerateOperatorResult(j || null, "done");
      try { FD_VG_LAST_VIDEO_GENERATE = j || null; } catch (eKeep) {}
      try { fdApplyRealProductionSmokeChecklist(); } catch (eRsAfter) {}
      try { fdVgSaveLastRunSummary(j || null); } catch (eSave) {}
      btn.classList.add((j && j.ok) ? "is-success" : "is-error");
      btn.textContent = "Video generieren";
      btn.disabled = false;
      btn.classList.remove("is-loading");
    } catch (e) {
      if (st) {
        st.textContent = "Video-Generierung: " + String(e && e.message ? e.message : e);
        st.classList.add("intake-status-err");
      }
      fdUpdateVideoGenerateExecutiveState({ ok: false, run_id: "", blocking_reasons: ["fetch_exception"] }, "done");
      fdRenderVideoGenerateOperatorResult({ ok: false, run_id: "", blocking_reasons: ["fetch_exception"], warnings: [] }, "done");
      btn.classList.add("is-error");
      btn.textContent = "Video generieren";
      btn.disabled = false;
      btn.classList.remove("is-loading");
    }
  }

  function fdApplyVideoGenerateAssetsModeHint() {
    var cb = document.getElementById("fd-vg-live-assets");
    var el = document.getElementById("fd-vg-assets-mode-hint");
    if (!el) return;
    var on = !!(cb && cb.checked);
    if (on) {
      el.innerHTML = "<strong>Real-Assets-Modus</strong> — kann Provider-Kosten verursachen; bei fehlender Konfiguration fällt der Lauf auf Platzhalter zurück.";
    } else {
      el.innerHTML = "<strong>Preview/Fallback-Modus</strong> — keine Live-Provider, Platzhalter sind erwartbar.";
    }
  }

  var FD_VG_PROVIDER_READINESS = null;
  var FD_VG_LAST_VIDEO_GENERATE = null;

  function fdPrStatusWord(s) {
    var v = String(s || "").toLowerCase();
    if (v === "ready") return "Bereit";
    if (v === "missing") return "Fehlt";
    if (v === "optional_missing") return "Optional fehlt";
    if (v === "unknown") return "Unbekannt";
    return "Unbekannt";
  }

  function fdApplyVideoGenerateProviderReadinessHint() {
    var hint = document.getElementById("fd-vg-provider-readiness-hint");
    if (!hint) return;
    hint.textContent = "";
    var cbAssets = document.getElementById("fd-vg-live-assets");
    var assetsRequested = !!(cbAssets && cbAssets.checked);
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var requestedVoice = voiceSel ? String(voiceSel.value || "dummy") : "dummy";
    var pr = FD_VG_PROVIDER_READINESS;
    if (!pr || typeof pr !== "object") return;

    try {
      var la = pr.live_assets || {};
      var el = pr.voice_elevenlabs || {};
      var oa = pr.voice_openai || {};
      if (assetsRequested && String(la.status || "") !== "ready") {
        hint.textContent = "Echte Assets sind angefordert, aber der Asset-Provider ist nicht konfiguriert. Der Lauf wird wahrscheinlich auf Platzhalter zurückfallen.";
        return;
      }
      if (requestedVoice === "elevenlabs" && String(el.status || "") !== "ready") {
        hint.textContent = "ElevenLabs ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice.";
        return;
      }
      if (requestedVoice === "openai" && String(oa.status || "") !== "ready") {
        hint.textContent = "OpenAI TTS ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice oder fällt zurück.";
        return;
      }
    } catch (eH) {}
  }

  function fdRenderFixChecklistFromProviderReadiness(pr) {
    var wrap = document.getElementById("fd-vg-fix-checklist");
    if (!wrap) return;
    wrap.innerHTML = "";
    if (!pr || typeof pr !== "object") {
      wrap.innerHTML = "<div class='fd-vg-kv-row'><span class='fd-vg-k'>—</span><span class='fd-vg-v'>Unbekannt</span></div>";
      return;
    }

    function addFix(label, envName, hintText) {
      var row = document.createElement("div");
      row.className = "fd-vg-kv-row";
      var k = document.createElement("span");
      k.className = "fd-vg-k";
      k.textContent = label;
      var v = document.createElement("span");
      v.className = "fd-vg-v";
      v.textContent = String(hintText || "");
      var actions = document.createElement("span");
      actions.className = "fd-vg-v";
      actions.style.display = "inline-flex";
      actions.style.gap = "6px";
      actions.style.alignItems = "center";
      var code = document.createElement("code");
      code.textContent = envName;
      code.title = "Nur Variablennamen kopieren";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tb-copy";
      btn.textContent = "Copy";
      btn.addEventListener("click", function() {
        try { fdFpCopyToClipboard(envName, btn); } catch (eC) {}
      });
      actions.appendChild(code);
      actions.appendChild(btn);
      row.appendChild(k);
      row.appendChild(v);
      row.appendChild(actions);
      wrap.appendChild(row);
    }

    var la = pr.live_assets || {};
    var el = pr.voice_elevenlabs || {};
    var oa = pr.voice_openai || {};
    var rw = pr.motion_runway || {};
    var imgOi = pr.image_openai || {};
    var added = 0;
    var cbAssets = document.getElementById("fd-vg-live-assets");
    var assetsRequested = !!(cbAssets && cbAssets.checked);
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var requestedVoice = voiceSel ? String(voiceSel.value || "dummy") : "dummy";

    if (assetsRequested && String(la.status || "") !== "ready") {
      addFix("Live Assets konfigurieren", "LEONARDO_API_KEY", "Setze LEONARDO_API_KEY in der Laufzeitumgebung/Secret-Konfiguration.");
      added += 1;
    }
    if (requestedVoice === "elevenlabs" && String(el.status || "") !== "ready") {
      addFix("ElevenLabs konfigurieren", "ELEVENLABS_API_KEY", "Setze ELEVENLABS_API_KEY in der Laufzeitumgebung/Secret-Konfiguration.");
      added += 1;
    }
    if (requestedVoice === "openai" && String(oa.status || "") !== "ready") {
      addFix("OpenAI TTS konfigurieren", "OPENAI_API_KEY", "Setze OPENAI_API_KEY, falls OpenAI TTS genutzt werden soll.");
      added += 1;
    }
    if (String(rw.status || "") !== "ready") {
      addFix("Runway optional konfigurieren", "RUNWAY_API_KEY", "Setze RUNWAY_API_KEY nur, wenn Live-Motion-Clips genutzt werden sollen.");
      added += 1;
    }
    if (imgOi.configured === true && String(imgOi.hint || "").trim()) {
      addFix("OpenAI Bild (Modell)", "OPENAI_IMAGE_MODEL", String(imgOi.hint || ""));
      added += 1;
    }
    if (!added) {
      wrap.innerHTML = "<div class='fd-vg-kv-row'><span class='fd-vg-k'>Alles bereit</span><span class='fd-vg-v'>Keine fehlenden Provider erkannt.</span></div>";
    }
  }

  function fdApplyVideoGeneratePreflight() {
    var st = document.getElementById("fd-vg-preflight-status");
    var tx = document.getElementById("fd-vg-preflight-text");
    if (!st || !tx) return;
    var cbAssets = document.getElementById("fd-vg-live-assets");
    var assetsRequested = !!(cbAssets && cbAssets.checked);
    var cbCosts = document.getElementById("fd-vg-confirm-costs");
    var costsConfirmed = !!(cbCosts && cbCosts.checked);
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var requestedVoice = voiceSel ? String(voiceSel.value || "dummy") : "dummy";
    var voiceHintEl = document.getElementById("fd-vg-voice-mode-hint");
    var pr = FD_VG_PROVIDER_READINESS;
    var la = pr && pr.live_assets ? pr.live_assets : {};
    var el = pr && pr.voice_elevenlabs ? pr.voice_elevenlabs : {};
    var oa = pr && pr.voice_openai ? pr.voice_openai : {};
    var rw = pr && pr.motion_runway ? pr.motion_runway : {};

    // Default ist Preview/Fallback
    if (!assetsRequested) {
      st.textContent = "Preview-Modus bereit";
      tx.textContent = "Der Lauf kann starten, nutzt aber voraussichtlich Platzhalter oder Dummy-Voice, wenn Provider fehlen.";
    } else if (String(la.status || "") === "ready") {
      st.textContent = "Real-Assets-Modus bereit";
      tx.textContent = "Echte Assets können angefordert werden. Provider-Kosten möglich.";
    } else {
      st.textContent = "Real-Assets-Modus nicht vollständig bereit";
      tx.textContent = "Der Asset-Provider fehlt. Der Lauf wird wahrscheinlich auf Platzhalter zurückfallen.";
    }

    // Zusatz-Hinweise (nicht blockierend)
    var extras = [];
    if (assetsRequested && !costsConfirmed) extras.push("Kostenbestätigung fehlt – Real-Assets-Lauf kann blockiert werden.");
    if (requestedVoice === "dummy") {
      extras.push("Dummy Voice aktiv – geeignet für Tests.");
      if (voiceHintEl) voiceHintEl.textContent = "Dummy Voice aktiv – geeignet für Tests.";
    } else if (requestedVoice === "none") {
      extras.push("Keine Voice ausgewählt.");
      if (voiceHintEl) voiceHintEl.textContent = "Keine Voice ausgewählt.";
    } else if (requestedVoice === "elevenlabs") {
      if (String(el.status || "") === "ready") {
        extras.push("ElevenLabs bereit.");
        if (voiceHintEl) voiceHintEl.textContent = "ElevenLabs bereit.";
      } else {
        extras.push("ElevenLabs ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice.");
        if (voiceHintEl) voiceHintEl.textContent = "ElevenLabs ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice.";
      }
    } else if (requestedVoice === "openai") {
      if (String(oa.status || "") === "ready") {
        extras.push("OpenAI TTS bereit.");
        if (voiceHintEl) voiceHintEl.textContent = "OpenAI TTS bereit.";
      } else {
        extras.push("OpenAI TTS ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice oder fällt zurück.");
        if (voiceHintEl) voiceHintEl.textContent = "OpenAI TTS ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice oder fällt zurück.";
      }
    }
    if (String(rw.status || "") !== "ready") extras.push("Motion-Clips sind optional und aktuell nicht verfügbar.");
    var cbThumbPf = document.getElementById("fd-vg-generate-thumbnail-pack");
    var thumbPf = !!(cbThumbPf && cbThumbPf.checked);
    if (thumbPf && !costsConfirmed) extras.push("Thumbnail Pack: Kostenbestätigung fehlt — Server kann mit 422 antworten.");
    if (thumbPf) extras.push("Thumbnail Pack erzeugt nach erfolgreichem Video zusätzliche OpenAI-Bilder (Kosten).");
    if (extras.length) tx.textContent = tx.textContent + " " + extras.join(" ");
  }

  function fdRsSetRow(idBase, statusText, detailText) {
    var v = document.getElementById("fd-vg-rs-" + idBase);
    var b = document.getElementById("fd-vg-rs-" + idBase + "-b");
    if (v) v.textContent = String(detailText || "—");
    if (b) {
      b.textContent = String(statusText || "Unbekannt");
      b.className = "fd-vg-badge " + (statusText === "OK" ? "fd-vg-badge--ok" : (statusText === "Prüfen" ? "fd-vg-badge--fallback" : "fd-vg-badge--neutral"));
    }
  }

  function fdApplyRealProductionSmokeChecklist() {
    var pr = FD_VG_PROVIDER_READINESS;
    var cbAssets = document.getElementById("fd-vg-live-assets");
    var assetsRequested = !!(cbAssets && cbAssets.checked);
    var cbCosts = document.getElementById("fd-vg-confirm-costs");
    var costsConfirmed = !!(cbCosts && cbCosts.checked);
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var requestedVoice = voiceSel ? String(voiceSel.value || "dummy") : "dummy";
    var reco = document.getElementById("fd-vg-rs-reco");

    var la = pr && pr.live_assets ? pr.live_assets : {};
    var el = pr && pr.voice_elevenlabs ? pr.voice_elevenlabs : {};
    var oa = pr && pr.voice_openai ? pr.voice_openai : {};
    var rw = pr && pr.motion_runway ? pr.motion_runway : {};
    var last = FD_VG_LAST_VIDEO_GENERATE;
    var lastAa = last && last.asset_artifact ? last.asset_artifact : null;
    var lastGate = lastAa && lastAa.asset_quality_gate ? lastAa.asset_quality_gate : null;
    var restored = null;
    if (!lastGate) {
      try { restored = fdVgGetRestoredAssetQualityGate(fdVgLoadLastRunSummary()); } catch (eR) { restored = null; }
    }
    // current payload wins; localStorage is restore-fallback after reload
    var gateEffective = lastGate || restored;
    var lastStatus = gateEffective && gateEffective.status ? String(gateEffective.status) : "";
    var lastStrict = !!(gateEffective && gateEffective.strict_ready);
    var lastLoose = !!(gateEffective && gateEffective.loose_ready);
    var localMark = (gateEffective && gateEffective.source === "local") ? " (local)" : "";
    var localHint = (gateEffective && gateEffective.source === "local") ? " aus letztem gespeicherten Lauf" : "";
    // keep strings in bundle for tests + operator clarity
    var FD_VG_ASSET_QUALITY_HINTS = {
      production_ready: "Asset Manifest enthält echte Assets ohne Placeholder.",
      mixed_assets: "Echte Assets vorhanden, aber noch Placeholder im Manifest.",
      placeholder_only: "Nur Placeholder-Assets vorhanden.",
      missing_assets: "Keine Asset-Dateien im Manifest.",
      unknown: "Asset-Qualität noch nicht verfügbar."
    };

    // Live Assets angefordert
    fdRsSetRow(
      "live-assets",
      assetsRequested ? "OK" : "Prüfen",
      assetsRequested ? "Echte Assets aktiv" : "Toggle aus (Preview/Fallback)"
    );

    // Kosten bestätigt (nur relevant wenn Live Assets angefordert sind)
    if (!assetsRequested) {
      fdRsSetRow("costs", "Nicht verfügbar", "Preview/Fallback");
    } else {
      fdRsSetRow(
        "costs",
        costsConfirmed ? "OK" : "Prüfen",
        costsConfirmed ? "Kosten bestätigt" : "Kostenbestätigung fehlt – Real-Assets-Lauf kann blockiert werden."
      );
    }

    // Asset Provider bereit
    var assetReady = String(la.status || "") === "ready";
    fdRsSetRow(
      "asset-provider",
      assetReady ? "OK" : "Prüfen",
      assetReady ? "Provider bereit" : ("Status: " + fdPrStatusWord(la.status))
    );

    // Asset Quality (post-run; do not require pre-run)
    if (!gateEffective || !lastStatus) {
      fdRsSetRow("asset-quality", "Nicht verfügbar", "Asset-Qualität noch nicht verfügbar.");
    } else if (lastStrict) {
      fdRsSetRow("asset-quality", "OK", "production_ready — " + ((gateEffective.summary || FD_VG_ASSET_QUALITY_HINTS.production_ready) + localMark));
    } else if (lastLoose) {
      // loose true but strict false => mixed or placeholder-like stage
      fdRsSetRow("asset-quality", "Prüfen", (lastStatus || "mixed_assets") + " — " + ((gateEffective.summary || FD_VG_ASSET_QUALITY_HINTS.mixed_assets) + localMark));
    } else {
      // placeholder_only / missing_assets / unknown
      var hint = FD_VG_ASSET_QUALITY_HINTS[lastStatus] || "Asset-Qualität noch nicht verfügbar.";
      fdRsSetRow("asset-quality", "Nicht verfügbar", (lastStatus || "unknown") + " — " + ((gateEffective.summary || hint) + localMark));
    }

    // Voice-Modus produktiv gewählt
    var voiceProd = (requestedVoice === "elevenlabs" || requestedVoice === "openai");
    var voiceNone = (requestedVoice === "none");
    fdRsSetRow(
      "voice-mode",
      voiceProd ? "OK" : (voiceNone ? "Nicht verfügbar" : "Prüfen"),
      requestedVoice
    );

    // Voice Provider bereit (abhängig von Selection)
    var vpStatus = "Nicht verfügbar";
    var vpDetail = "—";
    var vpOk = false;
    if (requestedVoice === "elevenlabs") {
      vpOk = String(el.status || "") === "ready";
      vpStatus = vpOk ? "OK" : "Prüfen";
      vpDetail = vpOk ? "ElevenLabs bereit" : "ElevenLabs fehlt";
    } else if (requestedVoice === "openai") {
      vpOk = String(oa.status || "") === "ready";
      vpStatus = vpOk ? "OK" : "Prüfen";
      vpDetail = vpOk ? "OpenAI TTS bereit" : "OpenAI TTS fehlt";
    } else if (requestedVoice === "dummy") {
      vpStatus = "Nicht verfügbar";
      vpDetail = "Dummy / Test";
    } else if (requestedVoice === "none") {
      vpStatus = "Nicht verfügbar";
      vpDetail = "keine Voice";
    } else {
      vpStatus = "Unbekannt";
      vpDetail = "—";
    }
    fdRsSetRow("voice-provider", vpStatus, vpDetail);

    // Timing / Voice Fit (best-effort aus letztem Lauf)
    try {
      var ta = last && last.timing_audit ? last.timing_audit : null;
      if (ta && typeof ta === "object") {
        function fdFmtSeconds2(v) {
          try {
            var n = Number(v);
            if (!isFinite(n)) return null;
            return n.toFixed(2) + "s";
          } catch (e) {
            return null;
          }
        }
        var pad = !!ta.padding_or_continue_applied;
        var vds = ta.voice_duration_seconds;
        var tds = ta.timeline_duration_seconds;
        var gapAbs = ta.timing_gap_abs_seconds;
        var gapStatus = String(ta.timing_gap_status || "unknown");
        var gapFmt = (gapAbs != null) ? fdFmtSeconds2(gapAbs) : null;
        var detBase = gapFmt ? ("Gap: " + gapFmt) : ((vds != null && tds != null) ? ("Voice ~" + String(vds) + "s vs Timeline ~" + String(tds) + "s") : (String(ta.summary || "—") || "—"));
        var st = (gapStatus === "major_gap") ? "Prüfen" : (pad ? "Prüfen" : (gapStatus === "ok" ? "OK" : (gapStatus === "minor_gap" ? "Prüfen" : "Nicht verfügbar")));
        var detail = detBase;
        if (pad) detail = detail + " · Audio kürzer als Timeline; gepadded/fortgeführt";
        fdRsSetRow("timing", st, detail);
      } else {
        fdRsSetRow("timing", "Nicht verfügbar", "timing_audit fehlt");
      }
    } catch (eT) {
      fdRsSetRow("timing", "Nicht verfügbar", "timing_audit Fehler");
    }

    // Motion optional (darf nicht blocken)
    var rwReady = String(rw.status || "") === "ready";
    fdRsSetRow(
      "motion",
      rwReady ? "OK" : "Prüfen",
      rwReady ? "Runway bereit" : ("Status: " + fdPrStatusWord(rw.status))
    );

    // Empfehlung ableiten
    var isPreviewOnly = !assetsRequested;
    var canRealAssets = assetsRequested && assetReady && costsConfirmed;
    var canProdVoice = voiceProd && vpOk;
    if (isPreviewOnly) {
      if (reco) reco.textContent = "Nur Preview/Fallback-Smoke";
    } else if (canRealAssets && canProdVoice) {
      var extra = "";
      if (lastStatus === "production_ready") extra = " · Asset-Gate bestanden.";
      else if (lastStatus === "mixed_assets") extra = " · Zwischenstufe: Live Assets funktionieren teilweise, aber Placeholder müssen noch ersetzt werden.";
      if (reco) reco.textContent = "Bereit für Real Production Smoke" + extra + (localHint ? (" ·" + localHint) : "");
    } else {
      if (reco) reco.textContent = "Noch nicht production-ready";
    }
  }

  function fdApplyRealProductionSmokePreset() {
    var pr = FD_VG_PROVIDER_READINESS || {};
    var la = pr.live_assets || {};
    var el = pr.voice_elevenlabs || {};
    var oa = pr.voice_openai || {};

    var cbAssets = document.getElementById("fd-vg-live-assets");
    var cbCosts = document.getElementById("fd-vg-confirm-costs");
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var hint = document.getElementById("fd-vg-real-smoke-preset-hint");

    if (cbAssets) cbAssets.checked = true;
    if (cbCosts) cbCosts.checked = true;

    var chosenVoice = "dummy";
    // Priorität: ElevenLabs vor OpenAI vor Dummy
    if (String(el.status || "") === "ready") chosenVoice = "elevenlabs";
    else if (String(oa.status || "") === "ready") chosenVoice = "openai";
    else chosenVoice = "dummy";
    if (voiceSel) voiceSel.value = chosenVoice;

    // Hinweistext
    var parts = [];
    if (chosenVoice === "elevenlabs" || chosenVoice === "openai") {
      parts.push("Preset aktiviert: Live Assets an, produktive Voice gewählt. Mögliche Provider-Kosten wurden bestätigt.");
    } else {
      parts.push("Preset aktiviert: Live Assets an, Kosten bestätigt, aber kein Voice-Provider bereit – Dummy Voice bleibt aktiv.");
    }
    if (String(la.status || "") !== "ready") {
      parts.push("Asset-Provider fehlt – der Lauf kann weiterhin auf Platzhalter zurückfallen.");
    }
    if (hint) hint.textContent = parts.join(" ");

    // UI refresh
    try { fdApplyVideoGenerateAssetsModeHint(); } catch (e0) {}
    try { fdApplyVideoGenerateProviderReadinessHint(); } catch (e1) {}
    try { fdApplyVideoGeneratePreflight(); } catch (e2) {}
    try { fdRenderFixChecklistFromProviderReadiness(FD_VG_PROVIDER_READINESS); } catch (e3) {}
    try { fdApplyRealProductionSmokeChecklist(); } catch (e4) {}
    try { fdApplyInline422Hint(); } catch (e5) {}
  }

  function fdApplyOpenAiImageMiniSmokePreset() {
    var cbThumb = document.getElementById("fd-vg-generate-thumbnail-pack");
    var nCand = document.getElementById("fd-vg-thumb-cand-count");
    var nOut = document.getElementById("fd-vg-thumb-max-out");
    if (cbThumb) cbThumb.checked = false;
    if (nCand) nCand.value = "1";
    if (nOut) nOut.value = "2";
    var cbAssets = document.getElementById("fd-vg-live-assets");
    var cbCosts = document.getElementById("fd-vg-confirm-costs");
    var cbMotion = document.getElementById("fd-vg-live-motion");
    var voiceSel = document.getElementById("fd-vg-voice-mode");
    var maxSc = document.getElementById("fd-vg-max-scenes");
    var maxLive = document.getElementById("fd-vg-max-live");
    var maxMot = document.getElementById("fd-vg-max-motion");
    var imgProv = document.getElementById("fd-vg-image-provider");
    var oaiModel = document.getElementById("fd-vg-openai-image-model");
    var oaiSize = document.getElementById("fd-vg-openai-image-size");
    if (cbMotion) cbMotion.checked = false;
    if (cbAssets) cbAssets.checked = true;
    if (cbCosts) cbCosts.checked = true;
    fdVgDispatchInputChange(cbAssets);
    fdVgDispatchInputChange(cbCosts);
    if (voiceSel) voiceSel.value = "none";
    if (maxSc) maxSc.value = "1";
    if (maxLive) maxLive.value = "1";
    if (maxMot) maxMot.value = "0";
    if (imgProv) imgProv.value = "openai_image";
    if (oaiModel) oaiModel.value = "gpt-image-2";
    if (oaiSize) oaiSize.value = "1024x1024";
    try { fdApplyVideoGenerateAssetsModeHint(); } catch (eA) {}
    try { fdApplyVideoGenerateProviderReadinessHint(); } catch (eB) {}
    try { fdApplyVideoGeneratePreflight(); } catch (eC) {}
    try { fdRenderFixChecklistFromProviderReadiness(FD_VG_PROVIDER_READINESS); } catch (eD) {}
    try { fdApplyRealProductionSmokeChecklist(); } catch (eE) {}
    try { fdApplyInline422Hint(); } catch (eF) {}
  }

  function fdApplyInline422Hint() {
    var el = document.getElementById("fd-vg-inline-422-hint");
    var go = document.getElementById("fd-vg-go-confirm-costs");
    if (!el) return;
    if (go) go.style.display = "none";
    var cbAssets = document.getElementById("fd-vg-live-assets");
    var cbCosts = document.getElementById("fd-vg-confirm-costs");
    var assetsRequested = !!(cbAssets && cbAssets.checked);
    var costsConfirmed = !!(cbCosts && cbCosts.checked);
    var cbThumb = document.getElementById("fd-vg-generate-thumbnail-pack");
    var thumbRequested = !!(cbThumb && cbThumb.checked);
    if ((assetsRequested || thumbRequested) && !costsConfirmed) {
      el.textContent = "Ohne Kostenbestätigung kann der Server den Real-Assets- oder Thumbnail-Pack-Lauf mit 422 ablehnen.";
      return;
    }
    if (assetsRequested && costsConfirmed) {
      el.textContent = "Kostenbestätigung aktiv.";
      return;
    }
    el.textContent = "Preview/Fallback-Modus – keine Live-Asset-Kosten erwartet.";
  }

  function fdVgApplyDevKeyOverrideHint() {
    var el = document.getElementById("fd-vg-dev-keys-hint");
    if (!el) return;
    var oai = document.getElementById("fd-vg-dev-openai-api-key");
    var ev = document.getElementById("fd-vg-dev-elevenlabs-api-key");
    var rw = document.getElementById("fd-vg-dev-runway-api-key");
    var leo = document.getElementById("fd-vg-dev-leonardo-api-key");
    var hasOai = !!(oai && String(oai.value || "").trim());
    var hasEv = !!(ev && String(ev.value || "").trim());
    var hasRw = !!(rw && String(rw.value || "").trim());
    var hasLeo = !!(leo && String(leo.value || "").trim());
    var parts = [];
    if (hasOai) parts.push("OpenAI Key per Request vorhanden.");
    if (hasEv) parts.push("ElevenLabs Key per Request vorhanden.");
    if (hasRw) parts.push("Runway Key per Request vorhanden.");
    if (hasLeo) parts.push("Leonardo Key per Request vorhanden.");
    el.textContent = parts.length ? parts.join(" ") : "";
  }

  var FD_VG_LAST_VIDEO_GENERATE_KEY = "FD_VG_LAST_VIDEO_GENERATE";

  function fdVgDeriveStatusFromPayload(j) {
    try {
      if (!j || typeof j !== "object") return "blocked";
      var rs0 = j.video_generate_run_status != null ? String(j.video_generate_run_status).trim() : "";
      if (rs0) return rs0;
      var ok = !!j.ok;
      var blocking = (j.blocking_reasons && j.blocking_reasons.length) ? j.blocking_reasons : [];
      if (!ok || (blocking && blocking.length)) return "blocked";
      var warnings = (j.warnings && j.warnings.length) ? j.warnings : [];
      var joined = fdVgWarnJoinedLower(warnings);
      var hasFallback = fdVgWarnTriggersFallbackPreview(j, joined);
      return hasFallback ? "fallback_preview" : "production_ready";
    } catch (e) {}
    return "blocked";
  }

  function fdVgBuildLastRunSummary(j) {
    try {
      if (!j || typeof j !== "object") return null;
      var ra = (j.readiness_audit && typeof j.readiness_audit === "object") ? j.readiness_audit : {};
      var aa = (j.asset_artifact && typeof j.asset_artifact === "object") ? j.asset_artifact : {};
      var gate = (aa.asset_quality_gate && typeof aa.asset_quality_gate === "object") ? aa.asset_quality_gate : {};
      var va = (j.voice_artifact && typeof j.voice_artifact === "object") ? j.voice_artifact : {};
      var status = fdVgDeriveStatusFromPayload(j);
      var runId = j.run_id != null ? String(j.run_id) : "";
      return {
        saved_at: (new Date()).toISOString(),
        run_id: runId,
        status: status,
        next_action: j.next_action != null ? String(j.next_action) : "",
        warnings_count: (j.warnings && j.warnings.length) ? parseInt(j.warnings.length, 10) : 0,
        blocking_reasons_count: (j.blocking_reasons && j.blocking_reasons.length) ? parseInt(j.blocking_reasons.length, 10) : 0,
        readiness_audit: {
          requested_live_assets: !!ra.requested_live_assets,
          asset_quality_status: ra.asset_quality_status != null ? String(ra.asset_quality_status) : "",
          asset_strict_ready: !!ra.asset_strict_ready,
          asset_loose_ready: !!ra.asset_loose_ready,
          requested_voice_mode: ra.requested_voice_mode != null ? String(ra.requested_voice_mode) : "",
          effective_voice_mode: ra.effective_voice_mode != null ? String(ra.effective_voice_mode) : "",
          voice_file_ready: !!ra.voice_file_ready,
          voice_is_dummy: !!ra.voice_is_dummy,
          silent_render_expected: typeof ra.silent_render_expected === "boolean" ? !!ra.silent_render_expected : null,
          silent_render_reason: ra.silent_render_reason != null ? String(ra.silent_render_reason) : ""
        },
        asset_quality_gate: {
          status: gate.status != null ? String(gate.status) : "",
          strict_ready: !!gate.strict_ready,
          loose_ready: !!gate.loose_ready,
          summary: gate.summary != null ? String(gate.summary) : ""
        },
        voice_artifact_summary: {
          requested_voice_mode: va.requested_voice_mode != null ? String(va.requested_voice_mode) : "",
          effective_voice_mode: va.effective_voice_mode != null ? String(va.effective_voice_mode) : "",
          voice_ready: !!va.voice_ready,
          is_dummy: !!va.is_dummy,
          duration_seconds: (va.duration_seconds == null ? null : Number(va.duration_seconds))
        }
      };
    } catch (e) {}
    return null;
  }

  function fdVgSaveLastRunSummary(j) {
    try {
      var sum = fdVgBuildLastRunSummary(j);
      if (!sum) return;
      // Data minimization: only the compact summary is saved.
      window.localStorage && window.localStorage.setItem(FD_VG_LAST_VIDEO_GENERATE_KEY, JSON.stringify(sum));
    } catch (e) {}
  }

  function fdVgLoadLastRunSummary() {
    try {
      if (!window.localStorage) return null;
      var raw = window.localStorage.getItem(FD_VG_LAST_VIDEO_GENERATE_KEY);
      if (!raw) return null;
      var j = JSON.parse(raw);
      if (!j || typeof j !== "object") return null;
      return j;
    } catch (e) {
      try { window.localStorage && window.localStorage.removeItem(FD_VG_LAST_VIDEO_GENERATE_KEY); } catch (e2) {}
      return null;
    }
  }

  function fdVgIsLastRunSummaryExpired(sum, days) {
    try {
      var d = (days == null ? 7 : parseInt(days, 10));
      if (!sum || typeof sum !== "object") return true;
      var s = sum.saved_at ? String(sum.saved_at) : "";
      if (!s) return true;
      var t = Date.parse(s);
      if (!isFinite(t)) return true;
      var ageMs = Date.now() - t;
      var maxMs = Math.max(1, d) * 24 * 60 * 60 * 1000;
      return ageMs > maxMs;
    } catch (e) {}
    return true;
  }

  function fdVgGetRestoredAssetQualityGate(sum) {
    // Restore-fallback: use compact localStorage summary, without backend calls.
    try {
      if (!sum || typeof sum !== "object") return null;
      if (fdVgIsLastRunSummaryExpired(sum, 7)) return null;
      var gate = (sum.asset_quality_gate && typeof sum.asset_quality_gate === "object") ? sum.asset_quality_gate : null;
      var ra = (sum.readiness_audit && typeof sum.readiness_audit === "object") ? sum.readiness_audit : null;
      var st = gate && gate.status ? String(gate.status) : (ra && ra.asset_quality_status ? String(ra.asset_quality_status) : "");
      if (!st) return null;
      return {
        status: st,
        strict_ready: !!(gate && gate.strict_ready) || !!(ra && ra.asset_strict_ready),
        loose_ready: !!(gate && gate.loose_ready) || !!(ra && ra.asset_loose_ready),
        summary: gate && gate.summary ? String(gate.summary) : "",
        source: "local"
      };
    } catch (e) {}
    return null;
  }

  function fdVgForgetLastRunSummary() {
    try { window.localStorage && window.localStorage.removeItem(FD_VG_LAST_VIDEO_GENERATE_KEY); } catch (e) {}
  }

  function fdVgRenderLastRunSummary(sum) {
    var box = document.getElementById("fd-vg-last-run-summary");
    var kv = document.getElementById("fd-vg-last-run-kv");
    if (!box || !kv) return;
    if (sum && fdVgIsLastRunSummaryExpired(sum, 7)) {
      try { fdVgForgetLastRunSummary(); } catch (eF) {}
      sum = null;
    }
    if (!sum || typeof sum !== "object") {
      box.style.display = "none";
      kv.innerHTML = "";
      return;
    }
    box.style.display = "block";
    kv.innerHTML = "";
    function row(k, v) {
      var r = document.createElement("div");
      r.className = "fd-vg-kv-row";
      var kk = document.createElement("span");
      kk.className = "fd-vg-k";
      kk.textContent = String(k);
      var vv = document.createElement("span");
      vv.className = "fd-vg-v";
      vv.textContent = (v == null || v === "") ? "—" : String(v);
      r.appendChild(kk); r.appendChild(vv);
      kv.appendChild(r);
    }
    row("run_id", sum.run_id || "—");
    row("saved_at", sum.saved_at || "—");
    row("status", sum.status || "—");
    row("asset_quality_status", (sum.readiness_audit && sum.readiness_audit.asset_quality_status) ? sum.readiness_audit.asset_quality_status : (sum.asset_quality_gate && sum.asset_quality_gate.status ? sum.asset_quality_gate.status : "—"));
    row("voice (effective)", (sum.readiness_audit && sum.readiness_audit.effective_voice_mode) ? sum.readiness_audit.effective_voice_mode : (sum.voice_artifact_summary && sum.voice_artifact_summary.effective_voice_mode ? sum.voice_artifact_summary.effective_voice_mode : "—"));
  }

  function fdVgErrorDetailContains(payloadOrDetail, needle) {
    try {
      if (!needle) return false;
      var n = String(needle);
      if (!n) return false;
      if (payloadOrDetail == null) return false;
      // If a full response/payload is passed, prefer its .detail field.
      var d = payloadOrDetail;
      if (typeof payloadOrDetail === "object" && payloadOrDetail.detail != null) d = payloadOrDetail.detail;
      if (typeof d === "string") return String(d).indexOf(n) >= 0;
      if (Array.isArray(d)) return JSON.stringify(d).indexOf(n) >= 0;
      if (typeof d === "object") return JSON.stringify(d).indexOf(n) >= 0;
      return String(d).indexOf(n) >= 0;
    } catch (e) {}
    return false;
  }

  function fdIsConfirmCostsRequired422(detail) {
    // Backwards-compatible wrapper (used by tests/older codepaths)
    return fdVgErrorDetailContains(detail, "confirm_provider_costs_required_when_live_flags");
  }

  function fdScrollToConfirmCosts() {
    var cb = document.getElementById("fd-vg-confirm-costs");
    if (!cb) return;
    try { cb.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) { try { cb.scrollIntoView(true); } catch (e2) {} }
    try { cb.focus({ preventScroll: true }); } catch (e3) { try { cb.focus(); } catch (e4) {} }
    // small highlight
    try {
      cb.style.outline = "2px solid rgba(251,191,36,.9)";
      cb.style.outlineOffset = "3px";
      setTimeout(function() {
        cb.style.outline = "";
        cb.style.outlineOffset = "";
      }, 1400);
    } catch (e5) {}
  }

  async function fdLoadVideoGenerateProviderReadiness() {
    try {
      const r = await fetch("/founder/dashboard/config", { method: "GET" });
      if (!r.ok) return;
      var j = null;
      try { j = await r.json(); } catch (eJ) {}
      var pr = j && j.provider_readiness ? j.provider_readiness : null;
      if (!pr || typeof pr !== "object") return;
      FD_VG_PROVIDER_READINESS = pr;
      var la = pr.live_assets || {};
      var el = pr.voice_elevenlabs || {};
      var oa = pr.voice_openai || {};
      var rw = pr.motion_runway || {};
      var elLa = document.getElementById("fd-vg-pr-live-assets");
      var elEl = document.getElementById("fd-vg-pr-eleven");
      var elOa = document.getElementById("fd-vg-pr-openai");
      var elRw = document.getElementById("fd-vg-pr-runway");
      if (elLa) elLa.textContent = fdPrStatusWord(la.status);
      if (elEl) elEl.textContent = fdPrStatusWord(el.status);
      if (elOa) elOa.textContent = fdPrStatusWord(oa.status);
      if (elRw) elRw.textContent = fdPrStatusWord(rw.status);
      fdApplyVideoGenerateProviderReadinessHint();
      fdApplyVideoGeneratePreflight();
      fdRenderFixChecklistFromProviderReadiness(pr);
      fdApplyRealProductionSmokeChecklist();
      fdApplyInline422Hint();
    } catch (e) {}
  }

  async function fdStartFreshPreviewDryRun() {
    var st = document.getElementById("fp-dry-run-status");
    var resEl = document.getElementById("fp-dry-run-result");
    var handoffWrap = document.getElementById("fp-dry-run-handoff");
    var btn = document.getElementById("fp-btn-start-dry-run");
    if (!btn) return;
    var label = btn.getAttribute("data-label") || btn.textContent || "Struktur-Test starten";
    if (isKillSwitchActive()) {
      if (st) {
        st.textContent = "Kill Switch aktiv — Struktur-Test blockiert.";
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
    fdClearDashboardManualResetFlag();
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
    btn.textContent = "Struktur-Test läuft…";
    if (resEl) {
      resEl.style.display = "none";
      resEl.textContent = "";
    }
    if (handoffWrap) handoffWrap.style.display = "none";
    if (st) st.textContent = "Starte Struktur-Test …";
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
          st.textContent = "Struktur-Test: " + String(detail);
          st.classList.add("intake-status-err");
        }
        if (handoffWrap) handoffWrap.style.display = "none";
        btn.classList.add("is-error");
        return;
      }
      if (!j || j.ok !== true) {
        if (st) {
          st.textContent = "Struktur-Test beendet mit Blockern. Siehe Details.";
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
        st.textContent = (j.snapshot_hint || "Status aktualisieren") + " — Run " + (j.run_id || "—");
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
        st.textContent = "Struktur-Test: " + (e && e.message ? e.message : String(e));
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

  function fdGuidedStatusLabel(st) {
    var s = String(st || "").toLowerCase();
    if (s === "done") return "Erledigt";
    if (s === "active") return "Aktiv";
    if (s === "pending") return "Offen";
    if (s === "warning") return "Hinweis";
    if (s === "blocked") return "Blockiert";
    if (s === "locked") return "Gesperrt";
    return s || "—";
  }

  function fdGuidedStatusBadgeClass(st) {
    var s = String(st || "").toLowerCase();
    if (s === "done") return "fd-guided-step-badge fd-guided-step-badge--done";
    if (s === "active") return "fd-guided-step-badge fd-guided-step-badge--active";
    if (s === "pending") return "fd-guided-step-badge fd-guided-step-badge--pending";
    if (s === "warning") return "fd-guided-step-badge fd-guided-step-badge--warning";
    if (s === "blocked") return "fd-guided-step-badge fd-guided-step-badge--blocked";
    if (s === "locked") return "fd-guided-step-badge fd-guided-step-badge--locked";
    return "fd-guided-step-badge fd-guided-step-badge--pending";
  }

  function fdFpResetGuidedFlowNeutral() {
    var host = document.getElementById("fd-guided-flow-steps");
    var nx = document.getElementById("fd-guided-flow-next-action");
    var lb = document.getElementById("fd-guided-flow-next-label");
    if (host) host.innerHTML = "";
    if (lb) lb.textContent = "";
    if (nx) nx.textContent = "—";
  }

  function fdFpApplyGuidedFlow(d) {
    var host = document.getElementById("fd-guided-flow-steps");
    var nx = document.getElementById("fd-guided-flow-next-action");
    var lb = document.getElementById("fd-guided-flow-next-label");
    if (!host || !nx) return;
    var steps = d && d.guided_flow_steps;
    var cur = d && d.guided_flow_current_step ? String(d.guided_flow_current_step) : "";
    if (!steps || !steps.length) {
      host.innerHTML = "";
      if (lb) lb.textContent = "";
      nx.textContent = "—";
      return;
    }
    host.innerHTML = "";
    steps.forEach(function(step) {
      var id = step && step.id != null ? String(step.id) : "";
      var ord = step && step.order != null ? step.order : "";
      var label = step && step.label != null ? String(step.label) : "—";
      var detail = step && step.detail != null ? String(step.detail) : "";
      var st = step && step.status != null ? String(step.status) : "pending";
      var div = document.createElement("div");
      div.className = "fd-guided-flow-step" + (cur && id === cur ? " fd-guided-flow-step--current" : "");
      div.setAttribute("data-guided-step-id", id);
      div.innerHTML =
        '<div class="fd-guided-flow-step-num">Schritt ' + String(ord) + '</div>' +
        '<div class="fd-guided-flow-step-label">' + label.replace(/</g, "&lt;") + '</div>' +
        (detail ? '<div class="fd-guided-flow-step-detail">' + detail.replace(/</g, "&lt;") + '</div>' : '') +
        '<span class="' + fdGuidedStatusBadgeClass(st) + '">' + fdGuidedStatusLabel(st) + '</span>';
      host.appendChild(div);
    });
    if (lb) lb.textContent = (d && d.guided_flow_next_step_label) ? String(d.guided_flow_next_step_label) : "";
    nx.textContent = (d && d.guided_flow_next_step_action) ? String(d.guided_flow_next_step_action) : "—";
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

  function fdFpApplyOperatorReview(d) {
    var badge = document.getElementById("fp-review-decision-badge");
    var ul = document.getElementById("fp-review-reasons");
    var nx = document.getElementById("fp-review-next-action");
    if (!badge || !ul || !nx) return;
    var dec = String((d && d.review_decision) || "pending").toLowerCase();
    var label = (d && d.review_decision_label) ? String(d.review_decision_label) : "Ausstehend";
    badge.textContent = label;
    badge.setAttribute("data-review-decision-marker", dec);
    var bcls = "fp-review-badge ";
    if (dec === "approve") bcls += "fp-review-badge--approve";
    else if (dec === "rework") bcls += "fp-review-badge--rework";
    else if (dec === "blocked") bcls += "fp-review-badge--blocked";
    else bcls += "fp-review-badge--pending";
    badge.className = bcls;
    ul.innerHTML = "";
    var rs = d && d.review_decision_reasons;
    if (rs && rs.length) {
      rs.forEach(function(x) {
        var li = document.createElement("li");
        li.textContent = String(x);
        ul.appendChild(li);
      });
    } else {
      var li0 = document.createElement("li");
      li0.textContent = "—";
      ul.appendChild(li0);
    }
    nx.textContent = (d && d.review_next_action) ? String(d.review_next_action) : "";
  }

  function fdFpResetFinalRenderGateNeutral() {
    var badge = document.getElementById("fp-final-render-gate-status");
    var ul = document.getElementById("fp-final-render-gate-reasons");
    var nx = document.getElementById("fp-final-render-next-action");
    if (badge) {
      badge.textContent = "—";
      badge.setAttribute("data-final-render-gate-marker", "locked");
      badge.className = "fp-fr-gate-badge fp-fr-gate-badge--locked";
    }
    if (ul) ul.innerHTML = "";
    if (nx) nx.textContent = "—";
  }

  function fdFpApplyFinalRenderGate(d) {
    var badge = document.getElementById("fp-final-render-gate-status");
    var ul = document.getElementById("fp-final-render-gate-reasons");
    var nx = document.getElementById("fp-final-render-next-action");
    if (!badge || !ul || !nx) return;
    var st = String((d && d.final_render_gate_status) || "locked").toLowerCase();
    var label = (d && d.final_render_gate_label) ? String(d.final_render_gate_label) : "Gesperrt";
    badge.textContent = label;
    badge.setAttribute("data-final-render-gate-marker", st);
    var bcls = "fp-fr-gate-badge ";
    if (st === "ready") bcls += "fp-fr-gate-badge--ready";
    else if (st === "needs_rework") bcls += "fp-fr-gate-badge--rework";
    else if (st === "blocked") bcls += "fp-fr-gate-badge--blocked";
    else bcls += "fp-fr-gate-badge--locked";
    badge.className = bcls;
    ul.innerHTML = "";
    var gr = d && d.final_render_gate_reasons;
    if (gr && gr.length) {
      gr.forEach(function(x) {
        var li = document.createElement("li");
        li.textContent = String(x);
        ul.appendChild(li);
      });
    } else {
      var li0 = document.createElement("li");
      li0.textContent = "—";
      ul.appendChild(li0);
    }
    nx.textContent = (d && d.final_render_next_action) ? String(d.final_render_next_action) : "";
  }

  function fdFpChecklistItemStatusClass(st) {
    var s = String(st || "").toLowerCase();
    if (s === "present") return "fp-fr-input-item-status fp-fr-input-item-status--present";
    if (s === "unknown") return "fp-fr-input-item-status fp-fr-input-item-status--unknown";
    return "fp-fr-input-item-status fp-fr-input-item-status--missing";
  }

  function fdFpBuildFinalRenderInputRow(it) {
    var row = document.createElement("div");
    row.className = "fp-fr-input-row";
    row.setAttribute("data-fr-input-item-id", String(it && it.id ? it.id : ""));
    var left = document.createElement("div");
    var lab = document.createElement("div");
    lab.className = "fp-fr-input-row-label";
    lab.textContent = it && it.label ? String(it.label) : "—";
    var meta = document.createElement("div");
    meta.className = "fp-fr-input-row-meta";
    meta.textContent = it && it.hint ? String(it.hint) : "";
    left.appendChild(lab);
    left.appendChild(meta);
    var pathCell = document.createElement("div");
    pathCell.className = "fp-fr-input-row-path";
    var pv = it && it.path ? String(it.path) : "";
    pathCell.textContent = pv || "(kein Pfad)";
    var stEl = document.createElement("div");
    var st = it && it.status ? String(it.status) : "missing";
    stEl.className = fdFpChecklistItemStatusClass(st);
    stEl.textContent = st === "present" ? "vorhanden" : (st === "unknown" ? "unklar" : "fehlt");
    var btnCell = document.createElement("div");
    btnCell.style.display = "flex";
    btnCell.style.flexWrap = "wrap";
    btnCell.style.gap = "0.35rem";
    btnCell.style.alignItems = "center";
    var openEl;
    if (pv && it && it.artifact_open_allowed) {
      openEl = document.createElement("a");
      openEl.href = fdFpArtifactFileUrl(pv);
      openEl.target = "_blank";
      openEl.rel = "noopener noreferrer";
      openEl.className = "fp-open-artifact";
      openEl.textContent = "Öffnen";
    } else {
      openEl = document.createElement("span");
      openEl.className = "fp-open-placeholder";
      openEl.setAttribute("aria-hidden", "true");
    }
    var b = document.createElement("button");
    b.type = "button";
    b.className = "fp-copy-path sm";
    b.textContent = "Kopieren";
    b.disabled = !pv;
    if (pv) {
      (function(txt, bt) { b.onclick = function() { fdFpCopyToClipboard(txt, bt); }; })(pv, b);
    }
    btnCell.appendChild(openEl);
    btnCell.appendChild(b);
    row.appendChild(left);
    row.appendChild(pathCell);
    row.appendChild(stEl);
    row.appendChild(btnCell);
    return row;
  }

  function fdFpResetFinalRenderInputChecklistNeutral() {
    var badge = document.getElementById("fp-final-render-input-checklist-status");
    var host = document.getElementById("fp-final-render-input-items");
    var nx = document.getElementById("fp-final-render-input-next-action");
    if (badge) {
      badge.textContent = "—";
      badge.setAttribute("data-fr-input-checklist-marker", "pending");
      badge.className = "fp-fr-input-badge fp-fr-input-badge--pending";
    }
    if (host) host.innerHTML = "";
    if (nx) nx.textContent = "—";
  }

  function fdFpResetSafeFinalRenderHandoffNeutral() {
    var av = document.getElementById("fp-safe-fr-availability");
    var lm = document.getElementById("fp-safe-fr-locked-msg");
    var rs = document.getElementById("fp-safe-fr-reasons");
    var note = document.getElementById("fp-safe-fr-note");
    var warn = document.getElementById("fp-safe-fr-warning");
    var pre = document.getElementById("fp-safe-final-render-cli");
    var cp = document.getElementById("fp-safe-final-render-copy");
    if (av) av.textContent = "—";
    if (lm) lm.style.display = "none";
    if (rs) { rs.innerHTML = ""; rs.style.display = "none"; }
    if (note) { note.textContent = ""; note.style.display = "none"; }
    if (warn) { warn.textContent = ""; warn.style.display = "none"; }
    if (pre) { pre.textContent = ""; pre.style.display = "none"; }
    if (cp) cp.style.display = "none";
  }

  function fdFpApplySafeFinalRenderHandoff(d) {
    var av = document.getElementById("fp-safe-fr-availability");
    var lm = document.getElementById("fp-safe-fr-locked-msg");
    var rs = document.getElementById("fp-safe-fr-reasons");
    var note = document.getElementById("fp-safe-fr-note");
    var warn = document.getElementById("fp-safe-fr-warning");
    var pre = document.getElementById("fp-safe-final-render-cli");
    var cp = document.getElementById("fp-safe-final-render-copy");
    if (!d || !av || !lm || !rs || !note || !warn || !pre || !cp) return;
    var ok = !!d.safe_final_render_handoff_available;
    if (ok) {
      av.textContent = "Status: verfügbar";
      lm.style.display = "none";
      rs.innerHTML = "";
      rs.style.display = "none";
      var ntxt = (d.safe_final_render_handoff_note) ? String(d.safe_final_render_handoff_note) : "";
      note.textContent = ntxt;
      note.style.display = ntxt ? "block" : "none";
      var wtxt = (d.safe_final_render_handoff_warning) ? String(d.safe_final_render_handoff_warning) : "";
      warn.textContent = wtxt;
      warn.style.display = wtxt ? "block" : "none";
      var cmd = (d.safe_final_render_cli_command_powershell) ? String(d.safe_final_render_cli_command_powershell) : "";
      pre.textContent = cmd;
      pre.style.display = cmd ? "block" : "none";
      cp.style.display = cmd ? "inline-block" : "none";
    } else {
      av.textContent = "Status: gesperrt";
      lm.style.display = "block";
      rs.innerHTML = "";
      var rrs = d.safe_final_render_handoff_reasons;
      if (rrs && rrs.length) {
        rrs.forEach(function(x) {
          var li = document.createElement("li");
          li.textContent = String(x);
          rs.appendChild(li);
        });
        rs.style.display = "block";
      } else {
        rs.style.display = "none";
      }
      note.textContent = "";
      note.style.display = "none";
      warn.textContent = "";
      warn.style.display = "none";
      pre.textContent = "";
      pre.style.display = "none";
      cp.style.display = "none";
    }
  }

  function fdFpApplyFinalRenderInputChecklist(d) {
    var badge = document.getElementById("fp-final-render-input-checklist-status");
    var host = document.getElementById("fp-final-render-input-items");
    var nx = document.getElementById("fp-final-render-input-next-action");
    if (!badge || !host || !nx) return;
    var cs = String((d && d.final_render_input_checklist_status) || "pending").toLowerCase();
    var bl = (d && d.final_render_input_checklist_label) ? String(d.final_render_input_checklist_label) : "Ausstehend";
    badge.textContent = bl;
    badge.setAttribute("data-fr-input-checklist-marker", cs);
    var bcls = "fp-fr-input-badge ";
    if (cs === "ready") bcls += "fp-fr-input-badge--ready";
    else if (cs === "warning") bcls += "fp-fr-input-badge--warning";
    else if (cs === "blocked") bcls += "fp-fr-input-badge--blocked";
    else bcls += "fp-fr-input-badge--pending";
    badge.className = bcls;
    host.innerHTML = "";
    var items = d && d.final_render_input_items;
    if (items && items.length) {
      items.forEach(function(it) {
        host.appendChild(fdFpBuildFinalRenderInputRow(it));
      });
    }
    nx.textContent = (d && d.final_render_input_next_action) ? String(d.final_render_input_next_action) : "";
  }

  var FD_DASHBOARD_MANUAL_RESET_KEY = "fd_dashboard_manual_reset";
  var FD_EXEC_NEXT_TARGET_KEY = "fd_exec_next_target_v1";
  var FD_VG_FALLBACK_SIGNALS = ["placeholder", "fallback", "dummy", "no_assets", "no_existing_video_asset", "cinematic_placeholder", "audio_missing_silent_render", "voice_mode_fallback", "no_elevenlabs_key"];
  var FD_VG_RENDER_LAYER_PLACEHOLDER_SIGNALS = ["ba266_cinematic_placeholder_applied", "audio_missing_silent_render"];

  /** BA 32.80 — Server-Status hat Vorrang vor reinem Warning-Substring-Match. */
  function fdVgVideoGenerateRunStatusFromPayload(j) {
    if (!j || j.video_generate_run_status == null) return "";
    return String(j.video_generate_run_status).trim();
  }

  function fdVgIsOkRunFallbackPreview(j, warnJoined) {
    if (!j || !j.ok) return false;
    var rs = fdVgVideoGenerateRunStatusFromPayload(j);
    if (rs === "fallback_preview") return true;
    if (rs === "gold_mini_ready" || rs === "production_ready" || rs === "mixed_preview" || rs === "blocked") return false;
    if (rs) return false;
    return fdVgWarnTriggersFallbackPreview(j, warnJoined || "");
  }

  function fdVgEffectiveVoiceMode(j) {
    if (!j || typeof j !== "object") return null;
    var va = j.voice_artifact;
    if (va && typeof va === "object" && va.effective_voice_mode != null) {
      var e = String(va.effective_voice_mode).trim().toLowerCase();
      if (e) return e;
    }
    var ra = j.readiness_audit;
    if (ra && typeof ra === "object" && ra.effective_voice_mode != null) {
      var e2 = String(ra.effective_voice_mode).trim().toLowerCase();
      if (e2) return e2;
    }
    if (j.effective_voice_mode != null) {
      var e3 = String(j.effective_voice_mode).trim().toLowerCase();
      if (e3) return e3;
    }
    if (j.requested_voice_mode != null) {
      var e4 = String(j.requested_voice_mode).trim().toLowerCase();
      if (e4) return e4;
    }
    return null;
  }

  /** BA 32.32 — bevorzugt readiness_audit.silent_render_expected; sonst BA-32.31-Heuristik. */
  function fdVgAudioSilentIsExpectedFallback(j) {
    var ra = j && j.readiness_audit;
    if (ra && typeof ra === "object" && typeof ra.silent_render_expected === "boolean") {
      return !!ra.silent_render_expected;
    }
    return fdVgEffectiveVoiceMode(j) === "none";
  }

  /** BA 32.80b — Voice „grün“ wie Python ``_voice_escape_ok_ba3280`` (QC-Reuse). */
  function fdVgVoiceEscapeOkBa3280(j) {
    var va = j && j.voice_artifact;
    var ra = j && j.readiness_audit;
    var eff = fdVgEffectiveVoiceMode(j);
    if (eff === "none") return true;
    if (!eff && ra && String(ra.requested_voice_mode || "").trim().toLowerCase() === "none") return true;
    if (va && typeof va === "object" && va.is_dummy) {
      var req = String(va.requested_voice_mode || (ra && ra.requested_voice_mode) || "").trim().toLowerCase();
      return req === "dummy";
    }
    if (va && va.voice_ready) return true;
    if (ra && ra.voice_file_ready) return true;
    return false;
  }

  /** Entfernt harmlose Teilstrings, die ``fallback`` nur im Namen tragen (BA 32.80b). */
  function fdVgSanitizeJoinedForFallbackPreview(j, joinedLower) {
    var jn = joinedLower || "";
    if (fdVgVoiceEscapeOkBa3280(j)) {
      jn = jn.split("elevenlabs_voice_id_default_fallback").join(" ");
    }
    return jn;
  }

  /** BA 32.31 — audio_missing_silent_render zählt nur als Fallback, wenn Voice erwartet wurde (nicht ``none``). */
  function fdVgWarnTriggersFallbackPreview(j, joinedLower) {
    var jn = fdVgSanitizeJoinedForFallbackPreview(j, joinedLower || "");
    for (var i = 0; i < FD_VG_FALLBACK_SIGNALS.length; i++) {
      var s = String(FD_VG_FALLBACK_SIGNALS[i]);
      if (jn.indexOf(s) < 0) continue;
      if (s === "audio_missing_silent_render" && fdVgAudioSilentIsExpectedFallback(j)) continue;
      return true;
    }
    return false;
  }

  function fdVgRenderLayerPlaceholderHit(joinedLower, readiness, payload) {
    var jn = joinedLower || "";
    if (readiness && typeof readiness.render_used_placeholders === "boolean") {
      var ru = !!readiness.render_used_placeholders;
      if (ru && jn.indexOf("audio_missing_silent_render") >= 0 && fdVgVoiceEscapeOkBa3280(payload) && jn.indexOf("ba266_cinematic_placeholder_applied") < 0) {
        return false;
      }
      return ru;
    }
    if (jn.indexOf("ba266_cinematic_placeholder_applied") >= 0) return true;
    if (jn.indexOf("audio_missing_silent_render") >= 0 && !fdVgAudioSilentIsExpectedFallback(payload)) {
      if (fdVgVoiceEscapeOkBa3280(payload)) return false;
      return true;
    }
    return false;
  }

  /** BA 32.29 — voice_artifact hat Vorrang vor readiness_audit; sonst Warning-Signale (wie Python _voice_qc). */
  function fdVgVoiceArtifactPresent(j) {
    var va = j && j.voice_artifact;
    return !!(va && typeof va === "object" && Object.keys(va).length > 0);
  }

  function fdVgVoiceQcRowTuple(j, raQc, hasVoiceFallback) {
    if (fdVgVoiceArtifactPresent(j)) {
      var va2 = j.voice_artifact;
      var eff2 = va2.effective_voice_mode != null ? String(va2.effective_voice_mode).trim().toLowerCase() : "";
      if (!eff2) eff2 = "none";
      if (eff2 === "none") {
        return ["Echte Voice verwendet", "Nicht verfügbar", "Keine Voice ausgewählt."];
      }
      if (va2.is_dummy) {
        return ["Echte Voice verwendet", "Prüfen", "Dummy Voice verwendet."];
      }
      if (va2.voice_ready) {
        return ["Echte Voice verwendet", "OK", "Echte Voice-Datei vorhanden."];
      }
      if (va2.voice_file_path) {
        return ["Echte Voice verwendet", "Prüfen", "Voice-Datei fehlt."];
      }
      return ["Echte Voice verwendet", hasVoiceFallback ? "Prüfen" : "OK", hasVoiceFallback ? "Dummy/Fallback-Signal in warnings" : "keine Voice-Fallback-Signale erkannt"];
    }
    var raV = raQc && typeof raQc === "object" ? raQc : {};
    var effR = raV.effective_voice_mode != null ? String(raV.effective_voice_mode).trim().toLowerCase() : "";
    if (effR === "none") {
      return ["Echte Voice verwendet", "Nicht verfügbar", "Keine Voice ausgewählt."];
    }
    if (raV.voice_is_dummy === true) {
      return ["Echte Voice verwendet", "Prüfen", "Dummy Voice verwendet."];
    }
    if (raV.voice_file_ready === true && !raV.voice_is_dummy) {
      return ["Echte Voice verwendet", "OK", "Echte Voice-Datei vorhanden."];
    }
    if (raV.voice_file_path_present === true && raV.voice_file_ready !== true) {
      return ["Echte Voice verwendet", "Prüfen", "Voice-Datei fehlt."];
    }
    return ["Echte Voice verwendet", hasVoiceFallback ? "Prüfen" : "OK", hasVoiceFallback ? "Dummy/Fallback-Signal in warnings" : "keine Voice-Fallback-Signale erkannt"];
  }

  function fdVgWarnJoinedLower(warnings) {
    try { return (warnings || []).map(function(x) { return String(x || ""); }).join(" ").toLowerCase(); } catch (eW) { return ""; }
  }

  function fdVgHasAnySignal(joinedLower, signals) {
    if (!joinedLower) return false;
    for (var i = 0; i < signals.length; i++) {
      if (joinedLower.indexOf(String(signals[i])) >= 0) return true;
    }
    return false;
  }

  function fdDashboardManualResetActive() {
    try { return localStorage.getItem(FD_DASHBOARD_MANUAL_RESET_KEY) === "1"; } catch (e) { return false; }
  }

  function fdClearDashboardManualResetFlag() {
    try { localStorage.removeItem(FD_DASHBOARD_MANUAL_RESET_KEY); } catch (e) {}
  }

  function fdSetDashboardManualResetFlag() {
    try { localStorage.setItem(FD_DASHBOARD_MANUAL_RESET_KEY, "1"); } catch (e) {}
  }

  function fdSetExecNextTarget(targetId) {
    var tid = String(targetId || "").trim();
    if (!tid) tid = "fd-video-generate-url";
    try { localStorage.setItem(FD_EXEC_NEXT_TARGET_KEY, tid); } catch (e) {}
    var btn = document.getElementById("fp-exec-next-step-btn");
    if (btn) btn.setAttribute("data-fd-exec-next-target", tid);
  }

  function fdGetExecNextTarget() {
    try {
      var tid = localStorage.getItem(FD_EXEC_NEXT_TARGET_KEY);
      return tid ? String(tid) : "fd-video-generate-url";
    } catch (e) {
      return "fd-video-generate-url";
    }
  }

  function fdExecSetNextStep(text, targetId, hint) {
    var exNx = document.getElementById("fp-exec-next-step-short");
    var hNext = document.getElementById("fp-exec-hint-next");
    if (exNx) {
      var s = String(text || "").trim();
      exNx.textContent = s ? (s.length > 72 ? s.slice(0, 72) + "…" : s) : "Gib eine URL ein und starte Video generieren.";
      exNx.setAttribute("title", s || "");
    }
    if (hNext) hNext.textContent = String(hint || "");
    fdSetExecNextTarget(targetId || "fd-video-generate-url");
  }

  function fdSetGuidedFlowVideoGenerateState(st, nextAction) {
    var host = document.getElementById("fd-guided-flow-steps");
    var nx = document.getElementById("fd-guided-flow-next-action");
    var lb = document.getElementById("fd-guided-flow-next-label");
    if (!host || !nx || !lb) return;
    host.innerHTML = "";
    var steps = [
      { id: "video_input", order: 1, label: "URL eingeben", detail: "Einen Artikel/Video-Link einfügen", status: (st === "running" || st === "ok" || st === "blocked") ? "done" : "active" },
      { id: "video_generate", order: 2, label: "Video generieren", detail: "Startet den URL→Final-Lauf (BA 32.3)", status: st === "running" ? "active" : (st === "ok" ? "done" : (st === "blocked" ? "blocked" : "pending")) },
      { id: "video_check", order: 3, label: "Ergebnis prüfen", detail: "Pfade, Warnungen und Video-Output prüfen", status: st === "ok" ? "active" : (st === "blocked" ? "active" : "pending") },
    ];
    steps.forEach(function(step) {
      var div = document.createElement("div");
      div.className = "fd-guided-flow-step";
      div.innerHTML =
        '<div class="fd-guided-flow-step-num">Schritt ' + String(step.order) + '</div>' +
        '<div class="fd-guided-flow-step-label">' + String(step.label).replace(/</g, "&lt;") + '</div>' +
        (step.detail ? '<div class="fd-guided-flow-step-detail">' + String(step.detail).replace(/</g, "&lt;") + '</div>' : '') +
        '<span class="' + fdGuidedStatusBadgeClass(step.status) + '">' + fdGuidedStatusLabel(step.status) + '</span>';
      host.appendChild(div);
    });
    lb.textContent = "BA 32.3 — URL → Video";
    nx.textContent = nextAction || "—";
  }

  function fdUpdateVideoGenerateExecutiveState(payload, phase) {
    var j = payload || null;
    if (phase === "neutral") {
      var exRun0 = document.getElementById("fp-exec-latest-run");
      if (exRun0) exRun0.textContent = "Kein aktiver Run";
      var exFs0 = document.getElementById("fp-exec-fresh-status");
      if (exFs0) exFs0.textContent = "Kein angezeigter Stand";
      fdExecSetNextStep("Gib eine URL ein und starte Video generieren.", "fd-video-generate-url", "");
      fdSetGuidedFlowVideoGenerateState("neutral", "Gib eine URL ein und starte Video generieren.");
      return;
    }
    if (String(phase || "").toLowerCase() === "running") {
      fdRenderVideoGenerateOperatorResult({ ok: false, run_id: "", blocking_reasons: [], warnings: [] }, "running");
    }
    var isRunning = phase === "running";
    if (isRunning) {
      var exRun = document.getElementById("fp-exec-latest-run");
      if (exRun) exRun.textContent = "Video läuft …";
      var exFs = document.getElementById("fp-exec-fresh-status");
      if (exFs) exFs.textContent = "Video-Status: läuft";
      fdExecSetNextStep("Video wird erzeugt … warte auf Ergebnis.", "fd-video-generate-result", "Nach Abschluss: Ergebnis prüfen");
      fdSetGuidedFlowVideoGenerateState("running", "Warte auf den Abschluss der Video-Generierung");
      return;
    }
    var ok = !!(j && j.ok);
    var rid = j && j.run_id ? String(j.run_id) : "";
    var blocking = (j && j.blocking_reasons && j.blocking_reasons.length) ? j.blocking_reasons : [];
    var warnings = (j && j.warnings && j.warnings.length) ? j.warnings : [];
    var warnJoined = fdVgWarnJoinedLower(warnings);
    var isFallbackPreview = ok && fdVgIsOkRunFallbackPreview(j, warnJoined);
    var exRun2 = document.getElementById("fp-exec-latest-run");
    if (exRun2) exRun2.textContent = rid ? ("Letzter Videolauf: " + rid) : "Kein aktiver Run";
    var exFs2 = document.getElementById("fp-exec-fresh-status");
    if (exFs2) exFs2.textContent = ok ? (isFallbackPreview ? "Video-Status: Fallback-Preview erstellt" : "Video-Status: fertig") : (blocking && blocking.length ? "Video-Status: blockiert" : "Video-Status: beendet");
    if (ok) {
      if (isFallbackPreview) {
        fdExecSetNextStep("Fallback-Preview erstellt. Provider/Assets prüfen oder Preview öffnen.", "fd-video-generate-result", "");
        fdSetGuidedFlowVideoGenerateState("ok", "Provider/Assets prüfen oder Preview öffnen, dann Ergebnis validieren");
      } else {
        fdExecSetNextStep("Video-Generierung abgeschlossen. Prüfe Ergebnis, Pfade und Warnungen.", "fd-video-generate-result", "");
        fdSetGuidedFlowVideoGenerateState("ok", "Ergebnis prüfen (JSON, Pfade, Warnungen) und final_video.mp4 validieren");
      }
    } else if (blocking && blocking.length) {
      fdExecSetNextStep("Video konnte nicht erzeugt werden. Prüfe Blocker im Ergebnisbereich.", "fd-video-generate-result", "");
      fdSetGuidedFlowVideoGenerateState("blocked", "Blocker prüfen und beheben, dann erneut starten");
    } else {
      fdExecSetNextStep("Video-Lauf beendet. Prüfe Ergebnis und Warnungen.", "fd-video-generate-result", "");
      fdSetGuidedFlowVideoGenerateState("blocked", "Ergebnis prüfen und ggf. erneut starten");
    }
  }

  function fdFpResetOperatorReviewNeutral() {
    var badge = document.getElementById("fp-review-decision-badge");
    var ul = document.getElementById("fp-review-reasons");
    var nx = document.getElementById("fp-review-next-action");
    if (badge) {
      badge.textContent = "Ausstehend";
      badge.setAttribute("data-review-decision-marker", "pending");
      badge.className = "fp-review-badge fp-review-badge--pending";
    }
    if (ul) ul.innerHTML = "";
    if (nx) nx.textContent = "Nach einem Vorschau-Prüflauf erscheinen hier Hinweise.";
  }

  function fdResetDashboardView() {
    fdSetDashboardManualResetFlag();
    fdApplyDashboardNeutralView();
    var eb = document.getElementById("error-bar");
    if (eb) {
      eb.textContent = "";
      eb.classList.remove("visible");
    }
  }

  function fdApplyDashboardNeutralView() {
    fdClearVideoGenerateForm();
    var tEl = document.getElementById("fp-dry-topic");
    var uEl = document.getElementById("fp-dry-url");
    var dEl = document.getElementById("fp-dry-duration");
    var mEl = document.getElementById("fp-dry-max-scenes");
    if (tEl) tEl.value = "";
    if (uEl) uEl.value = "";
    if (dEl) dEl.value = "45";
    if (mEl) mEl.value = "6";
    var dst = document.getElementById("fp-dry-run-status");
    if (dst) {
      dst.textContent = "";
      dst.classList.remove("intake-status-err", "intake-status-success");
    }
    var dres = document.getElementById("fp-dry-run-result");
    if (dres) {
      dres.textContent = "";
      dres.style.display = "none";
      dres.classList.add("out-empty");
    }
    var handoff = document.getElementById("fp-dry-run-handoff");
    if (handoff) handoff.style.display = "none";
    var hn = document.getElementById("fp-handoff-note");
    var hw = document.getElementById("fp-handoff-warning");
    var hpre = document.getElementById("fp-dry-run-handoff-ps");
    if (hn) hn.textContent = "";
    if (hw) hw.textContent = "";
    if (hpre) hpre.textContent = "";
    var dbtn = document.getElementById("fp-btn-start-dry-run");
    if (dbtn) {
      var dl = dbtn.getAttribute("data-label") || "Struktur-Test starten";
      dbtn.textContent = dl;
      dbtn.disabled = false;
      dbtn.classList.remove("is-loading", "is-success", "is-error");
    }
    var rfb = document.getElementById("fp-btn-refresh");
    if (rfb) {
      rfb.disabled = false;
      rfb.classList.remove("is-loading", "is-success", "is-error");
      var rlab = rfb.getAttribute("data-label") || "Status aktualisieren";
      rfb.textContent = rlab;
    }
    var sst = document.getElementById("fp-snapshot-status");
    if (sst) {
      sst.textContent = "Ansicht zurückgesetzt — wähle „Status aktualisieren“, um den Projektstand aus output/ neu einzulesen.";
      sst.classList.remove("intake-status-err");
    }
    var out = document.getElementById("out-fp-snapshot");
    if (out) {
      out.textContent = "Kein angezeigter Stand. Dateien im Ordner output/ bleiben erhalten. Nutze „Status aktualisieren“ für den letzten Lauf, einen Struktur-Test oder „Video generieren“.";
      out.classList.add("out-empty");
    }
    fdFpResetPreviewPowerNeutral();
    fdFpResetOperatorReviewNeutral();
    fdFpResetFinalRenderGateNeutral();
    fdFpResetFinalRenderInputChecklistNeutral();
    fdFpResetSafeFinalRenderHandoffNeutral();
    fdFpResetGuidedFlowNeutral();
    var glb = document.getElementById("fd-guided-flow-next-label");
    var gnx = document.getElementById("fd-guided-flow-next-action");
    if (glb) glb.textContent = "";
    if (gnx) gnx.textContent = "Gib eine URL ein und starte Video generieren.";
    var badge = document.getElementById("fp-readiness-badge");
    var scEl = document.getElementById("fp-readiness-score");
    if (badge) {
      badge.textContent = "OFFEN";
      badge.className = "fp-readiness-badge fp-readiness-unknown";
    }
    if (scEl) scEl.textContent = "Noch kein Bewertungsstand — „Status aktualisieren“ oder Struktur-Test.";
    var exFs = document.getElementById("fp-exec-fresh-status");
    if (exFs) exFs.textContent = "Kein angezeigter Stand";
    var exScore = document.getElementById("fp-exec-readiness-score");
    if (exScore) exScore.textContent = "Nicht bewertet";
    var exRun = document.getElementById("fp-exec-latest-run");
    if (exRun) exRun.textContent = "Kein aktiver Run";
    var exNx = document.getElementById("fp-exec-next-step-short");
    if (exNx) {
      exNx.textContent = "Gib eine URL ein und starte Video generieren.";
      exNx.setAttribute("title", "");
    }
    fdSetExecNextTarget("fd-video-generate-url");
    var hFresh = document.getElementById("fp-exec-hint-fresh");
    if (hFresh) hFresh.textContent = "Nur die Ansicht — Dateien bleiben auf der Festplatte.";
    var hScore = document.getElementById("fp-exec-hint-score");
    if (hScore) hScore.textContent = "Wird nach „Status aktualisieren“ berechnet";
    var hRun = document.getElementById("fp-exec-hint-run");
    if (hRun) hRun.textContent = "";
    var hNext = document.getElementById("fp-exec-hint-next");
    if (hNext) hNext.textContent = "";
    var exBtn = document.getElementById("fp-exec-next-step-btn");
    if (exBtn) exBtn.disabled = false;
    var nextBox = document.getElementById("fp-next-step-box");
    var nextText = document.getElementById("fp-operator-next-step");
    if (nextBox && nextText) {
      nextText.textContent = "Gib eine URL ein und starte Video generieren.";
      nextBox.className = "fp-next-step-box fp-next-step--neutral";
    }
    var pr = document.getElementById("fp-path-rows");
    if (pr) pr.innerHTML = "";
    fdFpFillReasonList("fp-blocking-list", "Freigabe blockiert (Review)", []);
    fdFpFillReasonList("fp-readiness-list", "Readiness zur Prüfung", []);
    fdFpFillReasonList("fp-scan-warnings-list", "Pfade und Dateien (Review)", []);
  }

  async function fdLoadFreshPreviewSnapshot() {
    var st = document.getElementById("fp-snapshot-status");
    var out = document.getElementById("out-fp-snapshot");
    if (!st || !out) return;
    if (fdDashboardManualResetActive()) {
      return;
    }
    try {
      if (isKillSwitchActive()) {
        st.textContent = "Kill Switch aktiv — Fresh-Preview-Snapshot übersprungen.";
        fdFpResetFinalRenderGateNeutral();
        fdFpResetFinalRenderInputChecklistNeutral();
        fdFpResetSafeFinalRenderHandoffNeutral();
        fdFpResetGuidedFlowNeutral();
        return;
      }
      const r = await fetch("/founder/dashboard/fresh-preview/snapshot", { method: "GET" });
      if (!r.ok) {
        st.textContent = "Fresh Preview Snapshot: HTTP " + r.status;
        st.classList.add("intake-status-err");
        fdFpResetPreviewPowerNeutral();
        fdFpResetFinalRenderGateNeutral();
        fdFpResetFinalRenderInputChecklistNeutral();
        fdFpResetSafeFinalRenderHandoffNeutral();
        fdFpResetGuidedFlowNeutral();
        return;
      }
      const d = await r.json();
      st.textContent = "Projektstand geladen · read-only · " + (d.fresh_preview_snapshot_version || "ba31_0_v1");
      st.classList.remove("intake-status-err");
      var rs = String(d.readiness_status || "").toLowerCase();
      var badge = document.getElementById("fp-readiness-badge");
      var scEl = document.getElementById("fp-readiness-score");
      if (badge) {
        var bl = rs === "ready" ? "READY" : (rs === "warning" ? "WARNING" : (rs === "blocked" ? "BLOCKED" : "OFFEN"));
        badge.textContent = bl;
        badge.className = "fp-readiness-badge " + (rs === "ready" ? "fp-readiness-ready" : (rs === "warning" ? "fp-readiness-warning" : (rs === "blocked" ? "fp-readiness-blocked" : "fp-readiness-unknown")));
      }
      if (scEl) scEl.textContent = d.readiness_score != null ? ("Score: " + String(d.readiness_score) + " / 100 · Readiness-Check Vorschau-Prüflauf") : "Wird nach „Status aktualisieren“ berechnet";
      fdFpUpdatePreviewPower(d);
      fdFpApplyOperatorReview(d);
      fdFpApplyFinalRenderGate(d);
      fdFpApplyFinalRenderInputChecklist(d);
      fdFpApplySafeFinalRenderHandoff(d);
      fdFpApplyGuidedFlow(d);
      var nsOp = String(d.operator_next_step || "").trim();
      var exFs = document.getElementById("fp-exec-fresh-status");
      if (exFs) exFs.textContent = d.fresh_preview_available ? "Vorschau aktiv" : "Kein Vorschau-Lauf gefunden";
      var exScore = document.getElementById("fp-exec-readiness-score");
      if (exScore) exScore.textContent = d.readiness_score != null ? String(d.readiness_score) + " / 100" : "Nicht bewertet";
      var exRun = document.getElementById("fp-exec-latest-run");
      if (exRun) exRun.textContent = d.latest_run_id || "Kein aktiver Run";
      var exNx = document.getElementById("fp-exec-next-step-short");
      if (exNx) {
        exNx.textContent = nsOp ? (nsOp.length > 72 ? nsOp.slice(0, 72) + "…" : nsOp) : "Gib eine URL ein und starte Video generieren.";
        exNx.setAttribute("title", nsOp || "");
      }
      var hFresh = document.getElementById("fp-exec-hint-fresh");
      if (hFresh) hFresh.textContent = d.fresh_preview_available ? "" : "Struktur-Test oder Status aktualisieren";
      var hScore = document.getElementById("fp-exec-hint-score");
      if (hScore) hScore.textContent = d.readiness_score != null ? "" : "Wird nach „Status aktualisieren“ berechnet";
      var hRun = document.getElementById("fp-exec-hint-run");
      if (hRun) hRun.textContent = d.latest_run_id ? "" : "Der zuletzt erkannte Run erscheint hier";
      var hNext = document.getElementById("fp-exec-hint-next");
      if (hNext) hNext.textContent = nsOp ? "" : "Aus Projektstand und Readiness abgeleitet";
      var nextBox = document.getElementById("fp-next-step-box");
      var nextText = document.getElementById("fp-operator-next-step");
      if (nextBox && nextText) {
        nextText.textContent = nsOp || "Gib eine URL ein und starte Video generieren.";
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
        pr.appendChild(fdFpBuildPathRow("Prüfbericht (OPEN_PREVIEW_SMOKE.md)", d.open_preview_smoke_report_path));
      }
      fdFpFillReasonList("fp-blocking-list", "Freigabe blockiert (Review)", d.blocking_reasons);
      fdFpFillReasonList("fp-readiness-list", "Readiness zur Prüfung", d.readiness_reasons);
      fdFpFillReasonList("fp-scan-warnings-list", "Pfade und Dateien (Review)", d.warnings);
      var lines = [];
      lines.push("Vorschau-Prüflauf — Kurzüberblick (Details oben)");
      lines.push("- Readiness: " + (d.readiness_status || "—") + " · Score: " + (d.readiness_score != null ? d.readiness_score : "—"));
      lines.push("- fresh_preview_available: " + (d.fresh_preview_available ? "ja" : "nein"));
      lines.push("- latest_run_id: " + (d.latest_run_id || "—"));
      lines.push("- Artefakt-Flags: script " + (d.script_json_present ? "ja" : "nein") + " · pack " + (d.scene_asset_pack_present ? "ja" : "nein") + " · manifest " + (d.asset_manifest_present ? "ja" : "nein") + " · summary " + (d.preview_smoke_summary_present ? "ja" : "nein") + " · open_me " + (d.open_preview_smoke_report_present ? "ja" : "nein"));
      out.textContent = lines.join("\\n");
      out.classList.remove("out-empty");
    } catch (e) {
      st.textContent = "Fresh Preview Snapshot: " + String(e && e.message ? e.message : e);
      st.classList.add("intake-status-err");
      fdFpResetPreviewPowerNeutral();
      fdFpResetFinalRenderGateNeutral();
      fdFpResetFinalRenderInputChecklistNeutral();
      fdFpResetSafeFinalRenderHandoffNeutral();
      fdFpResetGuidedFlowNeutral();
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

  function fdBindExecNextStepButton() {
    var btn = document.getElementById("fp-exec-next-step-btn");
    if (!btn) return;
    try {
      var tid0 = btn.getAttribute("data-fd-exec-next-target") || fdGetExecNextTarget();
      btn.setAttribute("data-fd-exec-next-target", tid0);
    } catch (eTid) {}
    btn.addEventListener("click", function(ev) {
      ev.preventDefault();
      var tid = btn.getAttribute("data-fd-exec-next-target") || fdGetExecNextTarget();
      if (!tid) return;
      openPanelAndScroll(null, tid);
    });
  }

  function fdBootstrapDashboard() {
    try {
      console.log("FD_BOOTSTRAP_START");
      showError("FD_BOOTSTRAP_START");
    } catch (eBootLog) {}
    fdBindSidebarNav();
    fdBindExecNextStepButton();
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
        await withActionButton(btn, "coll-legacy-debug", "coll-input-panel", async function() {
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
    await withActionButton(btn, "coll-legacy-debug", "coll-full-pipeline", runFullPipelineOrchestrator);
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

  $("btn-storyboard-plan").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-storyboard", "storyboard-plan-summary", async function() {
      await runStoryboardOnlyInternal();
    });
  };

  $("btn-storyboard-readiness").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-storyboard-readiness", "storyboard-readiness-summary", async function() {
      await runStoryboardReadinessOnlyInternal();
    });
  };

  $("btn-asset-generation-plan").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-asset-generation-plan", "asset-generation-plan-summary", async function() {
      await runAssetGenerationPlanOnlyInternal();
    });
  };

  $("btn-asset-execution-stub").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-asset-execution-stub", "asset-execution-stub-summary", async function() {
      await runAssetExecutionStubOnlyInternal();
    });
  };

  $("btn-openai-image-live").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-openai-image-live", "openai-image-live-summary", async function() {
      await runOpenAIImageLiveOnlyInternal();
    });
  };

  $("btn-elevenlabs-voice-live").onclick = async function(){
    var btn = this;
    clearWarnings();
    await withActionButton(btn, "coll-elevenlabs-voice-live", "elevenlabs-voice-live-summary", async function() {
      await runElevenLabsVoiceLiveOnlyInternal();
    });
  };

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
      lastStoryboard = pack.lastStoryboard || null;
      lastStoryboardReadiness = pack.lastStoryboardReadiness || null;
      lastAssetPlan = pack.lastAssetPlan || null;
      lastAssetExecutionStub = pack.lastAssetExecutionStub || null;
      lastOpenAIImageLive = pack.lastOpenAIImageLive || null;
      lastElevenLabsVoiceLive = pack.lastElevenLabsVoiceLive || null;
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
  if (fdDashboardManualResetActive()) {
    fdApplyDashboardNeutralView();
  } else {
    fdLoadFreshPreviewSnapshot();
  }
    var lpBtn = document.getElementById("lp-btn-run-mini");
    if (lpBtn) {
      lpBtn.addEventListener("click", async function() {
        try { await fdRunLocalPreviewMiniFixture(); } catch (eLp) {}
      });
    }
    var fpRef = document.getElementById("fp-btn-refresh");
    if (fpRef) {
      fpRef.addEventListener("click", async function() {
        fdClearDashboardManualResetFlag();
        try { await fdLoadFreshPreviewSnapshot(); } catch (eFp) {}
      });
    }
    var fdDashReset = document.getElementById("fd-btn-dashboard-reset");
    if (fdDashReset) {
      fdDashReset.addEventListener("click", function() {
        fdResetDashboardView();
      });
    }
    var fpDry = document.getElementById("fp-btn-start-dry-run");
    if (fpDry) {
      fpDry.addEventListener("click", async function() {
        try { await fdStartFreshPreviewDryRun(); } catch (eDry) {}
      });
    }
    var vgSub = document.getElementById("fd-video-generate-submit");
    if (vgSub) {
      vgSub.addEventListener("click", async function() {
        try { await fdSubmitVideoGenerate(); } catch (eVg) {}
      });
    }
    var vgClr = document.getElementById("fd-video-generate-clear");
    if (vgClr) {
      vgClr.addEventListener("click", function() {
        fdClearVideoGenerateForm();
      });
    }
    var vgLive = document.getElementById("fd-vg-live-assets");
    if (vgLive) {
      vgLive.addEventListener("change", function() {
        try { fdApplyVideoGenerateAssetsModeHint(); } catch (eHint) {}
        try { fdApplyVideoGenerateProviderReadinessHint(); } catch (eHint3) {}
        try { fdApplyVideoGeneratePreflight(); } catch (ePf) {}
        try { fdRenderFixChecklistFromProviderReadiness(FD_VG_PROVIDER_READINESS); } catch (eFix) {}
        try { fdApplyRealProductionSmokeChecklist(); } catch (eRs) {}
        try { fdApplyInline422Hint(); } catch (e422) {}
      });
    }
    var vgVoice = document.getElementById("fd-vg-voice-mode");
    if (vgVoice) {
      vgVoice.addEventListener("change", function() {
        try { fdApplyVideoGeneratePreflight(); } catch (ePf2) {}
        try { fdApplyVideoGenerateProviderReadinessHint(); } catch (eHint4) {}
        try { fdRenderFixChecklistFromProviderReadiness(FD_VG_PROVIDER_READINESS); } catch (eFix2) {}
        try { fdApplyRealProductionSmokeChecklist(); } catch (eRs2) {}
        try { fdApplyInline422Hint(); } catch (e422b) {}
      });
    }
    var vgCosts = document.getElementById("fd-vg-confirm-costs");
    if (vgCosts) {
      vgCosts.addEventListener("change", function() {
        try { fdApplyInline422Hint(); } catch (e422c) {}
        try { fdApplyVideoGeneratePreflight(); } catch (ePf3) {}
        try { fdApplyRealProductionSmokeChecklist(); } catch (eRs3) {}
      });
    }
    var vgThumbPack = document.getElementById("fd-vg-generate-thumbnail-pack");
    if (vgThumbPack) {
      vgThumbPack.addEventListener("change", function() {
        try { fdVgDispatchInputChange(vgThumbPack); } catch (eTb) {}
        try { fdApplyInline422Hint(); } catch (e422tp) {}
        try { fdApplyVideoGeneratePreflight(); } catch (ePftp) {}
      });
    }
    var vgDevKeys = [
      document.getElementById("fd-vg-dev-openai-api-key"),
      document.getElementById("fd-vg-dev-elevenlabs-api-key"),
      document.getElementById("fd-vg-dev-runway-api-key"),
      document.getElementById("fd-vg-dev-leonardo-api-key")
    ];
    vgDevKeys.forEach(function(inp) {
      if (!inp) return;
      inp.addEventListener("input", function() {
        try { fdVgApplyDevKeyOverrideHint(); } catch (eDk) {}
      });
    });
    try { fdApplyVideoGenerateAssetsModeHint(); } catch (eHint2) {}
    try { fdLoadVideoGenerateProviderReadiness(); } catch (ePr) {}
    try { fdApplyInline422Hint(); } catch (e422d) {}
    try { fdVgApplyDevKeyOverrideHint(); } catch (eDk0) {}
    try { fdVgRenderLastRunSummary(fdVgLoadLastRunSummary()); } catch (eLast) {}
    var vgPrRef = document.getElementById("fd-vg-provider-refresh");
    if (vgPrRef) {
      vgPrRef.addEventListener("click", async function() {
        try { await fdLoadVideoGenerateProviderReadiness(); } catch (ePr2) {}
      });
    }
    var vgGoCosts = document.getElementById("fd-vg-go-confirm-costs");
    if (vgGoCosts) {
      vgGoCosts.addEventListener("click", function() {
        try { fdScrollToConfirmCosts(); } catch (eSc) {}
      });
    }
    var vgForget = document.getElementById("fd-vg-forget-last-run");
    if (vgForget) {
      vgForget.addEventListener("click", function() {
        try { fdVgForgetLastRunSummary(); } catch (eF) {}
        try { FD_VG_LAST_VIDEO_GENERATE = null; } catch (eF2) {}
        try { fdVgRenderLastRunSummary(null); } catch (eF3) {}
        try { fdApplyRealProductionSmokeChecklist(); } catch (eF4) {}
      });
    }
    var vgPreset = document.getElementById("fd-vg-real-smoke-preset");
    if (vgPreset) {
      vgPreset.addEventListener("click", function() {
        try { fdApplyRealProductionSmokePreset(); } catch (ePs) {}
      });
    }
    var vgOaiMini = document.getElementById("fd-vg-openai-image-mini-preset");
    if (vgOaiMini) {
      vgOaiMini.addEventListener("click", function() {
        try { fdApplyOpenAiImageMiniSmokePreset(); } catch (eOm) {}
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
    var fpCopySafeFr = document.getElementById("fp-safe-final-render-copy");
    if (fpCopySafeFr) {
      fpCopySafeFr.addEventListener("click", function() {
        var pre = document.getElementById("fp-safe-final-render-cli");
        var t = pre && pre.textContent ? pre.textContent.trim() : "";
        if (t) fdFpCopyToClipboard(t, fpCopySafeFr);
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
