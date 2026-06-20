"""OData metadata fetcher and file downloader (tasks 20 + 21).

fetch_metadata() paginates through the Tweede Kamer OData API and yields
one dict per document. Filtering is applied server-side (Soort, Datum,
Verwijderd). Deduplication is the caller's responsibility.

download_file() retrieves the /resource endpoint for a document and writes
the raw file to disk. Returns the local path and the content type.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Iterator

import requests

import config

log = logging.getLogger(__name__)

_DOCUMENT_URL = f"{config.ODATA_BASE}/Document"
_RESOURCE_URL = f"{config.ODATA_BASE}/Document({{id}})/resource"

# Fields to request from the API — keeps response payload small
_SELECT = "Id,Soort,Datum,Onderwerp,Vergaderjaar,ContentType"


def fetch_metadata(watermark: str) -> Iterator[dict]:
    """Yield document metadata dicts for all relevant documents since watermark.

    Paginates automatically using $skip. Applies server-side filters for
    Soort (relevant values only), Datum (>= watermark), and Verwijderd (false).

    Args:
        watermark: ISO date string (e.g. '2020-01-01'). Only documents with
                   Datum >= watermark are returned.

    Yields:
        Raw dict with keys: Id, Soort, Datum, Onderwerp, Vergaderjaar, ContentType.
    """
    soort_filter = _build_soort_filter()
    skip = 0

    while True:
        params = {
            "$filter": (
                f"Verwijderd eq false"
                f" and Datum ge {watermark}"
                f" and ({soort_filter})"
            ),
            "$select": _SELECT,
            "$skip": skip,
            "$top": config.ODATA_MAX_PAGE,
            "$orderby": "Datum asc",
        }

        log.info("Fetching metadata: skip=%d watermark=%s", skip, watermark)
        response = requests.get(_DOCUMENT_URL, params=params, timeout=30)
        response.raise_for_status()

        records = response.json().get("value", [])
        if not records:
            break

        for record in records:
            yield record

        if len(records) < config.ODATA_MAX_PAGE:
            break

        skip += config.ODATA_MAX_PAGE


def fetch_single_metadata(doc_id: str) -> dict:
    """Fetch metadata for a single document by its OData Id.

    Uses $filter=Id eq <id> on the collection endpoint rather than the entity
    key endpoint Document('<id>'), because some documents return 404 on the key
    endpoint despite being present in the collection (OData API quirk).

    Args:
        doc_id: The OData document Id (UUID string).

    Returns:
        Raw dict with keys: Id, Soort, Datum, Onderwerp, Vergaderjaar, ContentType.

    Raises:
        KeyError: If the document is not found in the collection.
        requests.HTTPError: If the request itself fails.
    """
    log.info("Fetching single document metadata for doc_id=%s", doc_id)
    params = {
        "$filter": f"Id eq {doc_id}",
        "$select": _SELECT,
        "$top": 1,
    }
    response = requests.get(_DOCUMENT_URL, params=params, timeout=30)
    response.raise_for_status()
    results = response.json().get("value", [])
    if not results:
        raise KeyError(f"doc_id={doc_id!r} not found in OData collection")
    return results[0]


def download_file(doc_id: str, dest_dir: Path) -> tuple[Path, str]:
    """Download the raw file for a document and write it to dest_dir.

    Args:
        doc_id: The OData document Id (UUID string).
        dest_dir: Directory to write the file into.

    Returns:
        Tuple of (local file path, content type string).

    Raises:
        requests.HTTPError: If the download fails.
        ValueError: If the response has no recognisable content type.
    """
    url = _RESOURCE_URL.format(id=doc_id)
    log.info("Downloading file for doc_id=%s", doc_id)

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    extension = _extension_for(content_type)

    dest_dir.mkdir(parents=True, exist_ok=True)
    file_path = dest_dir / f"{doc_id}{extension}"
    file_path.write_bytes(response.content)

    log.info("Saved %s (%d bytes) → %s", content_type, len(response.content), file_path)
    return file_path, content_type


def _build_soort_filter() -> str:
    """Build an OData filter clause for the relevant Soort values."""
    clauses = [f"Soort eq '{soort}'" for soort in sorted(config.RELEVANT_SOORTEN)]
    return " or ".join(clauses)


def _extension_for(content_type: str) -> str:
    """Return a file extension for a given content type."""
    mapping = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }
    if content_type not in mapping:
        raise ValueError(f"Unsupported content type: {content_type!r}")
    return mapping[content_type]
