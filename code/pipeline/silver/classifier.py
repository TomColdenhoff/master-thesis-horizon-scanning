"""Zero-shot domain classifier (task 24)."""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass

import config
from pipeline.llm.client import BaseLLMClient

log = logging.getLogger(__name__)

_MAX_WORDS = 3000


@dataclass
class ClassificationResult:
    relevant: bool
    reason: str
    input_tokens: int = 0
    output_tokens: int = 0


def classify(text: str, llm: BaseLLMClient) -> ClassificationResult:
    """Classify a document as relevant or irrelevant to the stakeholder profile.

    Args:
        text: Full extracted document text.
        llm: LLM client to use for the API call.

    Returns:
        ClassificationResult with relevant flag and one-sentence reason.

    Raises:
        ValueError: If the LLM response cannot be parsed as JSON.
    """
    truncated = _truncate(text, _MAX_WORDS)
    user_message = f"{config.STAKEHOLDER_PROFILE}\n\n{truncated}"

    completion = llm.complete(
        system=config.CLASSIFIER_SYSTEM_PROMPT,
        user=user_message,
        max_tokens=256,
    )

    classification = _parse(completion.text)
    classification.input_tokens = completion.input_tokens
    classification.output_tokens = completion.output_tokens
    return classification


def _truncate(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _parse(raw: str) -> ClassificationResult:
    payload = _extract_json(raw)
    try:
        data = json.loads(payload)
        return ClassificationResult(
            relevant=bool(data["relevant"]),
            reason=str(data["reason"]),
        )
    except (json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"Could not parse classifier response: {raw!r}") from exc


def _extract_json(raw: str) -> str:
    """Return the first {...} block from the response, or the raw string."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    return match.group(0) if match else raw
