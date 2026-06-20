"""Repository for the gold store."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from pipeline.db.connection import transaction


@dataclass
class GoldRecord:
    doc_id: str
    chunk_index: int
    norm_frame: dict
    completeness_score: int
    stream_tag: str
    reasoning: Optional[str] = None
    signal_summary: Optional[str] = None
    signal_certainty: Optional[str] = None
    source_type: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    id: Optional[int] = None
    confirmed: Optional[bool] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None


@dataclass
class DocumentSignal:
    """Best gold record for a document, enriched with bronze metadata."""
    gold_id: int
    doc_id: str
    chunk_index: int
    norm_frame: dict
    reasoning: Optional[str]
    signal_summary: Optional[str]
    signal_certainty: Optional[str]
    source_type: Optional[str]
    completeness_score: int
    stream_tag: str
    confirmed: Optional[bool]
    timestamp: Optional[datetime]
    onderwerp: Optional[str]
    soort: str
    datum: Optional[date]
    vergaderjaar: Optional[str]
    chunk_text: Optional[str] = None


class GoldRepository:
    """All read/write access to the gold store."""

    def insert(self, record: GoldRecord) -> int:
        """Insert a signal record and return the generated id."""
        import json
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO gold
                    (doc_id, chunk_index, norm_frame, reasoning, signal_summary,
                     signal_certainty, source_type,
                     completeness_score, stream_tag, input_tokens, output_tokens, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    record.doc_id, record.chunk_index,
                    json.dumps(record.norm_frame),
                    record.reasoning,
                    record.signal_summary,
                    record.signal_certainty,
                    record.source_type,
                    record.completeness_score, record.stream_tag,
                    record.input_tokens, record.output_tokens,
                    record.duration_ms,
                ),
            )
            return cur.fetchone()[0]

    def get_document_signals(self, unreviewed_only: bool = False) -> list[DocumentSignal]:
        """Return the best-scoring non-existing gold record per document, with bronze metadata.

        Uses DISTINCT ON (doc_id) ordered by completeness_score DESC so the
        highest-scoring chunk represents each document in the review UI.
        Excludes records where source_type or signal_certainty is 'existing' —
        those describe current law, not early warning signals.
        """
        conditions = [
            "(g.source_type IS NULL OR g.source_type != 'existing')",
            "(g.signal_certainty IS NULL OR g.signal_certainty != 'existing')",
        ]
        if unreviewed_only:
            conditions.append("g.confirmed IS NULL")
        where = "WHERE " + " AND ".join(conditions)
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT DISTINCT ON (g.doc_id)
                    g.id, g.doc_id, g.chunk_index, g.norm_frame, g.reasoning,
                    g.signal_summary, g.signal_certainty, g.source_type,
                    g.completeness_score, g.stream_tag,
                    g.confirmed, g.timestamp,
                    b.onderwerp, b.soort, b.datum, b.vergaderjaar,
                    s.chunk_text
                FROM gold g
                JOIN bronze b ON b.id = g.doc_id
                LEFT JOIN LATERAL (
                    SELECT chunk_text FROM silver
                    WHERE doc_id = g.doc_id AND chunk_index = g.chunk_index
                    ORDER BY id DESC LIMIT 1
                ) s ON true
                {where}
                ORDER BY g.doc_id, g.completeness_score DESC, g.timestamp DESC
                """
            )
            return [self._row_to_signal_with_chunk(row) for row in cur.fetchall()]

    def get_chunks_for_doc(self, doc_id: str) -> list[dict]:
        """Return all gold chunks for a document, ordered by chunk_index.

        Each dict has: chunk_index, chunk_text, completeness_score, signal_summary.
        """
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.chunk_index, s.chunk_text,
                       g.completeness_score, g.signal_summary
                FROM gold g
                LEFT JOIN LATERAL (
                    SELECT chunk_text FROM silver
                    WHERE doc_id = g.doc_id AND chunk_index = g.chunk_index
                    ORDER BY id DESC LIMIT 1
                ) s ON true
                WHERE g.doc_id = %s
                ORDER BY g.chunk_index
                """,
                (doc_id,),
            )
            return [
                {
                    "chunk_index": row[0],
                    "chunk_text": row[1] or "",
                    "completeness_score": row[2],
                    "signal_summary": row[3] or "",
                }
                for row in cur.fetchall()
            ]

    def get_all_unreviewed_signals(self) -> list[DocumentSignal]:
        """Return all unreviewed gold records (one per chunk) with bronze and silver metadata."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT g.id, g.doc_id, g.chunk_index, g.norm_frame, g.reasoning,
                       g.signal_summary, g.signal_certainty, g.source_type,
                       g.completeness_score, g.stream_tag,
                       g.confirmed, g.timestamp,
                       b.onderwerp, b.soort, b.datum, b.vergaderjaar,
                       s.chunk_text
                FROM gold g
                JOIN bronze b ON b.id = g.doc_id
                LEFT JOIN LATERAL (
                    SELECT chunk_text FROM silver
                    WHERE doc_id = g.doc_id AND chunk_index = g.chunk_index
                    ORDER BY id DESC LIMIT 1
                ) s ON true
                WHERE g.confirmed IS NULL
                ORDER BY g.completeness_score DESC, g.timestamp DESC
                """
            )
            return [self._row_to_signal_with_chunk(row) for row in cur.fetchall()]

    def get_all_unreviewed(self) -> list[GoldRecord]:
        """Return all records not yet confirmed or discarded, sorted by score descending."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, doc_id, chunk_index, norm_frame, reasoning, signal_summary,
                       signal_certainty, source_type,
                       completeness_score, stream_tag, confirmed, timestamp
                FROM gold
                WHERE confirmed IS NULL
                ORDER BY completeness_score DESC, timestamp DESC
                """,
            )
            return [self._row_to_record(row) for row in cur.fetchall()]

    def set_confirmed(self, record_id: int, confirmed: bool) -> None:
        """Mark a record as confirmed (True) or discarded (False)."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE gold SET confirmed = %s WHERE id = %s",
                (confirmed, record_id),
            )

    @staticmethod
    def _row_to_record(row: tuple) -> GoldRecord:
        # columns: id, doc_id, chunk_index, norm_frame, reasoning, signal_summary,
        #          signal_certainty, source_type, completeness_score, stream_tag,
        #          confirmed, timestamp
        return GoldRecord(
            id=row[0], doc_id=row[1], chunk_index=row[2],
            norm_frame=row[3], reasoning=row[4], signal_summary=row[5],
            signal_certainty=row[6], source_type=row[7],
            completeness_score=row[8], stream_tag=row[9],
            confirmed=row[10], timestamp=row[11],
        )

    @staticmethod
    def _row_to_signal(row: tuple) -> DocumentSignal:
        # columns: id, doc_id, chunk_index, norm_frame, reasoning, signal_summary,
        #          signal_certainty, source_type, completeness_score, stream_tag,
        #          confirmed, timestamp, onderwerp, soort, datum, vergaderjaar
        return DocumentSignal(
            gold_id=row[0], doc_id=row[1], chunk_index=row[2],
            norm_frame=row[3], reasoning=row[4], signal_summary=row[5],
            signal_certainty=row[6], source_type=row[7],
            completeness_score=row[8], stream_tag=row[9],
            confirmed=row[10], timestamp=row[11],
            onderwerp=row[12], soort=row[13], datum=row[14], vergaderjaar=row[15],
        )

    @staticmethod
    def _row_to_signal_with_chunk(row: tuple) -> DocumentSignal:
        # columns: same as _row_to_signal plus chunk_text at index 16
        signal = GoldRepository._row_to_signal(row)
        signal.chunk_text = row[16]
        return signal
