"""PDF.js viewer endpoint (task 29).

Renders each PDF page on a canvas, then highlights search matches by drawing
yellow rectangles directly on the canvas using item positions from getTextContent().
This avoids the window.find() approach which fails when words are split across
absolutely-positioned spans without spaces between them.
"""

from __future__ import annotations
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/viewer", tags=["viewer"])

_PDFJS = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174"

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>Document viewer</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #525659; font-family: sans-serif; }
#toolbar {
  position: fixed; top: 0; left: 0; right: 0; height: 44px;
  background: #323639; color: #fff;
  display: flex; align-items: center; padding: 0 1rem; gap: 0.75rem;
  z-index: 100; font-size: 13px;
}
#status { color: #aaa; min-width: 80px; }
#s { padding: 0.25rem 0.6rem; border-radius: 3px; border: none;
     font-size: 13px; width: 300px; }
button { padding: 0.25rem 0.8rem; border-radius: 3px; border: none;
         cursor: pointer; font-size: 13px; background: #555; color: #fff; }
button:hover { background: #777; }
#viewer { padding-top: 56px; }
.pw { position: relative; margin: 10px auto;
      box-shadow: 0 2px 8px rgba(0,0,0,.6); }
canvas { display: block; }
.tl {
  position: absolute; top: 0; left: 0;
  width: 100%; height: 100%; overflow: hidden;
  pointer-events: none;
}
.tl span {
  position: absolute; color: transparent;
  white-space: pre; transform-origin: 0% 0%;
  pointer-events: all; cursor: text;
  user-select: text; -webkit-user-select: text;
}
</style>
</head>
<body>
<div id="toolbar">
  <span id="status">Loading…</span>
  <input id="s" type="text" value="__SEARCH_ATTR__" placeholder="Search in document…">
  <button onclick="doFind()">Find</button>
</div>
<div id="viewer"></div>

<script src="__PDFJS__/pdf.min.js"></script>
<script>
pdfjsLib.GlobalWorkerOptions.workerSrc = '__PDFJS__/pdf.worker.min.js';

const PDF_URL = __PDF_URL__;
const SEARCH  = __SEARCH__;

// Combines two 6-element 2-D affine matrices [a,b,c,d,e,f].
function matMul(m1, m2) {
  return [
    m1[0]*m2[0] + m1[2]*m2[1],
    m1[1]*m2[0] + m1[3]*m2[1],
    m1[0]*m2[2] + m1[2]*m2[3],
    m1[1]*m2[2] + m1[3]*m2[3],
    m1[0]*m2[4] + m1[2]*m2[5] + m1[4],
    m1[1]*m2[4] + m1[3]*m2[5] + m1[5],
  ];
}

// Stored per rendered page: {wrapper, canvas, items, vp}
const pages = [];

async function main() {
  const status = document.getElementById('status');
  try {
    const pdf = await pdfjsLib.getDocument(PDF_URL).promise;
    for (let n = 1; n <= pdf.numPages; n++) {
      status.textContent = n + ' / ' + pdf.numPages;
      await renderPage(pdf, n);
    }
    status.textContent = pdf.numPages + ' pages';
    if (SEARCH) doFind();
  } catch(e) {
    status.textContent = 'Error: ' + e.message;
    console.error(e);
  }
}

async function renderPage(pdf, n) {
  const page  = await pdf.getPage(n);
  const scale = Math.min(window.innerWidth - 24, 880) /
                page.getViewport({scale: 1}).width;
  const vp    = page.getViewport({scale});

  const wrap = document.createElement('div');
  wrap.className = 'pw';
  wrap.style.cssText = `width:${vp.width}px;height:${vp.height}px`;
  document.getElementById('viewer').appendChild(wrap);

  const canvas = document.createElement('canvas');
  canvas.width  = vp.width;
  canvas.height = vp.height;
  wrap.appendChild(canvas);
  await page.render({canvasContext: canvas.getContext('2d'), viewport: vp}).promise;

  const tc = await page.getTextContent();
  buildTextLayer(tc.items, vp, wrap);
  pages.push({wrap, canvas, items: tc.items, vp});
}

function buildTextLayer(items, vp, wrap) {
  const div = document.createElement('div');
  div.className = 'tl';
  wrap.appendChild(div);

  for (const item of items) {
    if (!item.str) continue;
    const tx = matMul(vp.transform, item.transform);
    const fs = Math.sqrt(tx[0]*tx[0] + tx[1]*tx[1]);
    if (fs < 1) continue;

    const span = document.createElement('span');
    span.textContent = item.str;
    span.style.fontSize = fs + 'px';
    span.style.left     = tx[4] + 'px';
    span.style.top      = (tx[5] - fs) + 'px';
    div.appendChild(span);

    // Scale each span so its rendered width matches the PDF advance width.
    // getBoundingClientRect() forces a synchronous layout — acceptable for
    // the ~100-200 items per page typical in these documents.
    const expected = (item.width || 0) * vp.scale;
    const natural  = span.getBoundingClientRect().width;
    if (natural > 0 && expected > 0) {
      span.style.transform = `scaleX(${expected / natural})`;
    }
  }
}

function doFind() {
  const term = document.getElementById('s').value.trim();
  if (!term) return;

  // Normalise: collapse whitespace, lowercase, remove hyphens at end of words
  // This matches the same normalisation applied to chunk_text in review.py.
  const norm = s => s.replace(/-\s+/g, '').replace(/\s+/g, ' ').toLowerCase().trim();
  const needle = norm(term);

  for (const {wrap, canvas, items, vp} of pages) {
    // Build page text the same way: join item strings with a space.
    // item.hasEOL items get an extra space so line breaks become word boundaries.
    const words = items.map(i => i.str + (i.hasEOL ? ' ' : '')).join('');
    const haystack = norm(words);

    const idx = haystack.indexOf(needle);
    if (idx < 0) continue;

    // Map character index back to items so we know which ones to highlight.
    highlight(canvas, items, vp, idx, idx + needle.length);
    wrap.scrollIntoView({behavior: 'smooth', block: 'center'});
    document.getElementById('status').textContent = 'Match found';
    return;
  }
  document.getElementById('status').textContent = 'Not found';
}

function highlight(canvas, items, vp, startIdx, endIdx) {
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(255, 200, 0, 0.45)';

  let pos = 0;
  for (const item of items) {
    if (!item.str) continue;
    const itemEnd = pos + item.str.length + (item.hasEOL ? 1 : 0);

    if (itemEnd > startIdx && pos < endIdx) {
      const tx       = matMul(vp.transform, item.transform);
      const fontSize = Math.sqrt(tx[0]*tx[0] + tx[1]*tx[1]);
      // item.width is the advance width in user-space; multiply by viewport scale for CSS pixels.
      const w = (item.width || 0) * vp.scale;
      if (w > 0 && fontSize > 0) {
        ctx.fillRect(tx[4], tx[5] - fontSize * 1.1, w, fontSize * 1.35);
      }
    }

    pos = itemEnd;
    if (pos > endIdx) break;
  }
}

main();
</script>
</body>
</html>"""


def _build(pdf_url: str, search: str) -> str:
    return (
        _TEMPLATE
        .replace("__PDFJS__", _PDFJS)
        .replace("__PDF_URL__", json.dumps(pdf_url))
        .replace("__SEARCH__", json.dumps(search))
        .replace("__SEARCH_ATTR__", search.replace('"', "&quot;").replace("<", "&lt;"))
    )


@router.get("/{doc_id}", response_class=HTMLResponse, include_in_schema=False)
def pdf_viewer(doc_id: str, search: str = "") -> str:
    """Serve a PDF.js viewer pre-loaded with the document and search term."""
    return _build(f"/documents/{doc_id}", search)
