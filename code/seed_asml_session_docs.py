"""Seed the bronze store with ASML-relevant government letters for the expert validation session.

These documents were selected for the think-aloud session with:
  - ASML, Head of Compliance Operations & Processes
  - ASML, Senior Legal Counsel Corporate

They cover the core regulatory domains relevant to ASML:
  1. Export controls on semiconductor equipment
  2. FDI / investment screening (Wet vifo)
  3. Supply chain due diligence (CSDDD/CSRD)
  4. Broader economic security / strategic resilience

Usage (inside the pipeline container or with local venv):
    python seed_asml_session_docs.py [--dry-run]

The script queries the OData API by subject keyword to resolve UUIDs,
then seeds found documents through the standard bronze pipeline.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Target documents — defined as (keyword, soort, year_from) tuples.
# The script finds the best match (most recent) for each and seeds it.
# ---------------------------------------------------------------------------
TARGET_SIGNALS = [
    {
        "label": "Voortgang halfgeleiderindustrie in veranderende geopolitieke omgeving",
        "rationale": (
            "Directly relevant for both experts: covers export control expansions "
            "(sept 2023, sept 2024, april 2025), ASML's strategic importance, "
            "and government obligations re: national security licensing."
        ),
        "keyword": "halfgeleiderindustrie",
        "soort": "Brief regering",
        "year_from": "2025-01-01",
    },
    {
        "label": "Nationale exportcontrolemaatregelen hoogwaardige en sensitieve technologieën",
        "rationale": (
            "Compliance-critical: announces new national licensing requirements "
            "published in the Staatscourant for high-value tech exports — triggers "
            "immediate operational compliance work for Head of Compliance."
        ),
        "keyword": "nationale exportcontrolemaatregelen",
        "soort": "Brief regering",
        "year_from": "2024-01-01",
    },
    {
        "label": "Rapport Nederlands exportcontrolebeleid in 2023",
        "rationale": (
            "Annual compliance overview — gives the Legal Counsel the full picture "
            "of dual-use and military export licensing volumes, refusals, and "
            "enforcement trends."
        ),
        "keyword": "exportcontrolebeleid in 2023",
        "soort": "Brief regering",
        "year_from": "2024-01-01",
    },
    {
        "label": "Stand van zaken herziening Verordening screening buitenlandse directe investeringen",
        "rationale": (
            "FDI screening (Wet vifo) revision at EU level — directly affects ASML "
            "as a strategic asset. Legal Counsel must track whether new sector-specific "
            "tests (incl. semiconductors) will apply."
        ),
        "keyword": "screening buitenlandse directe investeringen",
        "soort": "Brief regering",
        "year_from": "2025-01-01",
    },
    {
        "label": "Stop-the-clock CSDDD / Omnibus I — verlenging implementatietermijn",
        "rationale": (
            "Supply chain due diligence (CSDDD) implementation delay — compliance "
            "teams need to track revised timelines. Directly affects ASML's supplier "
            "compliance programme."
        ),
        "keyword": "CSDDD",
        "soort": "Brief regering",
        "year_from": "2025-04-01",
    },
    {
        "label": "Nederlandse inzet CRP Omnibus-CSDDD",
        "rationale": (
            "Government position on the CSDDD renegotiation — signals which "
            "due diligence obligations are likely to survive Omnibus I reforms. "
            "Critical for Legal Counsel planning the compliance roadmap."
        ),
        "keyword": "Omnibus-CSDDD",
        "soort": "Brief regering",
        "year_from": "2025-01-01",
    },
    {
        "label": "Investeren in een weerbare economie / maatschappelijke weerbaarheid",
        "rationale": (
            "Signals broad economic security obligations including technology "
            "protection requirements for strategic companies like ASML — relevant "
            "for both compliance and legal risk assessment."
        ),
        "keyword": "investeren in een weerbare",
        "soort": "Brief regering",
        "year_from": "2025-01-01",
    },
]


def _find_doc_by_keyword(keyword: str, soort: str, year_from: str) -> dict | None:
    """Query OData for the most recent document matching keyword + soort."""
    import requests
    import config

    params = {
        "$filter": (
            f"Soort eq '{soort}' and Verwijderd eq false "
            f"and Datum ge {year_from} "
            f"and contains(tolower(Onderwerp), '{keyword.lower()}')"
        ),
        "$select": "Id,Soort,Datum,Onderwerp,Vergaderjaar,ContentType",
        "$orderby": "Datum desc",
        "$top": 1,
    }
    url = f"{config.ODATA_BASE}/Document"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("value", [])
    return results[0] if results else None


def seed(dry_run: bool = False) -> None:
    # Late imports — only needed when actually seeding
    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_command
    import config
    from pipeline.bronze.fetcher import download_file
    from pipeline.bronze.tagger import assign_stream_tag
    from pipeline.db.repositories.bronze import BronzeRepository, BronzeRecord
    from pipeline.silver.extractor import get_extractor

    if not dry_run:
        log.info("Running migrations...")
        ini_path = Path(__file__).parent / "alembic.ini"
        cfg = AlembicConfig(str(ini_path))
        alembic_command.upgrade(cfg, "head")

    repo = None if dry_run else BronzeRepository()
    data_dir = Path(config.DATA_DIR)

    ok = failed = skipped = 0

    for target in TARGET_SIGNALS:
        label = target["label"]
        log.info("\n── %s", label)
        log.info("   Rationale: %s", target["rationale"])

        # Resolve UUID via OData keyword search
        match = _find_doc_by_keyword(
            target["keyword"], target["soort"], target["year_from"]
        )
        if not match:
            log.warning("   No match found for keyword=%r — skipping", target["keyword"])
            failed += 1
            continue

        doc_id = match["Id"]
        onderwerp = match.get("Onderwerp", "")
        datum_str = match.get("Datum", "")
        log.info("   Matched: %s  |  %s  |  %s", datum_str[:10], doc_id, onderwerp[:80])

        if dry_run:
            log.info("   [DRY RUN] Would seed doc_id=%s", doc_id)
            ok += 1
            continue

        if repo.exists(doc_id):
            log.info("   Already in bronze — skipping")
            skipped += 1
            continue

        datum = date.fromisoformat(datum_str[:10]) if datum_str else None
        stream_tag = assign_stream_tag(match.get("Soort", ""), datum)

        try:
            file_path, content_type = download_file(doc_id, data_dir)
        except Exception as exc:
            log.error("   File download failed: %s", exc)
            failed += 1
            continue

        try:
            extractor = get_extractor(content_type)
            raw_text = extractor.extract(file_path)
            if not raw_text.strip():
                raise ValueError("Empty text after extraction")
        except Exception as exc:
            log.error("   Text extraction failed: %s", exc)
            failed += 1
            continue

        record = BronzeRecord(
            id=doc_id,
            soort=match.get("Soort", ""),
            datum=datum,
            onderwerp=onderwerp,
            vergaderjaar=match.get("Vergaderjaar"),
            content_type=content_type,
            stream_tag=stream_tag,
            raw_text=raw_text,
            raw_file_path=str(file_path),
        )
        try:
            repo.insert(record)
            log.info("   Inserted — %d chars", len(raw_text))
            ok += 1
        except Exception as exc:
            log.error("   DB insert failed: %s", exc)
            failed += 1

    log.info("\nDone: %d seeded, %d skipped (already present), %d failed", ok, skipped, failed)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed ASML session documents into bronze.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve UUIDs and print matches without writing to the database.",
    )
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
