# Pipeline configuration — freeze values before any classifier testing
# Task 12: stakeholder profile FROZEN 2026-04-20

import os
from pathlib import Path as _Path

def _load_prompt(name: str) -> str:
    """Load a prompt file from src/prompts/<name>.md, stripped of surrounding whitespace."""
    return (_Path(__file__).parent / "prompts" / name).read_text(encoding="utf-8").strip()

# ── LLM ──────────────────────────────────────────────────────────────────────
# Provider: "bedrock" (AWS) or "anthropic" (direct API)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "bedrock")

# Model IDs — use Bedrock IDs when LLM_PROVIDER="bedrock", plain IDs otherwise.
# Bedrock IDs: verify in AWS console under Bedrock > Model access.
LLM_MODEL        = os.environ.get("LLM_MODEL",        "eu.anthropic.claude-sonnet-4-6")
CLASSIFIER_MODEL = os.environ.get("CLASSIFIER_MODEL", "eu.anthropic.claude-sonnet-4-6")

# ── OData API ─────────────────────────────────────────────────────────────────
ODATA_BASE = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0"
ODATA_MAX_PAGE = 250  # hard API limit per request

# Watermark: only fetch documents on or after this date.
# Prevents processing the entire archive on first run.
START_DATE = "2020-01-01"

# Soort values that route to each stream.
# Note: §5.4.1 lists "Kamervraag" and "Toezegging" — actual API Soort labels differ:
#   "Kamervraag" → "Schriftelijke vragen" (questions) + "Antwoord schriftelijke vragen" (answers)
#   "Toezegging" → separate /Toezegging entity, not a Document Soort value
EU_SOORTEN = {"EU-voorstel", "Brief Europese Commissie", "Lijst met EU-voorstellen"}
BUDGET_MONTHS = {7, 8, 9}  # July–September (pre-Prinsjesdag window)

# Soort values ingested by the pipeline.
# Only documents with one of these values are fetched from the OData API.
#
# Deliberately excluded:
#   "Schriftelijke vragen"    — MP questions, not government intent
#   "Motie"                   — parliamentary motions filed by MPs, not government
#   "Memorie van toelichting" — explanatory memo for a bill already before parliament;
#                               by this stage the signal has materialised into formal legislation
RELEVANT_SOORTEN = {
    "Brief regering",                # minister letters to parliament — core signal source
    "Antwoord schriftelijke vragen", # minister answers — can contain explicit commitments
    "EU-voorstel",                   # EU proposals requiring transposition
    "Brief Europese Commissie",      # EC letters signalling upcoming EU regulation
    "Lijst met EU-voorstellen",      # VWS/other monthly EU pipeline lists
}

# ── Text chunker ──────────────────────────────────────────────────────────────
CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE",    2500))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 400))  # must be >= longest key passage (~127 chars)

# ── Gold store threshold ───────────────────────────────────────────────────────
# Chunks with completeness_score < this value are discarded before writing to gold.
# Score 0–1 indicates a background passage with no normative content.
COMPLETENESS_THRESHOLD = 5

# ── Prompts (loaded from src/prompts/*.md — edit the files, not this block) ──
# Stakeholder profile FROZEN 2026-04-20 — do not change after any classifier test
STAKEHOLDER_PROFILE = _load_prompt("stakeholder_profile.md")
CLASSIFIER_SYSTEM_PROMPT = _load_prompt("classifier_system.md")
NORM_EXTRACTOR_SYSTEM_PROMPT = _load_prompt("norm_extractor_system.md")
SYNTHESIS_SYSTEM_PROMPT = _load_prompt("synthesis_system.md")
FEWSHOT_EXAMPLES_PATH = _Path(__file__).parent / "prompts" / "fewshot_examples.md"

# Version string for the frozen profile — stored in silver alongside each accepted chunk
PROFILE_VERSION = "v1-2026-04-20"

# ── Key document IDs (confirmed 2026-04-20) ───────────────────────────────────
OLLONGREN_DOC_ID = "088132e5-f6bd-4124-a5ce-f1705be36e9a"   # 27 926, nr. 337 — test case
MVT_DOC_ID       = "1ebe8099-a6db-41f9-afcc-32e61da718d7"   # 36 130, nr. 3   — ground truth
FEWSHOT_DOC_ID   = "f5424e09-a713-4c80-ab1e-daa6cb803e8a"   # 29 279, nr. 1020 — few-shot source

# ── Local data paths ──────────────────────────────────────────────────────────
DATA_DIR = "data"
