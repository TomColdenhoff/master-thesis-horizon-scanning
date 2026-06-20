"""Human review UI (task 29, updated tasks 30c/30d) — returns HTML for signal review."""

_HTML = """\
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>Horizon Scanning — Signal Review</title>
<style>
  body { font-family: sans-serif; max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
  h1   { font-size: 1.3rem; margin-bottom: 1rem; }
  #count { color: #555; font-size: 0.9rem; margin-bottom: 0.75rem; }

  /* Legend */
  #legend {
    border: 1px solid #e5e7eb; border-radius: 6px;
    margin-bottom: 1.25rem; overflow: hidden;
  }
  #legend summary {
    cursor: pointer; padding: 0.6rem 0.9rem;
    font-size: 0.85rem; font-weight: bold; color: #374151;
    background: #f9fafb; user-select: none; list-style: none;
  }
  #legend summary::-webkit-details-marker { display: none; }
  #legend summary::before { content: "\\25b6\\fe0e\\2002"; font-size: 0.7rem; }
  #legend[open] summary::before { content: "\\25bc\\fe0e\\2002"; }
  #legend-body {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 1rem 1.5rem; padding: 0.9rem; background: #fff;
  }
  .legend-section h4 { margin: 0 0 0.5rem; font-size: 0.8rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
  .legend-row { display: flex; gap: 0.5rem; margin-bottom: 0.4rem; align-items: baseline; }
  .legend-badge {
    flex-shrink: 0; display: inline-block; padding: 0.15rem 0.45rem;
    border-radius: 4px; font-size: 0.72rem; font-weight: bold;
    background: #e0e7ff; color: #3730a3; min-width: 80px; text-align: center;
  }
  .legend-badge.mod  { background: #fce7f3; color: #9d174d; }
  .legend-badge.cert { background: #fef9c3; color: #854d0e; }
  .legend-badge.sec  { background: #f3e8ff; color: #6b21a8; font-size: 0.68rem; min-width: unset; }
  .legend-desc { font-size: 0.8rem; color: #374151; }

  /* Filter bar */
  #filters {
    display: flex; gap: 0.75rem; flex-wrap: wrap;
    margin-bottom: 1.25rem; align-items: center;
  }
  #filters label { font-size: 0.85rem; color: #374151; }
  #filters select, #filters input {
    font-size: 0.85rem; padding: 0.3rem 0.5rem;
    border: 1px solid #d1d5db; border-radius: 4px; background: #fff;
  }
  #filter-count { font-size: 0.8rem; color: #6b7280; margin-left: auto; }

  .card {
    border: 1px solid #ccc; border-radius: 6px;
    padding: 1rem; margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
  }
  .card-header {
    display: flex; justify-content: space-between;
    align-items: flex-start; gap: 0.5rem; margin-bottom: 0.6rem;
  }
  .card-title   { font-weight: bold; font-size: 1rem; }
  .card-meta    { font-size: 0.8rem; color: #555; margin-top: 0.2rem; }
  .badge {
    display: inline-block; padding: 0.2rem 0.5rem;
    border-radius: 4px; font-size: 0.75rem; font-weight: bold;
  }
  .badge-score     { background: #dbeafe; color: #1e40af; }
  .badge-stream    { background: #dcfce7; color: #166534; }
  .badge-certainty { background: #fef9c3; color: #854d0e; font-weight: normal; }
  .badge-sector    { background: #f3e8ff; color: #6b21a8; font-weight: normal; }

  /* Client action box */
  .action-box {
    background: #fff7ed; border-left: 4px solid #f97316;
    padding: 0.6rem 0.8rem; margin-bottom: 0.75rem;
    font-size: 0.875rem; color: #1e293b; border-radius: 0 4px 4px 0;
  }
  .action-box strong { color: #c2410c; }

  /* Sectors row */
  .sectors { margin-bottom: 0.6rem; }
  .sector-item { display: inline-block; margin: 0.2rem 0.3rem 0.2rem 0; }
  .sector-reason { font-size: 0.76rem; color: #6b7280; margin-top: 0.15rem; }

  .summary { margin: 0.5rem 0 0.75rem; font-style: italic; color: #374151; }

  .chunk-block {
    background: #f8fafc; border-left: 3px solid #3b82f6;
    padding: 0.6rem 0.8rem; margin-bottom: 0.5rem;
    font-size: 0.85rem; line-height: 1.6; white-space: pre-wrap; color: #1e293b;
  }
  .chunk-item { margin-bottom: 0.75rem; }
  .chunk-link {
    display: inline-block; font-size: 0.78rem; color: #3b82f6;
    text-decoration: none; margin-bottom: 0.25rem;
  }
  .chunk-link:hover { text-decoration: underline; }
  .chunk-score { font-size: 0.75rem; color: #6b7280; margin-left: 0.4rem; }
  details > summary {
    cursor: pointer; font-size: 0.8rem; color: #3b82f6;
    margin-bottom: 0.4rem; user-select: none;
  }

  table  { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 0.75rem; }
  th, td { text-align: left; padding: 0.3rem 0.5rem; border-bottom: 1px solid #e5e7eb; }
  th     { color: #6b7280; font-weight: normal; width: 30%; }
  td     { color: #111; }
  .empty { color: #9ca3af; font-style: italic; }

  /* Tabs */
  .tabs { display: flex; gap: 0; margin-bottom: 1.25rem; border-bottom: 2px solid #e5e7eb; }
  .tab {
    padding: 0.5rem 1.2rem; font-size: 0.9rem; font-weight: bold;
    cursor: pointer; border: none; background: none; color: #6b7280;
    border-bottom: 2px solid transparent; margin-bottom: -2px;
  }
  .tab.active { color: #1d4ed8; border-bottom-color: #1d4ed8; }
  .tab:hover:not(.active) { color: #374151; }

  /* Review status badge on reviewed cards */
  .status-badge {
    display: inline-block; padding: 0.2rem 0.6rem;
    border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-left: 0.4rem;
  }
  .status-strong   { background: #dcfce7; color: #166534; }
  .status-weak     { background: #fef9c3; color: #854d0e; }
  .status-unsure   { background: #e0e7ff; color: #3730a3; }
  .status-discarded{ background: #fee2e2; color: #991b1b; }

  .actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }
  button {
    padding: 0.35rem 0.9rem; border: none; border-radius: 4px;
    cursor: pointer; font-size: 0.82rem; font-weight: bold;
  }
  .btn-strong  { background: #16a34a; color: #fff; }
  .btn-weak    { background: #ca8a04; color: #fff; }
  .btn-unsure  { background: #6366f1; color: #fff; }
  .btn-discard { background: #dc2626; color: #fff; }
  button:hover { opacity: 0.85; }

  /* Key-term highlight in summary */
  .summary mark { background: none; font-weight: bold; color: #1e293b; }

  #empty-state { color: #6b7280; text-align: center; padding: 3rem; }
  .hidden { display: none !important; }
</style>
</head>
<body>
<h1>Horizon Scanning — Signal Review</h1>
<div id="count"></div>

<div class="tabs">
  <button class="tab active" id="tab-unreviewed" onclick="switchTab('unreviewed')">Unreviewed <span id="tab-unreviewed-count"></span></button>
  <button class="tab" id="tab-reviewed" onclick="switchTab('reviewed')">Reviewed <span id="tab-reviewed-count"></span></button>
</div>

<details id="legend">
  <summary>Field reference — norm type, legal modality, certainty &amp; sectors</summary>
  <div id="legend-body">
    <div class="legend-section">
      <h4>Norm type</h4>
      <div class="legend-row">
        <span class="legend-badge">conduct</span>
        <span class="legend-desc">Regulates behaviour — tells someone what to do, not do, or that they may do something.</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge">competence</span>
        <span class="legend-desc">Creates a legal power — enables an authority to take binding decisions or establishes a new body.</span>
      </div>
    </div>
    <div class="legend-section">
      <h4>Legal modality</h4>
      <div class="legend-row">
        <span class="legend-badge mod">ought</span>
        <span class="legend-desc">Obligation — the subject is required to do something (<em>verplicht, moet, dient te</em>).</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge mod">ought not</span>
        <span class="legend-desc">Prohibition — the subject is forbidden from doing something (<em>verboden, mogen niet</em>).</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge mod">may</span>
        <span class="legend-desc">Permission — the subject is allowed but not required (<em>mogen, is het toegestaan</em>).</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge mod">can</span>
        <span class="legend-desc">Competence — an authority is given a power or capacity (<em>kan, heeft de bevoegdheid</em>).</span>
      </div>
    </div>
    <div class="legend-section">
      <h4>Signal certainty</h4>
      <div class="legend-row">
        <span class="legend-badge cert">committed</span>
        <span class="legend-desc">Government has formally decided or a bill has been submitted to parliament (<em>aangenomen, ingediend, treedt in werking</em>).</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge cert">proposed</span>
        <span class="legend-desc">A concrete proposal exists but is not yet decided — internet consultation open or closed, Raad van State stage (<em>wetsvoorstel in voorbereiding, internetconsultatie</em>).</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge cert">advisory</span>
        <span class="legend-desc">An intention or ambition without binding commitment — coalition agreement, research commissioned, policy letter (<em>is voornemens, streeft naar, wil inzetten op</em>).</span>
      </div>
      <div class="legend-row">
        <span class="legend-badge cert">existing</span>
        <span class="legend-desc">Describes a rule already in force — no new signal. These are filtered out of the review queue.</span>
      </div>
    </div>
    <div class="legend-section">
      <h4>Affected sectors</h4>
      <div style="display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.5rem">
        <span class="legend-badge sec">Financial services</span>
        <span class="legend-badge sec">Labour market</span>
        <span class="legend-badge sec">Housing / real estate</span>
        <span class="legend-badge sec">Energy / sustainability</span>
        <span class="legend-badge sec">Digital / IT / AI</span>
        <span class="legend-badge sec">Healthcare</span>
        <span class="legend-badge sec">Transport / logistics</span>
        <span class="legend-badge sec">Agriculture / environment</span>
        <span class="legend-badge sec">Consumer protection</span>
        <span class="legend-badge sec">Corporate / governance</span>
        <span class="legend-badge sec">Data protection / privacy</span>
        <span class="legend-badge sec">Tax / fiscal</span>
      </div>
      <span class="legend-desc">Fixed list assigned by the LLM. Each sector on a card includes a one-sentence explanation of why this signal affects it.</span>
    </div>
  </div>
</details>

<div id="filters">
  <label>Certainty:
    <select id="filter-certainty">
      <option value="">All</option>
      <option value="committed">Committed</option>
      <option value="proposed">Proposed</option>
      <option value="advisory">Advisory</option>
    </select>
  </label>
  <label>Sector:
    <select id="filter-sector">
      <option value="">All</option>
    </select>
  </label>
  <label>Search title:
    <input id="filter-search" type="text" placeholder="Filter by title or summary…" style="width:220px">
  </label>
  <span id="filter-count"></span>
</div>

<div id="app"></div>

<script>
const NORM_LABELS = {
  norm_identifier: "Norm identifier",
  norm_type:       "Norm type",
  promulgation:    "Promulgation",
  scope:           "Scope",
  conditions:      "Conditions",
  subject:         "Subject",
  legal_modality:  "Legal modality",
  act_identifier:  "Act identifier",
};

let _signals = [];
let _reviewed = [];
let _currentTab = "unreviewed";

async function load() {
  try {
    const [unreviewedRes, reviewedRes] = await Promise.all([
      fetch("/signals"),
      fetch("/signals/reviewed"),
    ]);
    if (!unreviewedRes.ok) throw new Error(`/signals: ${unreviewedRes.status}`);
    _signals  = await unreviewedRes.json();
    _reviewed = reviewedRes.ok ? await reviewedRes.json() : [];
    _populateSectorFilter();
    updateTabCounts();
    renderTab();
  } catch (e) {
    document.getElementById("app").innerHTML =
      `<p style="color:red">${e.message}</p>`;
  }
}

function updateTabCounts() {
  document.getElementById("tab-unreviewed-count").textContent =
    _signals.length ? `(${_signals.length})` : "";
  document.getElementById("tab-reviewed-count").textContent =
    _reviewed.length ? `(${_reviewed.length})` : "";
}

function switchTab(tab) {
  _currentTab = tab;
  document.getElementById("tab-unreviewed").classList.toggle("active", tab === "unreviewed");
  document.getElementById("tab-reviewed").classList.toggle("active", tab === "reviewed");
  document.getElementById("filters").style.display = tab === "unreviewed" ? "" : "none";
  renderTab();
}

function renderTab() {
  if (_currentTab === "unreviewed") render(_signals, false);
  else renderReviewed();
}

function renderReviewed() {
  const app   = document.getElementById("app");
  const count = document.getElementById("count");
  if (!_reviewed.length) {
    count.textContent = "";
    app.innerHTML = '<p id="empty-state">No reviewed signals yet.</p>';
    return;
  }
  count.textContent = `${_reviewed.length} reviewed signal(s)`;
  app.innerHTML = _reviewed.map(s => card(s, true)).join("");
  app.querySelectorAll("[data-id]").forEach(el => {
    const s = _reviewed.find(x => x.id === parseInt(el.dataset.id, 10));
    if (s) attachChunkLoader(el, s.id, s.doc_id);
  });
}

function _populateSectorFilter() {
  const seen = new Set();
  _signals.forEach(s => (s.affected_sectors || []).forEach(sec => seen.add(sec)));
  const sel = document.getElementById("filter-sector");
  [...seen].sort().forEach(sec => {
    const opt = document.createElement("option");
    opt.value = sec; opt.textContent = sec;
    sel.appendChild(opt);
  });
}

function _applyFilters() {
  const cert   = document.getElementById("filter-certainty").value;
  const sector = document.getElementById("filter-sector").value;
  const search = document.getElementById("filter-search").value.toLowerCase();

  const cards = document.querySelectorAll("[data-id]");
  let visible = 0;
  cards.forEach(card => {
    const id = parseInt(card.dataset.id, 10);
    const s = _signals.find(x => x.id === id);
    if (!s) return;
    const match =
      (!cert   || s.signal_certainty === cert) &&
      (!sector || (s.affected_sectors || []).includes(sector)) &&
      (!search || (s.onderwerp || "").toLowerCase().includes(search)
               || (s.signal_summary || "").toLowerCase().includes(search));
    card.classList.toggle("hidden", !match);
    if (match) visible++;
  });
  document.getElementById("filter-count").textContent =
    visible < cards.length ? `${visible} of ${cards.length} shown` : "";
}

["filter-certainty", "filter-sector"].forEach(id =>
  document.getElementById(id).addEventListener("change", _applyFilters)
);
document.getElementById("filter-search").addEventListener("input", _applyFilters);

function render(signals, readonly = false) {
  const app   = document.getElementById("app");
  const count = document.getElementById("count");

  if (!signals.length) {
    count.textContent = "";
    app.innerHTML = `<p id="empty-state">${readonly ? "No reviewed signals yet." : "No unreviewed signals."}</p>`;
    return;
  }

  count.textContent = readonly
    ? `${signals.length} reviewed signal(s)`
    : `${signals.length} unreviewed signal(s)`;
  app.innerHTML = signals.map(s => card(s, readonly)).join("");

  app.querySelectorAll("[data-id]").forEach(el => {
    if (!readonly) {
      el.querySelector(".btn-strong") ?.addEventListener("click", () => reviewSignal(el, "strong"));
      el.querySelector(".btn-weak")   ?.addEventListener("click", () => reviewSignal(el, "weak"));
      el.querySelector(".btn-unsure") ?.addEventListener("click", () => reviewSignal(el, "unsure"));
      el.querySelector(".btn-discard")?.addEventListener("click", () => reviewSignal(el, "discarded"));
    }
    const pool = readonly ? _reviewed : _signals;
    const s = pool.find(x => x.id === parseInt(el.dataset.id, 10));
    if (s) attachChunkLoader(el, s.id, s.doc_id);
  });
}

// Lazy-load chunks when the fold-out is first opened
function attachChunkLoader(cardEl, signalId, docId) {
  const det = cardEl.querySelector(".chunks-details");
  if (!det) return;
  let loaded = false;
  det.addEventListener("toggle", async () => {
    if (!det.open || loaded) return;
    loaded = true;
    const container = det.querySelector(".chunks-container");
    container.innerHTML = "<em style='font-size:0.8rem;color:#6b7280'>Loading…</em>";
    try {
      const res = await fetch(`/signals/${signalId}/chunks`);
      const chunks = await res.json();
      if (!chunks.length) {
        container.innerHTML = "<em style='font-size:0.8rem;color:#6b7280'>No chunks found.</em>";
        return;
      }
      container.innerHTML = chunks.map(c => {
        const text = normalize(c.chunk_text);
        const phrase = firstPhrase(text);
        const url = `/viewer/${docId}` + (phrase ? `?search=${encodeURIComponent(phrase)}` : "");
        const summary = c.signal_summary
          ? `<div style="font-size:0.78rem;color:#374151;font-style:italic;margin-bottom:0.25rem">${esc(c.signal_summary)}</div>` : "";
        return `<div class="chunk-item">
          <a class="chunk-link" href="${url}" target="_blank" rel="noopener">
            \\u2197 Open chunk ${c.chunk_index} in document
            <span class="chunk-score">${c.completeness_score}/8</span>
          </a>
          ${summary}
          <div class="chunk-block">${esc(text)}</div>
        </div>`;
      }).join("");
    } catch (e) {
      container.innerHTML = `<em style='color:red'>${e.message}</em>`;
    }
  });
}

async function reviewSignal(cardEl, status) {
  const id = parseInt(cardEl.dataset.id, 10);
  const signal = _signals.find(s => s.id === id);
  await fetch(`/signals/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  _signals = _signals.filter(s => s.id !== id);
  if (signal) { signal.review_status = status; _reviewed.unshift(signal); }
  cardEl.remove();
  updateTabCounts();
  const count = document.getElementById("count");
  count.textContent = _signals.length ? `${_signals.length} unreviewed signal(s)` : "";
  if (!_signals.length)
    document.getElementById("app").innerHTML = '<p id="empty-state">No unreviewed signals.</p>';
}

function card(s, readonly = false) {
  const title = s.onderwerp || s.doc_id;
  const meta  = [s.soort, s.datum, s.vergaderjaar].filter(Boolean).join(" \\u00b7 ");

  const rows = Object.entries(NORM_LABELS).map(([k, label]) => {
    const val  = s.norm_frame[k];
    const cell = val ? `<td>${esc(val)}</td>` : `<td class="empty">\\u2014</td>`;
    return `<tr><th>${label}</th>${cell}</tr>`;
  }).join("");

  const certainty = s.signal_certainty
    ? `<span class="badge badge-certainty">${esc(s.signal_certainty)}</span>` : "";

  const statusBadge = readonly && s.review_status
    ? `<span class="status-badge status-${s.review_status}">${esc(s.review_status)}</span>` : "";

  const actionBox = s.client_action
    ? `<div class="action-box"><strong>Action:</strong> ${esc(s.client_action)}</div>` : "";

  const reasons = s.sector_reasons || {};
  const sectors = (s.affected_sectors || []).length
    ? `<div class="sectors">${s.affected_sectors.map(sec => {
        const why = reasons[sec];
        return `<div class="sector-item">
          <span class="badge badge-sector">${esc(sec)}</span>
          ${why ? `<div class="sector-reason">${esc(why)}</div>` : ""}
        </div>`;
      }).join("")}</div>` : "";

  const summary = s.signal_summary
    ? `<p class="summary">${highlightTerms(s.signal_summary, s.norm_frame)}</p>` : "";

  const phrase    = s.signal_summary ? firstPhrase(s.signal_summary) : "";
  const searchUrl = `/viewer/${s.doc_id}` + (phrase ? `?search=${encodeURIComponent(phrase)}` : "");

  const actions = readonly ? "" : `
  <div class="actions">
    <button class="btn-strong">\\u2605 Strong signal</button>
    <button class="btn-weak">\\u2606 Weak signal</button>
    <button class="btn-unsure">? Not sure</button>
    <button class="btn-discard">\\u2715 Discard</button>
  </div>`;

  return `
<div class="card" data-id="${s.id}">
  <div class="card-header">
    <div>
      <div class="card-title">
        <a href="${searchUrl}" target="_blank" rel="noopener">${esc(title)}</a>
        ${statusBadge}
      </div>
      <div class="card-meta">${esc(meta)}</div>
    </div>
    <div style="display:flex;gap:.4rem;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end">
      <span class="badge badge-score">${s.completeness_score}</span>
      <span class="badge badge-stream">${esc(s.stream_tag)}</span>
      ${certainty}
    </div>
  </div>
  ${actionBox}
  ${sectors}
  ${summary}
  <details class="chunks-details">
    <summary>Source chunks used for this signal</summary>
    <div class="chunks-container"></div>
  </details>
  <table>${rows}</table>
  ${actions}
</div>`;
}

function normalize(text) {
  return text
    .replace(/-\\n/g, "")
    .replace(/\\n/g, " ")
    .replace(/ {2,}/g, " ")
    .trim();
}

function firstPhrase(text) {
  const end = text.search(/[.!?]/);
  return (end > 20 ? text.slice(0, end) : text.slice(0, 80)).trim();
}

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Bold norm-frame terms that appear verbatim in the summary text.
// We work on the HTML-escaped string throughout so we never double-escape.
function highlightTerms(summary, normFrame) {
  if (!summary || !normFrame) return esc(summary || "");

  let text = esc(summary);

  // Only highlight fields that carry meaningful domain terms
  const FIELDS = ["act_identifier", "subject", "legal_modality", "norm_type", "promulgation"];

  const terms = FIELDS
    .map(k => String(normFrame[k] || "").trim())
    .filter(v => v.length >= 4)        // skip trivially short values
    .sort((a, b) => b.length - a.length); // longest match first to avoid partial overlap

  for (const term of terms) {
    // Escape HTML in the term so it matches the already-escaped `text`
    const escapedTerm = esc(term);
    // Escape regex special characters inside the escaped term
    const pattern = escapedTerm.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
    const re = new RegExp(pattern, "gi");
    text = text.replace(re, m => `<mark>${m}</mark>`);
  }

  return text;
}

load();
</script>
</body>
</html>
"""


def html() -> str:
    """Return the full review UI HTML page."""
    return _HTML
