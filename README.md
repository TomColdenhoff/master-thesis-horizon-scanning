# Replication Package — Horizon Scanning Pipeline

**Thesis:** *Detecting Early Regulatory Signals in Dutch Parliamentary Documents Using LLMs*
**Author:** Tom Coldenhoff
**Institution:** Utrecht University, MSc Business Informatics
**Date:** June 2026

---

## Overview

This package contains all code, prompts, data, and results needed to understand and reproduce the proof-of-concept pipeline described in the thesis. The pipeline detects early regulatory signals in Dutch parliamentary documents using a Bronze → Silver → Gold medallion architecture backed by LLM calls (Claude).

### What this package contains

```
replication-package/
├── README.md                      ← this file
├── REPRODUCING.md                 ← step-by-step instructions to run the pipeline
├── code/                          ← full pipeline source code
│   ├── run_pipeline.py            ← CLI entry point
│   ├── config.py                  ← all settings and constants
│   ├── requirements.txt           ← Python dependencies (minimum versions)
│   ├── requirements-frozen.txt    ← exact versions used in the thesis
│   ├── Dockerfile                 ← container image definition
│   ├── docker-compose.yml         ← orchestrates DB + pipeline + API
│   ├── .env.example               ← template for environment variables
│   ├── prompts/                   ← LLM prompt files (see note below)
│   ├── pipeline/                  ← bronze / silver / gold / synthesis stages
│   ├── api/                       ← FastAPI review interface
│   ├── alembic/                   ← database migration scripts
│   └── ui/                        ← terminal review UI
├── data/
│   └── sample_input/              ← 10 validation documents (PDF, from Tweede Kamer OData API)
└── validation/
    ├── retrospective-detection/   ← RQ6 feasibility validation run (2026-05-17)
    ├── feasibility-benchmark/     ← token cost + latency benchmark (2026-05-18)
    └── interview-coding/          ← coded expert interview themes (anonymised)
```

---

## Key design decisions

| Decision | Value used in thesis |
|---|---|
| LLM model | `eu.anthropic.claude-sonnet-4-6` (AWS Bedrock, EU region) |
| Chunk size | 2500 tokens, 400 token overlap |
| Completeness threshold | 5 / 10 (chunks below this are discarded) |
| Stakeholder profile | FROZEN 2026-04-20 — `code/prompts/stakeholder_profile.md` |
| Document types ingested | Brief regering, Antwoord schriftelijke vragen, EU-voorstel, Brief Europese Commissie, Lijst met EU-voorstellen |
| Data source | Tweede Kamer OData API v4 — `https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0` |
| Date range | 2020-01-01 onwards |

---

## Important notes on reproducibility

**LLM non-determinism.** The pipeline calls Claude with default temperature settings. Re-running the pipeline on the same documents will produce outputs that are semantically equivalent but not token-identical to the results in the thesis. The validation SQL dump (`validation/retrospective-detection/validation_db_dump_2026-05-17.sql`) contains the exact outputs used for evaluation.

**Model versioning.** Results were produced with `eu.anthropic.claude-sonnet-4-6` as it existed in May 2026. Anthropic may update this model; behaviour may differ on later versions.

**Prompts are frozen.** The stakeholder profile and extractor prompts were frozen before any validation runs. Do not modify `code/prompts/stakeholder_profile.md` if you want to reproduce the thesis results — changing it invalidates the comparison.

**Data access.** The Tweede Kamer OData API is publicly accessible without authentication. The 10 documents in `data/sample_input/` are sufficient to reproduce the validation run. The full dataset (~335 documents) can be re-fetched by running the bronze stage; see `REPRODUCING.md`.

**Interview data.** Expert interview recordings and full transcripts are not included in this package to protect participant privacy (consent was obtained for research use only, not public archival). Anonymised theme summaries are in `validation/interview-coding/`.

---

## Software versions

- Python 3.12 (tested; 3.11+ should work)
- PostgreSQL 16 (via Docker)
- poppler-utils (system dependency for PDF text extraction)
- See `code/requirements-frozen.txt` for exact Python package versions
