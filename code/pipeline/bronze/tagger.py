"""Rule-based legislative stream tagger (task 22).

Assigns one of three stream tags to a document based on its Soort and Datum.
No LLM involved. Pure function — no I/O, no side effects.

Stream tags:
  eu_transposition  — Soort is in the EU set
  budget            — Datum falls in July, August, or September
  general           — all other documents
"""

from datetime import date
from typing import Optional

import config

STREAM_EU = "eu_transposition"
STREAM_BUDGET = "budget"
STREAM_GENERAL = "general"


def assign_stream_tag(soort: str, datum: Optional[date]) -> str:
    """Return the stream tag for a document.

    Args:
        soort: The Soort field value from the OData API.
        datum: The Datum field value. May be None for documents without a date.

    Returns:
        One of 'eu_transposition', 'budget', or 'general'.
    """
    if soort in config.EU_SOORTEN:
        return STREAM_EU
    if datum is not None and datum.month in config.BUDGET_MONTHS:
        return STREAM_BUDGET
    return STREAM_GENERAL
