"""Feasibility benchmark — runtime and token-cost scaling study.

Runs the full pipeline (bronze → silver → gold → synthesis) on increasing batch
sizes and records wall-clock time per stage, token usage, and cost per document.

For each batch size N the script:
  1. Ingests N new 'Brief regering' documents from the OData API (timed).
  2. Runs silver → gold → synthesis on exactly those N new documents (timed).
  3. Collects all metrics from the DB and writes them to CSV/JSON.

Because each batch uses freshly ingested documents, bronze just grows across
iterations and no data is wiped between runs.

Usage:
    # Default scaling study (10, 20, 40, 80, 160 documents per batch):
    python benchmark.py

    # Single batch of N documents:
    python benchmark.py --n-docs 40

    # Custom batch sizes:
    python benchmark.py --batch-sizes 10 50 100

Output (written to data/benchmark/):
    benchmark_<timestamp>.json          — full per-document metrics
    benchmark_<timestamp>.csv           — per-document flat table
    benchmark_summary_<timestamp>.csv   — one row per batch size
"""

import argparse
import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

import config
from pipeline.db.connection import transaction
from pipeline.db.repositories.bronze import BronzeRepository
from pipeline.stages import run_bronze, run_silver, run_gold, run_synthesis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pricing constants — AWS Bedrock Claude Sonnet 4.6 (eu region), USD per token
# Verify against https://aws.amazon.com/bedrock/pricing/ before use
# ---------------------------------------------------------------------------
PRICE_INPUT_PER_TOKEN  = 3.00 / 1_000_000   # $3.00 per 1M input tokens
PRICE_OUTPUT_PER_TOKEN = 15.00 / 1_000_000  # $15.00 per 1M output tokens


def _run_migrations() -> None:
    ini_path = Path(__file__).parent / "alembic.ini"
    cfg = AlembicConfig(str(ini_path))
    alembic_command.upgrade(cfg, "head")


