"""Seed the bronze store with the 10 validation documents (5 positive + 5 negative).

Run this once on a clean database (after docker-compose down -v && docker-compose up -d db).
After this script completes, all 10 documents are in the bronze store with raw_text populated,
ready for individual --doc-id pipeline runs.

Usage (inside the pipeline container or with local venv):
    python seed_validation_docs.py
"""

import logging
import sys
from datetime import date
from pathlib import Path

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

import config
from pipeline.bronze.fetcher import fetch_single_metadata, download_file
from pipeline.bronze.tagger import assign_stream_tag
from pipeline.db.repositories.bronze import BronzeRepository, BronzeRecord
from pipeline.silver.extractor import get_extractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# 5 positive cases (should be detected as signals)
VALIDATION_DOCS = [
    {
        "id": "088132e5-f6bd-4124-a5ce-f1705be36e9a",
        "label": "Case 1 — Wet goed verhuurderschap (Ollongren letter, 2021-02-22)",
    },
    {
        "id": "f072ca19-05b9-4af1-a895-d5020876fe78",
        "label": "Case 2 — Wet toekomst pensioenen (Principeakkoord, 2019-06-05)",
    },
    {
        "id": "9dac5c86-862b-4e00-962a-4e5168218a3e",
        "label": "Case 3 — Wet inburgering 2021 (Hoofdlijnen veranderopgave, 2018-07-02)",
    },
    {
        "id": "3b7e0412-8e5a-4b81-902e-b17e01657627",
        "label": "Case 4 — Wtta (Technische uitwerking Borstlap, 2020-07-15)",
    },
    {
        "id": "911c7082-b68b-4d73-9c80-16c2419a3259",
        "label": "Case 5 — Wet franchise (Stand van zaken regelgeving Franchise, 2018-05-23)",
    },
    # 5 negative cases (same dossiers, should be discarded — no legislative commitment)
    {
        "id": "552b83c2-67ac-4f4c-8ae5-96abb482cbdf",
        "label": "N1 — 27 926 nr. 326 Stand van zaken Huurcommissie (2020-07-02)",
    },
    {
        "id": "349df7ce-d2a8-405d-a099-5ed5c6c5cdf3",
        "label": "N2 — 29 544 nr. 970 Rapport Commissie Borstlap (2020-01-23)",
    },
    {
        "id": "6b96d047-d7f5-4909-9597-360f6a527a95",
        "label": "N3 — 29 544 nr. 1002 Uitkomsten uitzendonderzoeken (2020-04-06)",
    },
    {
        "id": "bf392419-e4be-4725-8580-b83d775a787b",
        "label": "N4 — 31 311 nr. 186 Evaluatie fiscale ondernemerschapsregelingen (2017-05-18)",
    },
    {
        "id": "9858d519-158f-4497-8652-c3a9c24d4d70",
        "label": "N5 — 32 824 nr. 50 Ontwikkelingen inburgeringsexamens (2014-03-11)",
    },
]


def _run_migrations() -> None:
    ini_path = Path(__file__).parent / "alembic.ini"
    cfg = AlembicConfig(str(ini_path))
    alembic_command.upgrade(cfg, "head")


def seed() -> None:
    log.info("Running migrations...")
    _run_migrations()

    repo = BronzeRepository()
    data_dir = Path(config.DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)

    ok = failed = 0

    for entry in VALIDATION_DOCS:
        doc_id = entry["id"]
        label = entry["label"]
        log.info("── %s", label)

        if repo.exists(doc_id):
            log.info("   Already in bronze — skipping")
            ok += 1
            continue

        # 1. Fetch metadata from OData
        try:
            raw = fetch_single_metadata(doc_id)
        except Exception as exc:
            log.error("   Metadata fetch failed: %s", exc)
            failed += 1
            continue

        datum_str = raw.get("Datum")
        datum = date.fromisoformat(datum_str[:10]) if datum_str else None
        stream_tag = assign_stream_tag(raw.get("Soort", ""), datum)

        # 2. Download the file
        try:
            file_path, content_type = download_file(doc_id, data_dir)
        except Exception as exc:
            log.error("   File download failed: %s", exc)
            failed += 1
            continue

        # 3. Extract text
        try:
            extractor = get_extractor(content_type)
            raw_text = extractor.extract(file_path)
            if not raw_text.strip():
                raise ValueError("Empty text after extraction")
        except Exception as exc:
            log.error("   Text extraction failed: %s", exc)
            failed += 1
            continue

        # 4. Insert into bronze
        record = BronzeRecord(
            id=doc_id,
            soort=raw.get("Soort", ""),
            datum=datum,
            onderwerp=raw.get("Onderwerp"),
            vergaderjaar=raw.get("Vergaderjaar"),
            content_type=content_type,
            stream_tag=stream_tag,
            raw_text=raw_text,
            raw_file_path=str(file_path),
        )
        try:
            repo.insert(record)
            log.info("   Inserted — %d chars extracted", len(raw_text))
            ok += 1
        except Exception as exc:
            log.error("   DB insert failed: %s", exc)
            failed += 1

    log.info("Seed complete: %d ok, %d failed", ok, failed)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    seed()
