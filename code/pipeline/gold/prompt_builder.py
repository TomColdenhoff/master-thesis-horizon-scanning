"""Assembles the few-shot + CoT prompt for the norm-frame extractor (task 26)."""

from __future__ import annotations
from functools import lru_cache

import config

_NORM_FRAME_KEYS = (
    "norm_identifier", "norm_type", "promulgation", "scope",
    "conditions", "subject", "legal_modality", "act_identifier",
)


def build_prompt(chunk_text: str) -> tuple[str, str]:
    """Assemble the system and user prompts for the norm-frame extractor.

    Args:
        chunk_text: Plain text of the silver chunk to analyse.

    Returns:
        Tuple of (system_prompt, user_message).
    """
    system = config.NORM_EXTRACTOR_SYSTEM_PROMPT
    user = f"{_fewshot_examples()}\n\n---\n\nNow extract the norm frame from this chunk:\n\n\"{chunk_text}\""
    return system, user


@lru_cache(maxsize=1)
def _fewshot_examples() -> str:
    """Load and cache the frozen few-shot examples."""
    return config.FEWSHOT_EXAMPLES_PATH.read_text(encoding="utf-8").strip()