def _collect_metrics(doc_ids: list[str]) -> list[dict]:
    """Query the DB for all benchmark metrics for a set of doc_ids."""
    with transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                b.id                              AS doc_id,
                b.onderwerp                       AS onderwerp,
                b.datum                           AS datum,
                b.soort                           AS soort,

                -- classifier (silver stage)
                cl.relevant                       AS classifier_relevant,
                cl.input_tokens                   AS clf_input_tokens,
                cl.output_tokens                  AS clf_output_tokens,
                cl.duration_ms                    AS clf_duration_ms,

                -- silver chunks produced
                (SELECT COUNT(*) FROM silver s WHERE s.doc_id = b.id)
                                                  AS silver_chunk_count,

                -- gold: sum tokens + durations over all chunks, counts
                (SELECT COUNT(*) FROM gold g WHERE g.doc_id = b.id)
                                                  AS gold_chunks_written,
                (SELECT COUNT(*) FROM gold_discarded gd WHERE gd.doc_id = b.id)
                                                  AS gold_chunks_discarded,
                (SELECT COALESCE(SUM(g.input_tokens),  0) FROM gold g WHERE g.doc_id = b.id)
                                                  AS gold_input_tokens,
                (SELECT COALESCE(SUM(g.output_tokens), 0) FROM gold g WHERE g.doc_id = b.id)
                                                  AS gold_output_tokens,
                (SELECT COALESCE(SUM(g.duration_ms),   0) FROM gold g WHERE g.doc_id = b.id)
                                                  AS gold_duration_ms,
                (SELECT COALESCE(AVG(g.duration_ms), NULL) FROM gold g WHERE g.doc_id = b.id)
                                                  AS gold_avg_chunk_duration_ms,

                -- synthesis
                sy.input_tokens                   AS syn_input_tokens,
                sy.output_tokens                  AS syn_output_tokens,
                sy.duration_ms                    AS syn_duration_ms,
                sy.completeness_score             AS syn_completeness_score,
                sy.signal_certainty               AS syn_signal_certainty

            FROM bronze b
            LEFT JOIN classifier_log cl ON cl.doc_id = b.id
            LEFT JOIN synthesis sy      ON sy.doc_id = b.id
            WHERE b.id = ANY(%s)
            ORDER BY b.datum
            """,
            (doc_ids,),
        )
        columns = [d[0] for d in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    for row in rows:
        clf_in  = row["clf_input_tokens"]  or 0
        clf_out = row["clf_output_tokens"] or 0
        g_in    = row["gold_input_tokens"] or 0
        g_out   = row["gold_output_tokens"] or 0
        s_in    = row["syn_input_tokens"]  or 0
        s_out   = row["syn_output_tokens"] or 0

        row["total_input_tokens"]  = clf_in  + g_in  + s_in
        row["total_output_tokens"] = clf_out + g_out + s_out
        row["total_tokens"]        = row["total_input_tokens"] + row["total_output_tokens"]
        row["cost_usd"] = round(
            row["total_input_tokens"]  * PRICE_INPUT_PER_TOKEN +
            row["total_output_tokens"] * PRICE_OUTPUT_PER_TOKEN,
            6,
        )
        row["total_llm_duration_ms"] = (
            (row["clf_duration_ms"]  or 0) +
            (row["gold_duration_ms"] or 0) +
            (row["syn_duration_ms"]  or 0)
        )
        if row["datum"]:
            row["datum"] = str(row["datum"])
        avg = row.get("gold_avg_chunk_duration_ms")
        row["gold_avg_chunk_duration_ms"] = float(avg) if avg is not None else None

    return rows


def run_batch(n: int, bronze_repo: BronzeRepository) -> tuple[list[dict], dict]:
    """Ingest N new documents and run the full pipeline on them.

    Returns (per-document metrics, stage wall-clock timings in seconds).
    """
    before_ids = set(bronze_repo.get_all_ids())

    # Stage 1: bronze ingestion
    t0 = time.perf_counter()
    run_bronze(limit=n)
    bronze_seconds = time.perf_counter() - t0

    after_ids = set(bronze_repo.get_all_ids())
    new_ids = list(after_ids - before_ids)

    if len(new_ids) < n:
        log.warning("Requested %d new documents but only got %d from OData", n, len(new_ids))
    if not new_ids:
        log.error("No new documents were ingested — OData may be exhausted")
        return [], {"bronze": bronze_seconds, "silver": 0, "gold": 0, "synthesis": 0, "total": bronze_seconds}

    failed: list[str] = []

    # Stage 2: silver (classify + chunk)
    t0 = time.perf_counter()
    for doc_id in new_ids:
        try:
            run_silver(doc_id=doc_id)
        except Exception as exc:
            log.error("Silver failed doc_id=%s: %s — skipping", doc_id, exc)
            failed.append(doc_id)
    silver_seconds = time.perf_counter() - t0

    ok_ids = [d for d in new_ids if d not in failed]

    # Stage 3: gold (norm frame extraction, one LLM call per chunk)
    t0 = time.perf_counter()
    for doc_id in ok_ids:
        try:
            run_gold(doc_id=doc_id)
        except Exception as exc:
            log.error("Gold failed doc_id=%s: %s — skipping", doc_id, exc)
            failed.append(doc_id)
    gold_seconds = time.perf_counter() - t0

    ok_ids = [d for d in ok_ids if d not in failed]

    # Stage 4: synthesis (one LLM call per document)
    t0 = time.perf_counter()
    for doc_id in ok_ids:
        try:
            run_synthesis(doc_id=doc_id)
        except Exception as exc:
            log.error("Synthesis failed doc_id=%s: %s — skipping", doc_id, exc)
            failed.append(doc_id)
    synthesis_seconds = time.perf_counter() - t0

    if failed:
        log.warning("%d document(s) failed and were skipped: %s", len(failed), failed)

    total = bronze_seconds + silver_seconds + gold_seconds + synthesis_seconds
    stage_times = {
        "bronze":    round(bronze_seconds,    2),
        "silver":    round(silver_seconds,    2),
        "gold":      round(gold_seconds,      2),
        "synthesis": round(synthesis_seconds, 2),
        "total":     round(total,             2),
    }

    metrics = _collect_metrics(new_ids)
    for m in metrics:
        m["batch_size"] = n

    return metrics, stage_times


def summarise(metrics: list[dict], stage_times: dict, n_requested: int) -> dict:
    n = len(metrics)
    relevant = [m for m in metrics if m.get("classifier_relevant") is True]

    def _sum(key):
        return sum(m.get(key) or 0 for m in metrics)

    def _avg(key, subset=None):
        src = subset if subset is not None else metrics
        vals = [m.get(key) for m in src if m.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    total_s = stage_times["total"]
    return {
        "n_docs_requested":       n_requested,
        "n_docs_ingested":        n,
        "n_relevant":             len(relevant),
        "n_with_synthesis":       sum(1 for m in metrics if m.get("syn_completeness_score") is not None),

        # Wall-clock seconds per stage
        "bronze_seconds":         stage_times["bronze"],
        "silver_seconds":         stage_times["silver"],
        "gold_seconds":           stage_times["gold"],
        "synthesis_seconds":      stage_times["synthesis"],
        "total_seconds":          total_s,

        # Throughput
        "docs_per_hour":          round(n / total_s * 3600, 1) if total_s > 0 else None,
        "avg_seconds_per_doc":    round(total_s / n, 2) if n > 0 else None,

        # Token totals
        "total_input_tokens":     _sum("total_input_tokens"),
        "total_output_tokens":    _sum("total_output_tokens"),
        "total_tokens":           _sum("total_tokens"),

        # Per-stage token totals
        "clf_input_tokens":       _sum("clf_input_tokens"),
        "clf_output_tokens":      _sum("clf_output_tokens"),
        "gold_input_tokens":      _sum("gold_input_tokens"),
        "gold_output_tokens":     _sum("gold_output_tokens"),
        "syn_input_tokens":       _sum("syn_input_tokens"),
        "syn_output_tokens":      _sum("syn_output_tokens"),

        # Per-document averages
        "avg_tokens_per_doc":     round(_sum("total_tokens") / n, 0) if n > 0 else None,
        "avg_cost_usd_per_doc":   round(_sum("cost_usd") / n, 6) if n > 0 else None,
        "total_cost_usd":         round(_sum("cost_usd"), 4),

        # LLM latency averages (ms, excludes bronze/chunking overhead)
        "avg_clf_duration_ms":    _avg("clf_duration_ms"),
        "avg_gold_duration_ms":   _avg("gold_duration_ms"),
        "avg_syn_duration_ms":    _avg("syn_duration_ms"),
        "avg_total_llm_ms":       _avg("total_llm_duration_ms"),

        # Chunk stats (relevant docs only)
        "avg_silver_chunks":      _avg("silver_chunk_count", relevant),
        "avg_gold_written":       _avg("gold_chunks_written", relevant),
        "avg_gold_discarded":     _avg("gold_chunks_discarded", relevant),
        "gold_discard_rate":      round(
            _sum("gold_chunks_discarded") /
            max(_sum("gold_chunks_written") + _sum("gold_chunks_discarded"), 1),
            3,
        ),
    }


def write_outputs(all_metrics: list[dict], summaries: list[dict], out_dir: Path, ts: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"benchmark_{ts}.json"
    json_path.write_text(json.dumps(
        {
            "generated_at": ts,
            "pricing": {
                "model": config.LLM_MODEL,
                "input_usd_per_token":  PRICE_INPUT_PER_TOKEN,
                "output_usd_per_token": PRICE_OUTPUT_PER_TOKEN,
            },
            "documents": all_metrics,
            "summaries": summaries,
        },
        indent=2, default=str,
    ))
    log.info("Full results → %s", json_path)

    if all_metrics:
        doc_csv = out_dir / f"benchmark_{ts}.csv"
        with doc_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_metrics[0].keys()))
            writer.writeheader()
            writer.writerows(all_metrics)
        log.info("Per-document CSV → %s", doc_csv)

    if summaries:
        summary_csv = out_dir / f"benchmark_summary_{ts}.csv"
        with summary_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
            writer.writeheader()
            writer.writerows(summaries)
        log.info("Summary CSV → %s", summary_csv)


def print_summary_table(summaries: list[dict]) -> None:
    print("\n── Benchmark summary ──────────────────────────────────────────────────────────────────────────────")
    print(f"{'N':>5}  {'Total(s)':>9}  {'Bronze(s)':>9}  {'Silver(s)':>9}  {'Gold(s)':>8}  {'Syn(s)':>7}  "
          f"{'doc/h':>6}  {'Tok/doc':>8}  {'Cost/doc':>9}  {'Total $':>8}  {'Disc%':>6}")
    print("-" * 102)
    for s in summaries:
        print(
            f"{s['n_docs_ingested']:>5}  "
            f"{s['total_seconds']:>9.1f}  "
            f"{s['bronze_seconds']:>9.1f}  "
            f"{s['silver_seconds']:>9.1f}  "
            f"{s['gold_seconds']:>8.1f}  "
            f"{s['synthesis_seconds']:>7.1f}  "
            f"{(s['docs_per_hour'] or 0):>6.0f}  "
            f"{(s['avg_tokens_per_doc'] or 0):>8.0f}  "
            f"{(s['avg_cost_usd_per_doc'] or 0):>9.6f}  "
            f"{s['total_cost_usd']:>8.4f}  "
            f"{s['gold_discard_rate']*100:>5.0f}%"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Feasibility benchmark")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--batch-sizes", type=int, nargs="+", default=[10, 20, 40, 80, 160],
        metavar="N",
        help="Batch sizes to run in sequence (default: 10 20 40 80 160). "
             "Each batch ingests N NEW documents from OData.",
    )
    group.add_argument(
        "--n-docs", type=int,
        help="Run a single batch of N documents (overrides --batch-sizes)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directory for output files (default: data/benchmark/)",
    )
    args = parser.parse_args()

    batch_sizes = [args.n_docs] if args.n_docs else sorted(set(args.batch_sizes))
    out_dir = Path(args.output_dir) if args.output_dir else Path(config.DATA_DIR) / "benchmark"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    log.info("Running migrations...")
    _run_migrations()

    bronze_repo = BronzeRepository()
    all_metrics: list[dict] = []
    summaries: list[dict] = []

    for n in batch_sizes:
        log.info("=== Batch n=%d ===", n)
        metrics, stage_times = run_batch(n, bronze_repo)
        all_metrics.extend(metrics)

        summary = summarise(metrics, stage_times, n)
        summaries.append(summary)
        log.info(
            "Batch n=%d done — total=%.1fs  bronze=%.1fs  silver=%.1fs  gold=%.1fs  syn=%.1fs  "
            "%.0f doc/h  avg %.0f tok/doc  $%.4f total",
            n,
            stage_times["total"], stage_times["bronze"], stage_times["silver"],
            stage_times["gold"], stage_times["synthesis"],
            summary["docs_per_hour"] or 0,
            summary["avg_tokens_per_doc"] or 0,
            summary["total_cost_usd"],
        )

    write_outputs(all_metrics, summaries, out_dir, ts)
    print_summary_table(summaries)


if __name__ == "__main__":
    main()
