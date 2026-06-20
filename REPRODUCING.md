# Reproducing the Thesis Results

This guide takes you from zero to a running pipeline and reproduces the validation results reported in Chapter 6. Follow the steps in order.

---

## Prerequisites

- Docker Desktop (tested with Docker 25+)
- An Anthropic API key **or** AWS account with Bedrock access in `eu-central-1`
- macOS or Linux (Windows with WSL2 should also work)

---

## Step 1 — Configure environment

Copy the template and fill in your credentials:

```bash
cd code/
cp .env.example .env
```

Edit `.env`:

```
# Choose your LLM provider
LLM_PROVIDER=anthropic          # or: bedrock

# If using Anthropic direct API:
ANTHROPIC_API_KEY=sk-ant-...

# If using AWS Bedrock:
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-central-1

# Leave DB settings as-is (Docker handles them)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=horizon_scanning
DB_USER=postgres
DB_PASSWORD=postgres
```

The model IDs default to `eu.anthropic.claude-sonnet-4-6` (Bedrock) or `claude-sonnet-4-6` (direct). These match the values used in the thesis.

---

## Step 2 — Start the database

```bash
cd code/
docker-compose up -d db
```

Wait a few seconds for Postgres to initialise, then verify:

```bash
docker-compose exec db pg_isready -U postgres
# Expected: /var/run/postgresql:5432 - accepting connections
```

---

## Step 3 — Apply database migrations

```bash
docker-compose run --rm pipeline python run_pipeline.py --stage bronze --limit 0
# This runs Alembic migrations on startup and exits immediately (limit 0 = no documents).
```

Or run Alembic directly:

```bash
docker-compose run --rm pipeline alembic upgrade head
```

---

## Step 4a — Reproduce the validation run (recommended)

This restores the exact database state from the thesis validation run without making any LLM calls.

```bash
# Load the SQL dump into the running database
docker-compose exec -T db psql -U postgres horizon_scanning \
  < ../validation/retrospective-detection/validation_db_dump_2026-05-17.sql
```

The database now contains all bronze, silver, gold, and synthesis records for the 10 validation documents. You can inspect the results via the API (Step 6) or query the DB directly.

---

## Step 4b — Re-run the pipeline on the sample documents

This re-runs the pipeline from scratch on the 10 validation documents, making live LLM calls. Results will be semantically equivalent but not token-identical to the thesis (LLM non-determinism).

**Seed the 10 validation documents into the database:**

```bash
# Copy the sample PDFs to the data mount
mkdir -p code/data/
cp data/sample_input/*.pdf code/data/

# Seed them as bronze records
docker-compose run --rm pipeline python seed_validation_docs.py
```

**Run the full pipeline:**

```bash
# Silver stage: extract text, classify, chunk
docker-compose run --rm pipeline python run_pipeline.py --stage silver

# Gold stage: extract norm frames
docker-compose run --rm pipeline python run_pipeline.py --stage gold

# Synthesis stage: merge gold records per document
docker-compose run --rm pipeline python run_pipeline.py --stage synthesis
```

Each stage is idempotent. Re-running a stage skips already-processed records.

---

## Step 4c — Fetch fresh documents from the Tweede Kamer API (optional)

This fetches new documents published since 2020-01-01 (the full dataset, ~335 documents as of May 2026).

```bash
docker-compose run --rm pipeline python run_pipeline.py --stage bronze
docker-compose run --rm pipeline python run_pipeline.py --stage silver
docker-compose run --rm pipeline python run_pipeline.py --stage gold
docker-compose run --rm pipeline python run_pipeline.py --stage synthesis
```

The bronze stage fetches document metadata from the OData API and downloads PDFs to `code/data/`. No authentication required — the API is public.

---

## Step 5 — Run the benchmark

Reproduces Table X in Section 6.x (token cost and latency per stage):

```bash
docker-compose run --rm pipeline python benchmark.py
```

Output is written to `code/data/benchmark_<timestamp>.json` and `.csv`. Reference results from the thesis are in `validation/feasibility-benchmark/benchmark/`.

---

## Step 6 — Inspect results via the review API

```bash
docker-compose up api
```

Open `http://localhost:8000/docs` for the Swagger UI.

Key endpoints:

| Endpoint | Description |
|---|---|
| `GET /signals` | All extracted signals (gold + synthesis records) |
| `GET /documents` | All ingested documents with their pipeline status |
| `PATCH /signals/{id}` | Mark a signal as reviewed / accepted / rejected |

---

## Step 7 — Single-document debug run

To inspect what the pipeline does to a specific document:

```bash
# Replace <doc-id> with any UUID from the bronze table
docker-compose run --rm pipeline python run_pipeline.py --doc-id 088132e5-f6bd-4124-a5ce-f1705be36e9a
```

This deletes existing silver/gold/synthesis rows for that document and re-runs all stages, logging each LLM call.

---

## Troubleshooting

**`pdftotext` not found** — The Dockerfile installs `poppler-utils`. If running outside Docker, install it manually:
- macOS: `brew install poppler`
- Ubuntu/Debian: `apt-get install poppler-utils`

**`relation "bronze_documents" does not exist`** — Migrations have not run yet. Run Step 3.

**AWS Bedrock `AccessDeniedException`** — Ensure model access is enabled in the Bedrock console for `eu.anthropic.claude-sonnet-4-6` in `eu-central-1`.

**Empty silver/gold output** — Check that `STAKEHOLDER_PROFILE` in `code/prompts/stakeholder_profile.md` is intact (FROZEN 2026-04-20). A corrupted profile causes the classifier to reject all chunks.
