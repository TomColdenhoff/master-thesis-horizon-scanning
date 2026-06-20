"""Completeness scorer and gold store threshold filter (task 28)."""

from __future__ import annotations

_NORM_FRAME_KEYS = (
    "norm_identifier", "norm_type", "promulgation", "scope",
    "conditions", "subject", "legal_modality", "act_identifier",
)


_NULL_EQUIVALENTS = frozenset({
    "n/a", "unknown", "not specified", "not applicable",
    "none", "null", "not stated", "not mentioned", "unspecified",
})


def score(norm_frame: dict) -> int:
    """Count how many of the 8 norm-frame fields are substantively filled.

    Fields that contain only null-equivalent placeholders (e.g. "N/A",
    "unknown") are treated as empty to prevent inflated scores.

    Returns:
        Integer 0–8. Higher means more complete.
    """
    def _is_filled(value: object) -> bool:
        s = str(value).strip()
        return bool(s) and s.lower() not in _NULL_EQUIVALENTS

    return sum(1 for key in _NORM_FRAME_KEYS if _is_filled(norm_frame.get(key, "")))
