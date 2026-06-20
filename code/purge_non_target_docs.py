"""Remove all pipeline data except the 5 target documents for the expert validation session.

Deletes from synthesis -> gold -> silver -> bronze in reverse FK order,
keeping only the doc_ids seeded for the semiconductor industry expert session.

Usage:
    docker-compose run --rm api python purge_non_target_docs.py
"""

from pipeline.db.connection import transaction

KEEP_DOC_IDS = [
    "aa4fa1b8-bc64-40a9-922b-554668007704",  # CSDDD Omnibus I trilogue (dec 2025)
    "970285fe-95ba-4b5a-bbde-8158e5b9c55a",  # Voortgang halfgeleiderindustrie (may 2025)
    "73ab4bb0-8e79-43fb-8405-52eff5047b34",  # Nederlandse inzet CRP Omnibus-CSDDD (jun 2025)
    "562d622e-61fe-43bf-8427-607db13708c6",  # FDI screening BDI (jan 2025)
    "19599fde-cd5d-4a1b-a4c7-3e169515e9de",  # Nationale exportcontrolemaatregelen (oct 2024)
]

TABLES = ["synthesis", "gold", "silver"]  # deletion order; bronze last

with transaction() as conn:
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(KEEP_DOC_IDS))

    for table in TABLES:
        col = "doc_id"
        cur.execute(
            f"DELETE FROM {table} WHERE {col} NOT IN ({placeholders})",
            KEEP_DOC_IDS,
        )
        print(f"  {table}: deleted {cur.rowcount} rows")

    cur.execute(
        f"DELETE FROM bronze WHERE id NOT IN ({placeholders})",
        KEEP_DOC_IDS,
    )
    print(f"  bronze: deleted {cur.rowcount} rows")

print("Done — only target session documents remain.")
