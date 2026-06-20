"""Repository for the synthesis store."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from pipeline.db.connection import transaction

REVIEW_STATUSES = ("strong", "weak", "unsure", "discarded")


@dataclass
class SynthesisRecord:
    doc_id: str
    norm_frame: dict
    expected_date: str
    affected_sectors: list[str]
    sector_reasons: dict
    client_action: str
    signal_summary: str
    signal_certainty: str
    source_type: str
    completeness_score: int
    stream_tag: str
    input_tokens: int = 0
    output_tokens: int = 0
    id: Optional[int] = None
    confirmed: Optional[bool] = None
    review_status: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None


@dataclass
class DocumentSynthesis:
    """A synthesis record enriched with bronze metadata for the review UI."""
    synthesis_id: int
    doc_id: str
    norm_frame: dict
    expected_date: str
    affected_sectors: list[str]
    sector_reasons: dict
    client_action: str
    signal_summary: str
    signal_certainty: str
    source_type: str
    completeness_score: int
    stream_tag: str
    confirmed: Optional[bool]
    review_status: Optional[str]
    timestamp: Optional[datetime]
    onderwerp: Optional[str]
    soort: str
    datum: Optional[date]
    vergaderjaar: Optional[str]


class SynthesisRepository:
    """All read/write access to the synthesis store."""

    def insert(self, record: SynthesisRecord) -> int:
        """Insert a synthesis record and return its id.

        Skips insertion if doc_id already exists (idempotency via UNIQUE constraint).
        Returns the existing id if skipped.
        """
        import json
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO synthesis (
                    doc_id, norm_frame, expected_date, affected_sectors,
                    sector_reasons, client_action, signal_summary, signal_certainty,
                    source_type, completeness_score, stream_tag, input_tokens, output_tokens,
                    duration_ms
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO NOTHING
                RETURNING id
                """,
                (
                    record.doc_id,
                    json.dumps(record.norm_frame),
                    record.expected_date,
                    record.affected_sectors,
                    json.dumps(record.sector_reasons),
                    record.client_action,
                    record.signal_summary,
                    record.signal_certainty,
                    record.source_type,
                    record.completeness_score,
                    record.stream_tag,
                    record.input_tokens,
                    record.output_tokens,
                    record.duration_ms,
                ),
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute("SELECT id FROM synthesis WHERE doc_id = %s", (record.doc_id,))
            return cur.fetchone()[0]

    def exists(self, doc_id: str) -> bool:
        """Return True if a synthesis record already exists for this document."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM synthesis WHERE doc_id = %s", (doc_id,))
            return cur.fetchone() is not None

    def get_unprocessed_doc_ids(self) -> list[str]:
        """Return doc_ids in gold that have no synthesis record yet."""
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT g.doc_id
                FROM gold g
                WHERE NOT EXISTS (
                    SELECT 1 FROM synthesis s WHERE s.doc_id = g.doc_id
                )
                ORDER BY g.doc_id
                """
            )
            return [row[0] for row in cur.fetchall()]

    def get_all_unreviewed(self, unreviewed_only: bool = False) -> list[DocumentSynthesis]:
        """Return synthesis records enriched with bronze metadata.

        Args:
            unreviewed_only: If True, only return records where review_status IS NULL.
        """
        conditions = [
            "(s.signal_certainty IS NULL OR s.signal_certainty != 'existing')",
            "(s.source_type IS NULL OR s.source_type != 'existing')",
        ]
        if unreviewed_only:
            conditions.append("s.review_status IS NULL")
        where = "WHERE " + " AND ".join(conditions)
        return self._query(where)

    def get_reviewed(self) -> list[DocumentSynthesis]:
        """Return all reviewed records (any review_status set), ordered by review_status then score."""
        where = "WHERE s.review_status IS NOT NULL"
        return self._query(where, order="s.review_status, s.completeness_score DESC")

    def set_review_status(self, record_id: int, status: str) -> None:
        """Set the review_status and derive the legacy confirmed boolean.

        status must be one of: strong, weak, unsure, discarded.
        """
        if status not in REVIEW_STATUSES:
            raise ValueError(f"Invalid review status {status!r}. Choose from {REVIEW_STATUSES}")
        confirmed = True if status in ("strong", "weak") else (False if status == "discarded" else None)
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE synthesis SET review_status = %s, confirmed = %s WHERE id = %s",
                (status, confirmed, record_id),
            )

    def set_confirmed(self, record_id: int, confirmed: bool) -> None:
        """Legacy binary confirm/discard. Kept for backwards compatibility."""
        status = "strong" if confirmed else "discarded"
        self.set_review_status(record_id, status)

    def _query(
        self,
        where: str,
        order: str = "s.completeness_score DESC, s.timestamp DESC",
    ) -> list[DocumentSynthesis]:
        with transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                SELECT
                    s.id, s.doc_id, s.norm_frame, s.expected_date, s.affected_sectors,
                    s.sector_reasons, s.client_action, s.signal_summary, s.signal_certainty,
                    s.source_type, s.completeness_score, s.stream_tag,
                    s.confirmed, s.review_status, s.timestamp,
                    b.onderwerp, b.soort, b.datum, b.vergaderjaar
                FROM synthesis s
                JOIN bronze b ON b.id = s.doc_id
                {where}
                ORDER BY {order}
                """
            )
            return [self._row_to_document_synthesis(row) for row in cur.fetchall()]

    @staticmethod
    def _row_to_document_synthesis(row: tuple) -> DocumentSynthesis:
        # columns: id, doc_id, norm_frame, expected_date, affected_sectors,
        #          sector_reasons, client_action, signal_summary, signal_certainty,
        #          source_type, completeness_score, stream_tag,
        #          confirmed, review_status, timestamp,
        #          onderwerp, soort, datum, vergaderjaar
        return DocumentSynthesis(
            synthesis_id=row[0],
            doc_id=row[1],
            norm_frame=row[2] or {},
            expected_date=row[3] or "",
            affected_sectors=list(row[4]) if row[4] else [],
            sector_reasons=dict(row[5]) if row[5] else {},
            client_action=row[6] or "",
            signal_summary=row[7] or "",
            signal_certainty=row[8] or "",
            source_type=row[9] or "",
            completeness_score=row[10],
            stream_tag=row[11],
            confirmed=row[12],
            review_status=row[13],
            timestamp=row[14],
            onderwerp=row[15],
            soort=row[16],
            datum=row[17],
            vergaderjaar=row[18],
        )
