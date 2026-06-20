"""Norm-frame extractor: sends prompt to LLM and parses response (task 27)."""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass

from pipeline.gold.prompt_builder import build_prompt
from pipeline.llm.client import BaseLLMClient

log = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    norm_frame: dict
    reasoning: str
    signal_summary: str = ""
    signal_certainty: str = ""
    source_type: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


def extract(chunk_text: str, llm: BaseLLMClient) -> ExtractionResult:
    """Extract a Van Kralingen norm frame from a silver chunk.

    Args:
        chunk_text: Plain text of the chunk to analyse.
        llm: LLM client to use for the API call.

    Returns:
        ExtractionResult with parsed norm_frame, raw reasoning, and token counts.

    Raises:
        ValueError: If the LLM response cannot be parsed after one retry.
    """
    system, user = build_prompt(chunk_text)
    result = llm.complete(system=system, user=user, max_tokens=1024)

    try:
        return _parse(result.text, result.input_tokens, result.output_tokens)
    except ValueError:
        log.warning("First parse attempt failed — retrying once")
        result = llm.complete(system=system, user=user, max_tokens=1024)
        return _parse(result.text, result.input_tokens, result.output_tokens)


def _parse(raw: str, input_tokens: int, output_tokens: int) -> ExtractionResult:
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse norm-frame JSON: {raw!r}") from exc

    signal_summary   = data.pop("signal_summary",   "")
    signal_certainty = data.pop("signal_certainty", "")
    source_type      = data.pop("source_type",      "")
    reasoning = raw[:raw.rfind("```")].strip() if "```" in raw else ""
    return ExtractionResult(
        norm_frame=data,
        reasoning=reasoning,
        signal_summary=signal_summary,
        signal_certainty=signal_certainty,
        source_type=source_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _extract_json(raw: str) -> str:
    """Extract the last ```json ... ``` block, falling back to bare {...}."""
    matches = re.findall(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if matches:
        return matches[-1]
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return match.group(0)
    return raw
