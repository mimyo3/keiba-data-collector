"""Repair stored Netkeiba race dates from matching cached newspaper pages."""

from __future__ import annotations

from typing import Any

from src.helpers.db_helper import get_connection
from src.netkeiba_fetcher.netkeiba_prevrun_fetch import NEWSPAPER_DIR
from src.netkeiba_fetcher.race_card import extract_race_date


def repair_race_dates_from_cached_newspapers() -> dict[str, Any]:
    """Correct race dates in status and race-card tables using verified pages."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    corrected_dates: dict[str, str] = {}
    skipped: dict[str, str] = {}

    try:
        cur.execute("SELECT race_id FROM race_fetch_status")
        race_ids = {row["race_id"] for row in cur.fetchall()}
        cur.execute("SELECT DISTINCT race_id FROM race_card_entries")
        race_ids.update(row["race_id"] for row in cur.fetchall())

        for race_id in sorted(race_ids):
            html_path = NEWSPAPER_DIR / f"race_sp_newspaper_{race_id}.html"
            if not html_path.is_file():
                skipped[race_id] = f"新聞HTMLがありません: {html_path}"
                continue

            try:
                html = html_path.read_text(encoding="utf-8")
                corrected_dates[race_id] = extract_race_date(html, race_id)
            except (OSError, UnicodeError, ValueError) as exc:
                skipped[race_id] = str(exc)

        status_updates = [
            (race_date, race_id, race_date)
            for race_id, race_date in corrected_dates.items()
        ]
        card_updates = list(status_updates)
        if status_updates:
            cur.executemany(
                """
                UPDATE race_fetch_status
                SET race_date = %s
                WHERE race_id = %s AND race_date <> %s
                """,
                status_updates,
            )
            status_rows_updated = cur.rowcount
            cur.executemany(
                """
                UPDATE race_card_entries
                SET race_date = %s
                WHERE race_id = %s AND race_date <> %s
                """,
                card_updates,
            )
            card_rows_updated = cur.rowcount
        else:
            status_rows_updated = 0
            card_rows_updated = 0

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    result = {
        "status_rows_updated": status_rows_updated,
        "race_card_rows_updated": card_rows_updated,
        "races_verified": len(corrected_dates),
        "skipped": skipped,
    }
    print(
        "Race-date repair complete: "
        f"{status_rows_updated} status rows, "
        f"{card_rows_updated} race-card rows; "
        f"{len(skipped)} races skipped."
    )
    for race_id, reason in skipped.items():
        print(f"Skipped {race_id}: {reason}")
    return result


if __name__ == "__main__":
    repair_race_dates_from_cached_newspapers()
