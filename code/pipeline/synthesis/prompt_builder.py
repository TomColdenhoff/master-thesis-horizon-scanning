"""Assembles the synthesis prompt from all gold records for one document."""

from __future__ import annotations
from functools import lru_cache

import config


def build_prompt(fragments: list[dict]) -> tuple[str, str]:
    """Assemble system and user prompts for the synthesis stage.

    Args:
        fragments: List of dicts, each with keys:
            chunk_index, chunk_text, signal_summary, signal_certainty,
            source_type, norm_frame (dict), reasoning.

    Returns:
        Tuple of (system_prompt, user_message).
    """
    system = _synthesis_system()
    user = _format_fragments(fragments)
    return system, user


@lru_cache(maxsize=1)
def _synthesis_system() -> str:
    return config.SYNTHESIS_SYSTEM_PROMPT


def _format_fragments(fragments: list[dict]) -> str:
    lines: list[str] = [
        f"I have {len(fragments)} norm-frame fragment(s) from a single document. "
        "Please synthesise them into one unified record.\n"
    ]
    for i, frag in enumerate(fragments, 1):
        lines.append(f"## Fragment {i} (chunk {frag.get('chunk_index', '?')})")
        if frag.get("chunk_text"):
            lines.append(f"**Source passage:** \"{frag['chunk_text'][:600]}\"")
        if frag.get("signal_summary"):
            lines.append(f"**Signal summary:** {frag['signal_summary']}")
        if frag.get("signal_certainty"):
            lines.append(f"**Signal certainty:** {frag['signal_certainty']}")
        if frag.get("source_type"):
            lines.append(f"**Source type:** {frag['source_type']}")
        nf = frag.get("norm_frame") or {}
        for key, val in nf.items():
            if val:
                lines.append(f"**{key}:** {val}")
        if frag.get("reasoning"):
            lines.append(f"**Reasoning:** {frag['reasoning'][:300]}")
        lines.append("")
    lines.append("Now synthesise these fragments into one unified norm frame.")
    return "\n".join(lines)
