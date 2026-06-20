"""Synthesis extractor: sends all gold fragments for a document to the LLM
and parses the unified norm-frame response."""

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field

from pipeline.synthesis.prompt_builder import build_prompt
from pipeline.llm.client import BaseLLMClient

log = logging.getLogger(__name__)

_NORM_FRAME_KEYS = (
    "norm_identifier", "norm_type", "promulgation", "scope",
    "conditions", "subject", "legal_modality", "act_identifier",
)

_NULL_EQUIVALENTS = frozenset({
    "n/a", "unknown", "not specified", "not applicable",
    "none", "null", "not stated", "not mentioned", "unspecified",
})


@dataclass
class SynthesisResult:
    norm_frame: dict
    signal_summary: str
    signal_certainty: str
    source_type: str
    expected_date: str
    affected_sectors: list[str]
    sector_reasons: dict
    client_action: str
    completeness_score: int
    reasoning: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


def synthesise(fragments: list[dict], llm: BaseLLMClient) -> SynthesisResult:
    """Synthesise all gold fragments for one document into a unified record.

    Args:
        fragments: List of dicts with keys chunk_index, chunk_text,
            signal_summary, signal_certainty, source_type, norm_frame, reasoning.
        llm: LLM client to call.

    Returns:
        SynthesisResult with all fields populated from the LLM response.

    Raises:
        ValueError: If the LLM response cannot be parsed after one retry.
    """
    system, user = build_prompt(fragments)
    result = llm.complete(system=system, user=user, max_tokens=1500)

    try:
        return _parse(result.text, result.input_tokens, result.output_tokens)
    except ValueError:
        log.warning("Synthesis parse failed — retrying once")
        result = llm.complete(system=system, user=user, max_tokens=1500)
        return _parse(result.text, result.input_tokens, result.output_tokens)


def _parse(raw: str, input_tokens: int, output_tokens: int) -> SynthesisResult:
    json_str = _extract_json(raw)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse synthesis JSON: {raw!r}") from exc

    norm_frame = {k: str(data.pop(k, "") or "") for k in _NORM_FRAME_KEYS}
    signal_summary   = str(data.pop("signal_summary",   "") or "")
    signal_certainty = str(data.pop("signal_certainty", "") or "")
    source_type      = str(data.pop("source_type",      "") or "")
    expected_date    = str(data.pop("expected_date",     "") or "")
    client_action    = str(data.pop("client_action",     "") or "")
    raw_sectors      = data.pop("affected_sectors", [])
    affected_sectors = [str(s) for s in raw_sectors] if isinstance(raw_sectors, list) else []
    raw_reasons      = data.pop("sector_reasons", {})
    sector_reasons   = {str(k): str(v) for k, v in raw_reasons.items()} if isinstance(raw_reasons, dict) else {}

    reasoning = raw[:raw.rfind("```")].strip() if "```" in raw else ""

    completeness = sum(
        1 for k in _NORM_FRAME_KEYS
        if norm_frame.get(k, "").strip()
        and norm_frame[k].strip().lower() not in _NULL_EQUIVALENTS
    )

    return SynthesisResult(
        norm_frame=norm_frame,
        signal_summary=signal_summary,
        signal_certainty=signal_certainty,
        source_type=source_type,
        expected_date=expected_date,
        affected_sectors=affected_sectors,
        sector_reasons=sector_reasons,
        client_action=client_action,
        completeness_score=completeness,
        reasoning=reasoning,
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
