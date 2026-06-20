"""Document proxy endpoint (task 29).

Fetches a document from the OData resource endpoint and serves it inline,
so the browser opens it in a tab instead of downloading it.
"""

from __future__ import annotations

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

import config

router = APIRouter(prefix="/documents", tags=["documents"])

_RESOURCE_URL = config.ODATA_BASE + "/Document({doc_id})/resource"


@router.get("/{doc_id}")
def get_document(doc_id: str) -> Response:
    """Proxy the OData resource file and force inline display."""
    url = _RESOURCE_URL.format(doc_id=doc_id)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    content_type = resp.headers.get("Content-Type", "application/octet-stream")
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Content-Disposition": "inline"},
    )
