"""Stage orchestrators.

Each function runs one stage end-to-end over all pending records.
Stages are idempotent: records already processed are skipped automatically.

run_single_doc() is the exception: it deletes existing downstream rows first so a
named document is always fully reprocessed — useful for isolated validation runs.
"""

import logging

import config

log = logging.getLogger(__name__)


def run_bronze(limit: int | None = None) -> None:
    """Fetch new documents from OData, tag streams, store in bronze.

    Skips documents already in the bronze store (deduplication by id).
    Only fetches documents with Datum >= watermark (MAX ingested_at or START_DATE).

    Args:
        limit: Stop after inserting this many documents. None = no limit.
               Use during development to avoid downloading the full archive.
    """
    from pathlib import Path
    from datetime import date as _date
    from pipeline.bronze.fetcher import fetch_metadata, download_file
    from pipeline.bronze.tagger import assign_stream_tag
    from pipeline.db.repositories.bronze import BronzeRepository, BronzeRecord

    repo = BronzeRepository()
    watermark = repo.get_watermark()
    data_dir = Path(config.DATA_DIR)

    inserted = skipped = errors = 0

    for raw in fetch_metadata(watermark):
        if limit is not None and inserted >= limit:
            log.info("Reached limit of %d inserted documents — stopping bronze", limit)
            break

        doc_id = raw["Id"]

        if repo.exists(doc_id):
            skipped += 1
            continue

        # Parse datum — API returns ISO string or null
        datum_str = raw.get("Datum")
        datum = _date.fromisoformat(datum_str[:10]) if datum_str else None

        stream_tag = assign_stream_tag(raw.get("Soort", ""), datum)

        try:
            file_path, content_type = download_file(doc_id, data_dir)
        except Exception as exc:
            log.warning("Failed to download doc_id=%s: %s", doc_id, exc)
            errors += 1
            continue

        try:
            from pipeline.silver.extractor import get_extractor
            raw_text = get_extractor(content_type).extract(file_path)
        except (KeyError, ValueError) as exc:
            log.warning("Text extraction failed doc_id=%s: %s", doc_id, exc)
            raw_text = None

        record = BronzeRecord(
            id=doc_id,
            soort=raw.get("Soort", ""),
            datum=datum,
            onderwerp=raw.get("Onderwerp"),
            vergaderjaar=raw.get("Vergaderjaar"),
            content_type=content_type,
            stream_tag=stream_tag,
            raw_file_path=str(file_path),
            raw_text=raw_text,
        )
        repo.insert(record)
        inserted += 1

    log.info("Bronze complete — inserted=%d skipped=%d errors=%d", inserted, skipped, errors)


def run_bronze_backfill() -> None:
    """Populate raw_text for bronze records that were ingested before text extraction was added."""
    from pathlib import Path
    from pipeline.silver.extractor import get_extractor
    from pipeline.db.repositories.bronze import BronzeRepository

    repo = BronzeRepository()
    filled = errors = 0

    for record in repo.get_missing_raw_text():
        try:
            text = get_extractor(record.content_type).extract(Path(record.raw_file_path))
            repo.update_raw_text(record.id, text)
            filled += 1
        except (KeyError, ValueError) as exc:
            log.warning("Backfill extraction failed doc_id=%s: %s", record.id, exc)
            errors += 1

    log.info("Bronze backfill complete — filled=%d errors=%d", filled, errors)


