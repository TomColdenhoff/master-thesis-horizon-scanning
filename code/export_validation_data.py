"""Export all validation data to JSON for use in thesis analysis.

Run after all 10 validation pipeline runs are complete (5 positive + 5 negative):
    python export_validation_data.py

Writes: validation_results.json
"""

import json
import logging
from pathlib import Path
from pipeline.db.connection import transaction

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

VALIDATION_DOCS = {
    # Positive cases — expected to be detected as signals
    "088132e5-f6bd-4124-a5ce-f1705be36e9a": {
        "case": 1,
        "label": "P1",
        "expected_signal": True,
        "law": "Wet goed verhuurderschap",
        "signal_date": "2021-02-22",
        "signal_title": "Uitkomst aanpak goed verhuurderschap",
        "mvt_date": "2022-06-07",
        "lead_months": 16,
    },
    "f072ca19-05b9-4af1-a895-d5020876fe78": {
        "case": 2,
        "label": "P2",
        "expected_signal": True,
        "law": "Wet toekomst pensioenen",
        "signal_date": "2019-06-05",
        "signal_title": "Principeakkoord vernieuwing pensioenstelsel",
        "mvt_date": "2022-03-29",
        "lead_months": 33,
    },
    "9dac5c86-862b-4e00-962a-4e5168218a3e": {
        "case": 3,
        "label": "P3",
        "expected_signal": True,
        "law": "Wet inburgering 2021",
        "signal_date": "2018-07-02",
        "signal_title": "Hoofdlijnen veranderopgave inburgering",
        "mvt_date": "2020-06-03",
        "lead_months": 23,
    },
    "3b7e0412-8e5a-4b81-902e-b17e01657627": {
        "case": 4,
        "label": "P4",
        "expected_signal": True,
        "law": "Wet toelating terbeschikkingstelling van arbeidskrachten (Wtta)",
        "signal_date": "2020-07-15",
        "signal_title": "Technische uitwerking van het advies van de Commissie Regulering van werk",
        "mvt_date": "2023-10-06",
        "lead_months": 39,
    },
    "911c7082-b68b-4d73-9c80-16c2419a3259": {
        "case": 5,
        "label": "P5",
        "expected_signal": True,
        "law": "Wet franchise",
        "signal_date": "2018-05-23",
        "signal_title": "Stand van zaken regelgeving Franchise",
        "mvt_date": "2020-02-10",
        "lead_months": 21,
    },
    # Negative cases — same dossiers, no legislative commitment; expected to be discarded
    "552b83c2-67ac-4f4c-8ae5-96abb482cbdf": {
        "case": "N1",
        "label": "N1",
        "expected_signal": False,
        "law": "Wet goed verhuurderschap (dossier 27 926)",
        "signal_date": None,
        "signal_title": "Stand van zaken bij de Huurcommissie",
        "letter_date": "2020-07-02",
        "mvt_date": None,
        "lead_months": None,
    },
    "349df7ce-d2a8-405d-a099-5ed5c6c5cdf3": {
        "case": "N2",
        "label": "N2",
        "expected_signal": False,
        "law": "Wet Wtta (dossier 29 544)",
        "signal_date": None,
        "signal_title": "Rapport Commissie Borstlap",
        "letter_date": "2020-01-23",
        "mvt_date": None,
        "lead_months": None,
    },
    "6b96d047-d7f5-4909-9597-360f6a527a95": {
        "case": "N3",
        "label": "N3",
        "expected_signal": False,
        "law": "Wet Wtta (dossier 29 544)",
        "signal_date": None,
        "signal_title": "Uitkomsten uitzendonderzoeken",
        "letter_date": "2020-04-06",
        "mvt_date": None,
        "lead_months": None,
    },
    "bf392419-e4be-4725-8580-b83d775a787b": {
        "case": "N4",
        "label": "N4",
        "expected_signal": False,
        "law": "Zelfstandig ondernemerschap (dossier 31 311)",
        "signal_date": None,
        "signal_title": "Evaluatie fiscale ondernemerschapsregelingen",
        "letter_date": "2017-05-18",
        "mvt_date": None,
        "lead_months": None,
    },
    "9858d519-158f-4497-8652-c3a9c24d4d70": {
        "case": "N5",
        "label": "N5",
        "expected_signal": False,
        "law": "Wet inburgering (dossier 32 824)",
        "signal_date": None,
        "signal_title": "Ontwikkelingen op het gebied van de inburgeringsexamens",
        "letter_date": "2014-03-11",
        "mvt_date": None,
        "lead_months": None,
    },
}


