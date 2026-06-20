"""Pipeline entry point.

Each stage is independent and idempotent. Run one stage at a time or all in sequence.

Usage:
    python run_pipeline.py                         # run all pending stages
    python run_pipeline.py --stage bronze          # fetch new documents only
    python run_pipeline.py --stage backfill        # populate raw_text for existing bronze records
    python run_pipeline.py --stage silver          # classify + chunk unprocessed bronze docs
    python run_pipeline.py --stage gold            # extract frames from unprocessed silver chunks
    python run_pipeline.py --stage synthesis       # synthesise gold records into unified document records

Isolated single-document run (useful for validation):
    python run_pipeline.py --doc-id <id>           # run silver → gold → synthesis for one document
    python run_pipeline.py --doc-id <id> --stage gold  # only the gold stage for one document

    The bronze record must already exist.  --doc-id forces the named stages (or all of
    silver/gold/synthesis when no --stage is given) to operate on that document only,
    even if a record for it already exists in the downstream store (idempotency is
    bypassed by deleting the existing rows first).

Reprocessing a document from synthesis:
    1. DELETE FROM synthesis WHERE doc_id = '<id>';
    2. python run_pipeline.py --stage synthesis
    To reprocess from silver: also delete silver + gold rows, then re-run silver.
"""

import argparse
import logging
import time
from pathlib import Path

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from pipeline.stages import run_bronze, run_bronze_backfill, run_silver, run_gold, run_synthesis, run_single_doc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

STAGES = ["bronze", "backfill", "silver", "gold", "synthesis"]
# Stages that make sense for a single-document run
_DOC_STAGES = ["silver", "gold", "synthesis"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Horizon scanning pipeline runner")
    parser.add_argument(
        "--stage",
        choices=STAGES,
        default=None,
        help="Run a single stage only. Omit to run all pending stages in sequence.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of documents processed. Applies to bronze, gold, and synthesis.",
    )
    parser.add_argument(
        "--from-stage",
        choices=STAGES,
        default=None,
        dest="from_stage",
        help="Start the pipeline from this stage, skipping all earlier ones.",
    )
    parser.add_argument(
        "--doc-id",
        default=None,
        metavar="ID",
        help=(
            "Run the pipeline for a single document (bronze record must already exist). "
            "Existing silver/gold/synthesis rows for this doc_id are deleted first so the "
            "document is always reprocessed. Combine with --stage to restrict to one stage."
        ),
    )
    return parser.parse_args()


def _run_migrations() -> None:
    ini_path = Path(__file__).parent / "alembic.ini"
    cfg = AlembicConfig(str(ini_path))
    alembic_command.upgrade(cfg, "head")


def main() -> None:
    args = parse_args()
    _run_migrations()

    # --- single-document mode ---
    if args.doc_id:
        stages_to_run = [args.stage] if args.stage in _DOC_STAGES else _DOC_STAGES
        invalid = args.stage and args.stage not in _DOC_STAGES
        if invalid:
            log.warning(
                "--doc-id is only compatible with stages: %s. Ignoring --stage %s.",
                ", ".join(_DOC_STAGES), args.stage,
            )
        log.info("Single-document mode: doc_id=%s stages=%s", args.doc_id, stages_to_run)
        t0 = time.perf_counter()
        run_single_doc(args.doc_id, stages_to_run)
        log.info("Single-document run complete in %.1fs", time.perf_counter() - t0)
        return

    # --- normal (all-documents) mode ---
    if args.stage:
        stages_to_run = [args.stage]
    elif args.from_stage:
        stages_to_run = STAGES[STAGES.index(args.from_stage):]
    else:
        stages_to_run = STAGES
    pipeline_start = time.perf_counter()

    for stage in stages_to_run:
        t0 = time.perf_counter()
        log.info("── Stage start: %s", stage)
        if stage == "bronze":
            run_bronze(limit=args.limit)
        elif stage == "backfill":
            run_bronze_backfill()
        elif stage == "silver":
            run_silver()
        elif stage == "gold":
            run_gold(limit=args.limit)
        elif stage == "synthesis":
            run_synthesis(limit=args.limit)
        log.info("── Stage done:  %s  (%.1fs)", stage, time.perf_counter() - t0)

    log.info("Pipeline complete in %.1fs", time.perf_counter() - pipeline_start)


if __name__ == "__main__":
    main()
