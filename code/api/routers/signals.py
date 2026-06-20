"""Signal review endpoints (task 29, updated tasks 30c/30d/supervisor feedback).

GET  /signals              — unreviewed synthesis records, sorted by score desc
GET  /signals/reviewed     — all reviewed records grouped by status
GET  /signals/{id}/chunks  — gold chunks for a synthesis record (lazy-loaded)
PATCH /signals/{id}        — set review_status (strong | weak | unsure | discarded)
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline.db.repositories.synthesis import SynthesisRepository, REVIEW_STATUSES
from pipeline.db.repositories.gold import GoldRepository

router = APIRouter(prefix="/signals", tags=["signals"])

_NORM_FRAME_KEYS = (
    "norm_identifier", "norm_type", "promulgation", "scope",
    "conditions", "subject", "legal_modality", "act_identifier",
)


class NormFrameOut(BaseModel):
    norm_identifier: str
    norm_type: str
    promulgation: str
    scope: str
    conditions: str
    subject: str
    legal_modality: str
    act_identifier: str


class SignalOut(BaseModel):
    id: int
    doc_id: str
    norm_frame: NormFrameOut
    completeness_score: str
    stream_tag: str
    confirmed: Optional[bool]
    review_status: Optional[str]
    timestamp: Optional[datetime]
    onderwerp: Optional[str]
    soort: str
    datum: Optional[date]
    tk_url: str
    signal_summary: Optional[str]
    signal_certainty: Optional[str]
    source_type: Optional[str]
    expected_date: Optional[str]
    affected_sectors: list[str]
    sector_reasons: dict
    client_action: Optional[str]
    chunk_index: Optional[int] = None
    chunk_text: Optional[str] = None


class ChunkOut(BaseModel):
    chunk_index: int
    chunk_text: str
    completeness_score: int
    signal_summary: str


class ReviewRequest(BaseModel):
    status: str  # strong | weak | unsure | discarded


def _norm_frame_out(raw: dict) -> NormFrameOut:
    return NormFrameOut(**{k: str(raw.get(k) or "") for k in _NORM_FRAME_KEYS})


def _to_signal_out(s) -> SignalOut:
    return SignalOut(
        id=s.synthesis_id,
        doc_id=s.doc_id,
        norm_frame=_norm_frame_out(s.norm_frame),
        completeness_score=f"{s.completeness_score}/8",
        stream_tag=s.stream_tag,
        confirmed=s.confirmed,
        review_status=s.review_status,
        timestamp=s.timestamp,
        onderwerp=s.onderwerp,
        soort=s.soort,
        datum=s.datum,
        tk_url=f"/documents/{s.doc_id}",
        signal_summary=s.signal_summary,
        signal_certainty=s.signal_certainty,
        source_type=s.source_type,
        expected_date=s.expected_date or None,
        affected_sectors=s.affected_sectors,
        sector_reasons=s.sector_reasons,
        client_action=s.client_action or None,
    )


@router.get("", response_model=list[SignalOut])
def list_signals() -> list[SignalOut]:
    """Return all unreviewed synthesis records, sorted by completeness score descending."""
    repo = SynthesisRepository()
    records = repo.get_all_unreviewed(unreviewed_only=True)
    if records:
        return [_to_signal_out(s) for s in records]

    # Fallback: synthesis not yet run — serve from gold (best chunk per doc)
    gold_repo = GoldRepository()
    return [
        SignalOut(
            id=s.gold_id,
            doc_id=s.doc_id,
            norm_frame=_norm_frame_out(s.norm_frame),
            completeness_score=f"{s.completeness_score}/8",
            stream_tag=s.stream_tag,
            confirmed=s.confirmed,
            review_status=None,
            timestamp=s.timestamp,
            onderwerp=s.onderwerp,
            soort=s.soort,
            datum=s.datum,
            tk_url=f"/documents/{s.doc_id}",
            signal_summary=s.signal_summary,
            signal_certainty=s.signal_certainty,
            source_type=s.source_type,
            expected_date=None,
            affected_sectors=[],
            sector_reasons={},
            client_action=None,
            chunk_index=s.chunk_index,
            chunk_text=s.chunk_text,
        )
        for s in gold_repo.get_document_signals(unreviewed_only=True)
    ]


@router.get("/reviewed", response_model=list[SignalOut])
def list_reviewed() -> list[SignalOut]:
    """Return all reviewed synthesis records ordered by review_status then score."""
    repo = SynthesisRepository()
    return [_to_signal_out(s) for s in repo.get_reviewed()]


@router.get("/{signal_id}/chunks", response_model=list[ChunkOut])
def get_signal_chunks(signal_id: int) -> list[ChunkOut]:
    """Return all gold chunks for the document behind a synthesis record."""
    repo = SynthesisRepository()
    all_records = repo.get_all_unreviewed(unreviewed_only=False) + repo.get_reviewed()
    match = next((r for r in all_records if r.synthesis_id == signal_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    gold_repo = GoldRepository()
    return [ChunkOut(**c) for c in gold_repo.get_chunks_for_doc(match.doc_id)]


@router.patch("/{signal_id}", status_code=204)
def review_signal(signal_id: int, body: ReviewRequest) -> None:
    """Set review_status: strong | weak | unsure | discarded."""
    if body.status not in REVIEW_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status {body.status!r}. Choose from {REVIEW_STATUSES}",
        )
    repo = SynthesisRepository()
    repo.set_review_status(signal_id, body.status)