def run_silver(doc_id: str | None = None) -> None:
    """Classify and chunk bronze documents not yet in silver.

    If doc_id is given, only that document is processed (single-doc mode).
    Otherwise all unprocessed bronze documents are processed.
    """
    from pipeline.silver.classifier import classify
    from pipeline.silver.chunker import chunk
    from pipeline.llm.client import get_client
    from pipeline.db.repositories.bronze import BronzeRepository
    from pipeline.db.repositories.silver import SilverRepository, SilverRecord
    from pipeline.db.repositories.silver_rejected import SilverRejectedRepository
    from pipeline.db.repositories.classifier_log import ClassifierLogRepository, ClassifierLogRecord

    bronze_repo = BronzeRepository()
    silver_repo = SilverRepository()
    rejected_repo = SilverRejectedRepository()
    classifier_log_repo = ClassifierLogRepository()
    llm = get_client(config.CLASSIFIER_MODEL)

    accepted = rejected = errors = 0
    import time as _time
    t_stage = _time.perf_counter()

    for record in bronze_repo.get_unprocessed(config.PROFILE_VERSION, doc_id=doc_id):
        t0 = _time.perf_counter()
        if not record.raw_text:
            log.warning("No raw_text for doc_id=%s — skipping", record.id)
            errors += 1
            continue

        try:
            result = classify(record.raw_text, llm)
        except Exception as exc:
            log.warning("Classification failed doc_id=%s: %s", record.id, exc)
            errors += 1
            continue

        elapsed = _time.perf_counter() - t0

        classifier_log_repo.insert(ClassifierLogRecord(
            doc_id=record.id,
            relevant=result.relevant,
            reason=result.reason,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            profile_version=config.PROFILE_VERSION,
            duration_ms=int(elapsed * 1000),
        ))

        if not result.relevant:
            log.info("Rejected doc_id=%s in=%d out=%d (%.1fs) reason=%r",
                     record.id, result.input_tokens, result.output_tokens, elapsed, result.reason)
            rejected_repo.insert(record.id, config.PROFILE_VERSION, result.reason)
            rejected += 1
            continue

        chunks = chunk(record.raw_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        for i, chunk_text in enumerate(chunks):
            silver_repo.insert(SilverRecord(
                doc_id=record.id,
                chunk_index=i,
                chunk_text=chunk_text,
                profile_version=config.PROFILE_VERSION,
            ))
        accepted += 1
        log.info("Accepted doc_id=%s chunks=%d in=%d out=%d (%.1fs) reason=%r",
                 record.id, len(chunks), result.input_tokens, result.output_tokens, elapsed, result.reason)

    log.info(
        "Silver complete — accepted=%d rejected=%d errors=%d total=%.1fs",
        accepted, rejected, errors, _time.perf_counter() - t_stage,
    )


def run_gold(limit: int | None = None, doc_id: str | None = None) -> None:
    """Extract norm frames from silver chunks not yet in gold.

    If doc_id is given, only chunks for that document are processed (single-doc mode).
    Otherwise all unprocessed silver chunks are processed.

    Args:
        limit: Stop after processing chunks from this many documents. None = no limit.
        doc_id: Restrict processing to this document only.
    """
    from pipeline.gold.extractor import extract
    from pipeline.gold.scorer import score
    from pipeline.llm.client import get_client
    from pipeline.db.repositories.silver import SilverRepository
    from pipeline.db.repositories.gold import GoldRepository, GoldRecord
    from pipeline.db.repositories.gold_discarded import GoldDiscardedRepository

    silver_repo = SilverRepository()
    gold_repo = GoldRepository()
    discarded_repo = GoldDiscardedRepository()
    llm = get_client(config.LLM_MODEL)

    written = discarded = errors = 0
    import time as _time
    t_stage = _time.perf_counter()
    docs_seen: set[str] = set()

    for silver, stream_tag in silver_repo.get_unprocessed(doc_id=doc_id):
        if limit is not None and silver.doc_id not in docs_seen and len(docs_seen) >= limit:
            log.info("Reached limit of %d documents — stopping gold", limit)
            break
        docs_seen.add(silver.doc_id)
        t0 = _time.perf_counter()
        try:
            result = extract(silver.chunk_text, llm)
        except Exception as exc:
            log.warning(
                "Extraction failed doc_id=%s chunk=%d: %s",
                silver.doc_id, silver.chunk_index, exc,
            )
            errors += 1
            continue

        completeness = score(result.norm_frame)
        elapsed = _time.perf_counter() - t0

        if completeness < config.COMPLETENESS_THRESHOLD:
            log.debug(
                "Discarded doc_id=%s chunk=%d score=%d (%.1fs)",
                silver.doc_id, silver.chunk_index, completeness, elapsed,
            )
            discarded_repo.insert(silver.doc_id, silver.chunk_index, completeness)
            discarded += 1
            continue

        gold_repo.insert(GoldRecord(
            doc_id=silver.doc_id,
            chunk_index=silver.chunk_index,
            norm_frame=result.norm_frame,
            reasoning=result.reasoning,
            signal_summary=result.signal_summary,
            signal_certainty=result.signal_certainty,
            source_type=result.source_type,
            completeness_score=completeness,
            stream_tag=stream_tag,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            duration_ms=int(elapsed * 1000),
        ))
        written += 1
        log.info(
            "Gold chunk written doc_id=%s chunk=%d score=%d in=%d out=%d (%.1fs)",
            silver.doc_id, silver.chunk_index, completeness,
            result.input_tokens, result.output_tokens, elapsed,
        )

    log.info(
        "Gold complete — docs=%d written=%d discarded=%d errors=%d total=%.1fs",
        len(docs_seen), written, discarded, errors, _time.perf_counter() - t_stage,
    )


def run_synthesis(limit: int | None = None, doc_id: str | None = None) -> None:
    """Synthesise gold records for unprocessed documents into one unified record each.

    If doc_id is given, only that document is processed (single-doc mode).
    Otherwise all documents with gold records but no synthesis record are processed.

    Args:
        limit: Stop after processing this many documents. None = no limit.
        doc_id: Restrict processing to this document only.
    """
    from pipeline.synthesis.extractor import synthesise
    from pipeline.llm.client import get_client
    from pipeline.db.repositories.gold import GoldRepository
    from pipeline.db.repositories.silver import SilverRepository
    from pipeline.db.repositories.synthesis import SynthesisRepository, SynthesisRecord
    from pipeline.db.connection import transaction

    gold_repo = GoldRepository()
    synthesis_repo = SynthesisRepository()
    llm = get_client(config.LLM_MODEL)

    written = skipped = errors = 0
    import time as _time
    t_stage = _time.perf_counter()

    doc_ids_to_process = [doc_id] if doc_id else synthesis_repo.get_unprocessed_doc_ids()
    for doc_id in doc_ids_to_process:
        if limit is not None and written >= limit:
            log.info("Reached limit of %d documents — stopping synthesis", limit)
            break

        t0 = _time.perf_counter()
        # Fetch all gold records for this document with chunk_text from silver
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.chunk_index, g.norm_frame, g.reasoning,
                       g.signal_summary, g.signal_certainty, g.source_type,
                       g.stream_tag,
                       s.chunk_text
                FROM gold g
                LEFT JOIN LATERAL (
                    SELECT chunk_text FROM silver
                    WHERE doc_id = g.doc_id AND chunk_index = g.chunk_index
                    ORDER BY id DESC LIMIT 1
                ) s ON true
                WHERE g.doc_id = %s
                ORDER BY g.completeness_score DESC
                """,
                (doc_id,),
            )
            rows = cur.fetchall()

        if not rows:
            log.warning("No gold records found for doc_id=%s — skipping", doc_id)
            skipped += 1
            continue

        stream_tag = rows[0][6]

        fragments = [
            {
                "chunk_index": row[0],
                "norm_frame": row[1] or {},
                "reasoning": row[2] or "",
                "signal_summary": row[3] or "",
                "signal_certainty": row[4] or "",
                "source_type": row[5] or "",
                "chunk_text": row[7] or "",
            }
            for row in rows
        ]

        try:
            result = synthesise(fragments, llm)
        except Exception as exc:
            log.warning("Synthesis failed doc_id=%s: %s", doc_id, exc)
            errors += 1
            continue

        synthesis_repo.insert(SynthesisRecord(
            doc_id=doc_id,
            norm_frame=result.norm_frame,
            expected_date=result.expected_date,
            affected_sectors=result.affected_sectors,
            sector_reasons=result.sector_reasons,
            client_action=result.client_action,
            signal_summary=result.signal_summary,
            signal_certainty=result.signal_certainty,
            source_type=result.source_type,
            completeness_score=result.completeness_score,
            stream_tag=stream_tag,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            duration_ms=int((_time.perf_counter() - t0) * 1000),
        ))
        written += 1
        log.info(
            "Synthesis written doc_id=%s score=%d sectors=%s in=%d out=%d (%.1fs)",
            doc_id, result.completeness_score, result.affected_sectors,
            result.input_tokens, result.output_tokens, _time.perf_counter() - t0,
        )

    log.info(
        "Synthesis complete — written=%d skipped=%d errors=%d total=%.1fs",
        written, skipped, errors, _time.perf_counter() - t_stage,
    )


def run_single_doc(doc_id: str, stages: list[str]) -> None:
    """Run silver → gold → synthesis (or a subset) for a single document.

    Existing rows for this doc_id are deleted before each stage so the document
    is always fully reprocessed, regardless of what is already in the store.
    This is intentional: validation runs must reflect the current prompt, not a
    cached result from an earlier run.

    Args:
        doc_id: The bronze document id to (re-)process.
        stages: Ordered list of stages to run; must be a subset of
                ["silver", "gold", "synthesis"].
    """
    import requests as _requests
    from pathlib import Path
    from datetime import date as _date
    from pipeline.db.connection import transaction
    from pipeline.db.repositories.bronze import BronzeRepository, BronzeRecord
    from pipeline.bronze.fetcher import fetch_single_metadata, download_file
    from pipeline.bronze.tagger import assign_stream_tag
    from pipeline.silver.extractor import get_extractor

    bronze_repo = BronzeRepository()

    # Auto-ingest into bronze if the record is missing
    if not bronze_repo.exists(doc_id):
        log.info("doc_id=%s not in bronze — fetching from OData", doc_id)
        data_dir = Path(config.DATA_DIR)

        # Try OData first; fall back to a local file if the document has been
        # removed from the API (e.g. older documents no longer served).
        raw: dict = {}
        try:
            raw = fetch_single_metadata(doc_id)
        except (_requests.HTTPError, KeyError) as exc:
            log.warning("OData fetch failed (%s) — looking for local file", exc)

        # Resolve file: prefer already-downloaded copy, then try OData download
        local_pdf = data_dir / f"{doc_id}.pdf"
        local_docx = data_dir / f"{doc_id}.docx"
        if local_pdf.exists():
            file_path, content_type = local_pdf, "application/pdf"
            log.info("Using local file %s", file_path)
        elif local_docx.exists():
            file_path, content_type = local_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            log.info("Using local file %s", file_path)
        elif raw:
            file_path, content_type = download_file(doc_id, data_dir)
        else:
            raise FileNotFoundError(
                f"doc_id={doc_id!r} not found in OData and no local file exists at "
                f"{local_pdf} or {local_docx}. Download the file manually first."
            )

        datum_str = raw.get("Datum")
        datum = _date.fromisoformat(datum_str[:10]) if datum_str else None
        soort = raw.get("Soort", "Kamerstuk")
        stream_tag = assign_stream_tag(soort, datum)

        try:
            raw_text = get_extractor(content_type).extract(file_path)
        except (KeyError, ValueError) as exc:
            log.warning("Text extraction failed doc_id=%s: %s", doc_id, exc)
            raw_text = None

        bronze_repo.insert(BronzeRecord(
            id=doc_id,
            soort=soort,
            datum=datum,
            onderwerp=raw.get("Onderwerp"),
            vergaderjaar=raw.get("Vergaderjaar"),
            content_type=content_type,
            stream_tag=stream_tag,
            raw_file_path=str(file_path),
            raw_text=raw_text,
        ))
        log.info("Bronze record created for doc_id=%s", doc_id)

    # Delete downstream rows in reverse dependency order so FK constraints
    # are satisfied.  We only delete what we are about to rebuild.
    tables_to_clear: list[str] = []
    if "synthesis" in stages:
        tables_to_clear.append("synthesis")
    if "gold" in stages:
        tables_to_clear += ["gold_discarded", "gold"]
    if "silver" in stages:
        tables_to_clear += ["silver_rejected", "silver"]

    if tables_to_clear:
        with transaction() as conn:
            cur = conn.cursor()
            for table in tables_to_clear:
                cur.execute(f"DELETE FROM {table} WHERE doc_id = %s", (doc_id,))
                log.info("Cleared table=%s for doc_id=%s", table, doc_id)

    # Now run each requested stage — the normal functions will see the doc as
    # unprocessed because we just cleared its rows.
    for stage in stages:
        log.info("Single-doc stage start: %s doc_id=%s", stage, doc_id)
        if stage == "silver":
            run_silver(doc_id=doc_id)
        elif stage == "gold":
            run_gold(doc_id=doc_id)
        elif stage == "synthesis":
            run_synthesis(doc_id=doc_id)
        log.info("Single-doc stage done:  %s doc_id=%s", stage, doc_id)