def export() -> None:
    results = []

    with transaction() as conn:
        cur = conn.cursor()

        for doc_id, meta in VALIDATION_DOCS.items():
            log.info("Collecting case %s: %s", meta["case"], meta["law"])
            entry = {**meta, "doc_id": doc_id}

            # --- Bronze ---
            cur.execute(
                "SELECT soort, datum, onderwerp, vergaderjaar, stream_tag FROM bronze WHERE id = %s",
                (doc_id,),
            )
            row = cur.fetchone()
            if row:
                entry["bronze"] = {
                    "soort": row[0],
                    "datum": str(row[1]) if row[1] else None,
                    "onderwerp": row[2],
                    "vergaderjaar": row[3],
                    "stream_tag": row[4],
                }
            else:
                log.warning("No bronze record for doc_id=%s", doc_id)
                entry["bronze"] = None

            # --- Classifier decision ---
            cur.execute(
                """
                SELECT relevant, reason, input_tokens, output_tokens
                FROM classifier_log WHERE doc_id = %s
                ORDER BY id DESC LIMIT 1
                """,
                (doc_id,),
            )
            row = cur.fetchone()
            entry["classifier"] = {
                "relevant": row[0],
                "reason": row[1],
                "input_tokens": row[2],
                "output_tokens": row[3],
            } if row else None

            # --- Silver stats ---
            cur.execute(
                "SELECT COUNT(*) FROM silver WHERE doc_id = %s",
                (doc_id,),
            )
            entry["silver_chunk_count"] = cur.fetchone()[0]

            # --- Gold stats ---
            cur.execute(
                """
                SELECT COUNT(*),
                       AVG(completeness_score)::numeric(4,2),
                       MAX(completeness_score),
                       MIN(completeness_score)
                FROM gold WHERE doc_id = %s
                """,
                (doc_id,),
            )
            row = cur.fetchone()
            entry["gold_stats"] = {
                "chunks_written": row[0],
                "avg_completeness": float(row[1]) if row[1] else None,
                "max_completeness": row[2],
                "min_completeness": row[3],
            }

            cur.execute(
                "SELECT COUNT(*) FROM gold_discarded WHERE doc_id = %s",
                (doc_id,),
            )
            entry["gold_stats"]["chunks_discarded"] = cur.fetchone()[0]

            # All gold chunks (for element-level analysis)
            cur.execute(
                """
                SELECT g.chunk_index, g.completeness_score, g.norm_frame,
                       g.signal_summary, g.signal_certainty, g.source_type,
                       s.chunk_text
                FROM gold g
                LEFT JOIN silver s
                  ON s.doc_id = g.doc_id AND s.chunk_index = g.chunk_index
                WHERE g.doc_id = %s
                ORDER BY g.completeness_score DESC
                """,
                (doc_id,),
            )
            entry["gold_chunks"] = [
                {
                    "chunk_index": r[0],
                    "completeness_score": r[1],
                    "norm_frame": r[2],
                    "signal_summary": r[3],
                    "signal_certainty": r[4],
                    "source_type": r[5],
                    "chunk_text": r[6],
                }
                for r in cur.fetchall()
            ]

            # --- Synthesis record ---
            cur.execute(
                """
                SELECT norm_frame, completeness_score, signal_summary,
                       signal_certainty, source_type, expected_date,
                       affected_sectors, sector_reasons, client_action,
                       stream_tag, input_tokens, output_tokens
                FROM synthesis WHERE doc_id = %s
                """,
                (doc_id,),
            )
            row = cur.fetchone()
            if row:
                entry["synthesis"] = {
                    "norm_frame": row[0],
                    "completeness_score": row[1],
                    "signal_summary": row[2],
                    "signal_certainty": row[3],
                    "source_type": row[4],
                    "expected_date": row[5],
                    "affected_sectors": row[6],
                    "sector_reasons": row[7],
                    "client_action": row[8],
                    "stream_tag": row[9],
                    "input_tokens": row[10],
                    "output_tokens": row[11],
                }

                # Element population summary (which of the 8 are filled)
                nf = row[0] or {}
                fields = [
                    "norm_identifier", "norm_type", "promulgation", "scope",
                    "conditions", "subject", "legal_modality", "act_identifier",
                ]
                entry["synthesis"]["elements_populated"] = {
                    f: bool(nf.get(f) and str(nf[f]).strip()) for f in fields
                }
                entry["synthesis"]["elements_populated_count"] = sum(
                    entry["synthesis"]["elements_populated"].values()
                )
            else:
                log.warning("No synthesis record for doc_id=%s", doc_id)
                entry["synthesis"] = None

            results.append(entry)

    out_path = Path(__file__).parent / "data" / "validation_results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str))
    log.info("Written to %s", out_path)

    # Print summary table
    print("\n── Validation summary ──────────────────────────────────────────────────────────")
    print(f"{'#':<4} {'Expected':<9} {'Classifier':<11} {'Law':<40} {'Silver':>7} {'Gold':>5} {'Disc':>5} {'Elements':>9}")
    print("-" * 90)
    for e in results:
        s = e.get("synthesis") or {}
        clf = e.get("classifier") or {}
        expected = "signal" if e["expected_signal"] else "discard"
        actual = "signal" if clf.get("relevant") else ("discard" if clf.get("relevant") is False else "n/a")
        match = "✓" if (clf.get("relevant") is not None and clf.get("relevant") == e["expected_signal"]) else "✗"
        print(
            f"{str(e['case']):<4} {expected:<9} {actual + ' ' + match:<11} {e['law'][:39]:<40} "
            f"{e['silver_chunk_count']:>7} "
            f"{e['gold_stats']['chunks_written']:>5} "
            f"{e['gold_stats']['chunks_discarded']:>5} "
            f"{s.get('elements_populated_count', '-'):>7}/8"
        )

    # Precision / recall summary
    positives = [e for e in results if e["expected_signal"]]
    negatives = [e for e in results if not e["expected_signal"]]
    tp = sum(1 for e in positives if (e.get("classifier") or {}).get("relevant") is True)
    fp = sum(1 for e in negatives if (e.get("classifier") or {}).get("relevant") is True)
    tn = sum(1 for e in negatives if (e.get("classifier") or {}).get("relevant") is False)
    fn = sum(1 for e in positives if (e.get("classifier") or {}).get("relevant") is False)
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    print(f"\nTP={tp}  FP={fp}  TN={tn}  FN={fn}")
    print(f"Precision: {precision:.2f}" if precision is not None else "Precision: n/a")
    print(f"Recall:    {recall:.2f}" if recall is not None else "Recall: n/a")
    print()


if __name__ == "__main__":
    export()
