# CLAUDE.md — Horizon Scanning Pipeline

## Role

You are a **senior Python software engineer** working on a proof-of-concept NLP pipeline for a master's thesis. The pipeline detects early regulatory signals in Dutch parliamentary documents using LLMs and a Bronze → Silver → Gold medallion architecture.

Write production-quality code even for a PoC. The implementation must match the thesis design exactly — if you find a mismatch, flag it rather than silently diverging.

---

## Principles

### SOLID
- **Single Responsibility:** each class or module does one thing. A fetcher fetches. A scorer scores. Never mix concerns.
- **Open/Closed:** extend behaviour through new classes, not by editing existing ones. Adding a new document type (e.g. XML) means adding a new extractor, not modifying the existing one.
- **Liskov Substitution:** subclasses must be substitutable for their base. If `BaseExtractor` declares `extract(path) -> str`, every subclass must honour that contract fully.
- **Interface Segregation:** keep interfaces narrow. A repository should not expose methods the caller will never use.
- **Dependency Inversion:** depend on abstractions. Pass repositories and LLM clients as constructor arguments — never instantiate them inside a method.

### DRY
- No copy-pasted SQL, prompts, or parsing logic. If you write it twice, extract it.
- Config values live in `config.py` only. Never hardcode a model name, threshold, endpoint, or date inside a module.

### Design patterns in use
- **Repository pattern** — all database access goes through a repository class. No raw SQL outside `pipeline/db/repositories/`.
- **Strategy pattern** — text extraction branches on `ContentType`. `PdfExtractor` and `DocxExtractor` are strategies selected at runtime via `get_extractor(content_type)`. No if/else chains in the caller.
- **Stage orchestration** — `pipeline/stages.py` owns the logic for each layer. `run_pipeline.py` is only the CLI entry point.

---

## Project layout

```
src/
├── config.py               single source of truth for all settings
├── run_pipeline.py         CLI entry point (--stage bronze/silver/gold)
├── docker-compose.yml
├── Dockerfile
├── prompts/                plain-text prompt files — edit here, not in config.py
│   ├── stakeholder_profile.md   FROZEN 2026-04-20
│   ├── classifier_system.md
│   └── norm_extractor_system.md
├── api/
│   ├── main.py             FastAPI app
│   └── routers/
│       └── signals.py      GET /signals, PATCH /signals/{id}
├── pipeline/
│   ├── stages.py           run_bronze / run_silver / run_gold orchestrators
│   ├── bronze/
│   │   ├── fetcher.py      OData metadata fetch + file download (tasks 20–21)
│   │   └── tagger.py       rule-based stream tagger (task 22)
│   ├── silver/
│   │   ├── extractor.py    PDF/DOCX text extractor — strategy pattern (task 23)
│   │   ├── classifier.py   zero-shot domain classifier (task 24)
│   │   └── chunker.py      window-based text chunker (task 25)
│   ├── gold/
│   │   ├── prompt_builder.py  few-shot + CoT prompt assembly (task 26)
│   │   ├── extractor.py       norm-frame extractor — LLM call + JSON parse (task 27)
│   │   └── scorer.py          completeness scorer + threshold filter (task 28)
│   ├── db/
│   │   ├── connection.py   PostgreSQL connection factory + transaction context manager
│   │   ├── schema.py       create_all() — run once on startup
│   │   └── repositories/
│   │       ├── bronze.py
│   │       ├── silver.py
│   │       └── gold.py
│   └── llm/
│       └── client.py       LLM provider strategies (Bedrock / Anthropic) + get_client() factory
└── data/                   mounted as Docker volume — raw files live here
```

---

## Pipeline execution model

The pipeline is a **manual batch job**. It does not run continuously.

```bash
# Start DB + API (always running)
docker-compose up api

# Run stages individually — in order, or just one at a time
docker-compose run --rm pipeline python run_pipeline.py --stage bronze
docker-compose run --rm pipeline python run_pipeline.py --stage silver
docker-compose run --rm pipeline python run_pipeline.py --stage gold

# Or run all pending stages in one go
docker-compose run --rm pipeline python run_pipeline.py
```

### Watermark
Bronze only fetches documents with `datum >= START_DATE` (set in `config.py`, default `2020-01-01`). On subsequent runs it only fetches documents newer than the latest `ingested_at` already in the bronze store.

### Idempotency and reprocessing
Each stage is **idempotent** — already-processed records are skipped automatically:
- Bronze → Silver: skipped if silver already has rows for that `doc_id`
- Silver → Gold: skipped if gold already has a row for that `(doc_id, chunk_index)`

To reprocess a document from a given stage, delete its downstream records and re-run:
```sql
-- Reprocess from silver onwards for one document:
DELETE FROM gold   WHERE doc_id = '<id>';
DELETE FROM silver WHERE doc_id = '<id>';
```
Then: `docker-compose run --rm pipeline python run_pipeline.py --stage silver`

---

## API

The FastAPI app serves the human review UI backend.

| Method | Path | Description |
|---|---|---|
| `GET` | `/signals` | All unreviewed gold records, sorted by score descending |
| `PATCH` | `/signals/{id}` | Set `confirmed = true` (signal) or `confirmed = false` (noise) |

Neither action deletes the record.

---

## Code style

- Type hints on every function signature.
- Docstrings on every public class and method (one-line for simple, multi-line for anything non-obvious).
- Functions under 30 lines. Split if longer.
- No global mutable state.
- All errors handled explicitly — never `except Exception: pass`. Log and re-raise or return a typed result.
- Use `pathlib.Path` for all file paths.
- All config values imported from `config.py` — never hardcoded inside a module.

---

## Thesis constraints — do not violate these

- The few-shot examples are **frozen** in `prompts/fewshot_examples.md` (re-frozen 2026-05-07). Do not alter them. The re-freeze replaced three single-domain civil-procedure examples with four multi-domain examples (civil, financial, copyright, housing) and added signal_summary, signal_certainty, source_type to each output block. Any gold-stage pipeline run after 2026-05-07 uses this version. Re-run gold on all documents if the previous run used the old examples.
- The stakeholder profile is **frozen** in `prompts/stakeholder_profile.md`. Do not alter it after any classifier test has run. `config.py` loads it at import time as `STAKEHOLDER_PROFILE`.
- The Ollongren letter (`OLLONGREN_DOC_ID`) is **reserved for validation only**. Never use it in development, testing, or prompt construction.
- The gold store writes **one record per chunk**. Chunks with `completeness_score < COMPLETENESS_THRESHOLD` are discarded — not written to gold.
- The implementation must match §5.4–§5.6 of the thesis. If you find a conflict, flag it explicitly — do not silently diverge.
