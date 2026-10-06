
"""Database registration helpers for race and previous-run data."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Iterable, List

import mysql.connector


from src.netkeiba_fetcher.db_schema import (
    RACES_TABLE_SQL,
    HORSE_RACE_RESULTS_TABLE_SQL,
    RACE_FETCH_STATUS_TABLE_SQL,
    RACE_CARD_ENTRIES_TABLE_SQL,
)

from src.helpers.db_helper import get_connection


__all__ = [
    "init_db",
    "register_prev_run",
    "register_races",
    "register_html_saves",
    "register_race_fetch_status",
    "register_race_card_entries",
    "update_race_fetch_status",
]


def init_db(conn: Any = None) -> None:
    """Create the normalised MySQL tables when they do not exist."""

    if conn is None:
        conn = get_connection()
        close_after = True
    else:
        close_after = False

    cur = conn.cursor()

    cur.execute(RACES_TABLE_SQL)
    cur.execute(HORSE_RACE_RESULTS_TABLE_SQL)
    cur.execute(RACE_FETCH_STATUS_TABLE_SQL)
    cur.execute(RACE_CARD_ENTRIES_TABLE_SQL)

    conn.commit()
    cur.close()

    if close_after:
        conn.close()


def register_race_card_entries(entries: List[Dict[str, Any]]) -> int:
    """Insert or update the declared horses for one race."""
    if not entries:
        raise ValueError("出馬表から登録対象の馬が見つかりません")

    race_ids = {entry["race_id"] for entry in entries}
    if len(race_ids) != 1:
        raise ValueError("一度に登録できる出馬表は1レース分です")
    race_id = race_ids.pop()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM race_card_entries WHERE race_id = %s",
            (race_id,),
        )
        cur.executemany(
            """
            INSERT INTO race_card_entries (
                race_id,
                race_date,
                frame_number,
                horse_number,
                horse_id,
                horse_name,
                sex_age,
                carried_weight,
                jockey,
                trainer_area,
                trainer,
                horse_weight,
                weight_change,
                win_odds,
                popularity
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """,
            [
                (
                    entry["race_id"],
                    entry["race_date"],
                    entry["frame_number"],
                    entry["horse_number"],
                    entry["horse_id"],
                    entry["horse_name"],
                    entry["sex_age"],
                    entry["carried_weight"],
                    entry["jockey"],
                    entry["trainer_area"],
                    entry["trainer"],
                    entry["horse_weight"],
                    entry["weight_change"],
                    entry["win_odds"],
                    entry["popularity"],
                )
                for entry in entries
            ],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    print(f"Registered {len(entries)} race-card entries.")
    return len(entries)


def register_kaishi_dates(dates: Iterable[str]) -> None:
    """Register start dates."""

    dates = list(dates)

    conn = get_connection()
    cur = conn.cursor()



    conn.commit()
    cur.close()
    conn.close()

    print(f"Registered {len(dates)} kaishi dates.")


def register_race_fetch_status(
    race_id: str,
    race_date: str,
) -> None:
    """Register or update race fetch status."""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO race_fetch_status
            (race_id, race_date)
        VALUES
            (%s, %s)
        ON DUPLICATE KEY UPDATE
            race_date = VALUES(race_date),
            html_fetched = FALSE,
            parsed = FALSE,
            registered = FALSE,
            error_message = NULL
        """,
        (race_id, race_date),
    )

    conn.commit()
    cur.close()
    conn.close()

    print(f"Registered race fetch status for {race_id}.")


def update_race_fetch_status(
    race_id: str,
    **kwargs: Any,
) -> None:
    """Update race fetch status fields."""

    if not kwargs:
        return

    allowed = {
        "html_fetched",
        "parsed",
        "registered",
        "error_message",
    }

    invalid = set(kwargs) - allowed

    if invalid:
        raise ValueError(
            f"Invalid race_fetch_status fields: {sorted(invalid)}"
        )

    conn = get_connection()
    cur = conn.cursor()

    set_clause = ", ".join(
        f"{key} = %s"
        for key in kwargs
    )

    values = list(kwargs.values())
    values.append(race_id)

    cur.execute(
        f"""
        UPDATE race_fetch_status
        SET {set_clause}
        WHERE race_id = %s
        """,
        values,
    )

    conn.commit()
    cur.close()
    conn.close()

    print(f"Updated race fetch status for {race_id}.")


def _is_sqlite_like(conn: Any) -> bool:
    """Return True when conn looks like a sqlite connection."""

    return (
        "sqlite" in str(type(conn)).lower()
        or "sqlite" in str(conn).lower()
    )


def register_html_saves(
    html_contents: List[tuple],
) -> None:
    """Register HTML save metadata."""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS html_saves (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            save_date DATETIME NOT NULL,
            source_url VARCHAR(500) NOT NULL,
            save_path VARCHAR(500) NOT NULL,
            html_content MEDIUMTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        )
        """
    )

    for row in html_contents:
        cur.execute(
            """
            INSERT INTO html_saves
                (save_date, source_url, save_path, html_content)
            VALUES
                (%s, %s, %s, %s)
            """,
            row,
        )

    conn.commit()
    cur.close()

    if not _is_sqlite_like(conn):
        conn.close()

    print(f"Registered {len(html_contents)} html saves.")


def _race_date_from_id(race_id: str) -> str:
    """Convert YYYYMMDDxxxx race id to YYYY-MM-DD."""

    if (
        not isinstance(race_id, str)
        or len(race_id) != 12
        or not race_id[:8].isdigit()
    ):
        raise ValueError(
            f"Invalid historical race_id: {race_id!r}"
        )

    date_text = race_id[:8]

    datetime.strptime(date_text, "%Y%m%d")

    return (
        f"{date_text[:4]}-"
        f"{date_text[4:6]}-"
        f"{date_text[6:8]}"
    )


def _none_if_empty(value: Any) -> Any:
    """Convert empty strings to None."""

    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value or None

    return value


def _register_previous_race(
    cur: Any,
    meta: Dict[str, Any],
) -> None:
    """Insert/update one historical race in races."""

    race_id = _none_if_empty(meta.get("race_id"))

    if not race_id:
        return

    cur.execute(
        """
        INSERT INTO races (
            race_id,
            place_num,
            race_name,
            race_condition,
            grade,
            tousu,
            track,
            distance,
            `condition`,
            bias,
            ichinuke,
            jitenn,
            staus,
            pace
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            place_num = VALUES(place_num),
            race_name = VALUES(race_name),
            race_condition = VALUES(race_condition),
            grade = VALUES(grade),
            tousu = VALUES(tousu),
            track = VALUES(track),
            distance = VALUES(distance),
            `condition` = VALUES(`condition`),
            bias = VALUES(bias),
            ichinuke = VALUES(ichinuke),
            jitenn = VALUES(jitenn),
            staus = VALUES(staus),
            pace = VALUES(pace)
        """,
        (
            race_id,
            _none_if_empty(meta.get("place_num")),
            _none_if_empty(meta.get("race_name")),
            _none_if_empty(meta.get("race_condition")),
            meta.get("grade"),
            meta.get("tousu"),
            _none_if_empty(meta.get("track")),
            meta.get("distance"),
            _none_if_empty(meta.get("condition")),
            _none_if_empty(meta.get("bias")),
            _none_if_empty(meta.get("ichinuke")),
            _none_if_empty(meta.get("jitenn")),
            _none_if_empty(meta.get("staus")),
            _none_if_empty(meta.get("pace")),
        ),
    )


def _register_horse_result(
    cur: Any,
    race_id: str,
    horse: Dict[str, Any],
    meta: Dict[str, Any],
) -> None:
    r"""Insert or update one horse's result for one historical race."""

    horse_name = _none_if_empty(horse.get("horse_name"))

    if not horse_name:
        return

    values = (
        race_id,
        _none_if_empty(horse.get("horse_id")),
        horse_name,
        _none_if_empty(meta.get("jockey")),
        meta.get("post"),
        meta.get("popularity"),
        meta.get("tyakujun"),
        _none_if_empty(meta.get("time")),
        _none_if_empty(meta.get("margin")),
        meta.get("weight"),
        meta.get("horse_weight"),
        meta.get("weight_change"),
        meta.get("first_half"),
        meta.get("second_half"),
        _none_if_empty(meta.get("corners")),
        _none_if_empty(meta.get("huri1")),
        _none_if_empty(meta.get("corner1")),
        _none_if_empty(meta.get("corner2")),
        _none_if_empty(meta.get("corner3")),
        _none_if_empty(meta.get("corner4")),
        _none_if_empty(meta.get("corner_position")),
        meta.get("time_index_total"),
        meta.get("time_index_start"),
        meta.get("time_index_run"),
        meta.get("time_index_finish"),
        _none_if_empty(meta.get("ana04")),
        _none_if_empty(meta.get("running_type")),
    )

    # 同じ race_id + horse_name が既にあれば更新する。
    cur.execute(
        """
        SELECT id
        FROM horse_race_results
        WHERE race_id = %s
          AND horse_name = %s
        ORDER BY id
        LIMIT 1
        """,
        (race_id, horse_name),
    )

    row = cur.fetchone()

    if row:
        cur.execute(
            """
            UPDATE horse_race_results
            SET
                horse_id = %s,
                jockey = %s,
                post = %s,
                popularity = %s,
                tyakujun = %s,
                time = %s,
                margin = %s,
                weight = %s,
                horse_weight = %s,
                weight_change = %s,
                first_half = %s,
                second_half = %s,
                corners = %s,
                huri1 = %s,
                corner1 = %s,
                corner2 = %s,
                corner3 = %s,
                corner4 = %s,
                corner_position = %s,
                time_index_total = %s,
                time_index_start = %s,
                time_index_run = %s,
                time_index_finish = %s,
                ana04 = %s,
                running_type = %s
            WHERE id = %s
            """,
            values[1:2] + values[3:] + (row[0],),
        )
    else:
        cur.execute(
            """
            INSERT INTO horse_race_results (
                race_id,
                horse_id,
                horse_name,
                jockey,
                post,
                popularity,
                tyakujun,
                time,
                margin,
                weight,
                horse_weight,
                weight_change,
                first_half,
                second_half,
                corners,
                huri1,
                corner1,
                corner2,
                corner3,
                corner4,
                corner_position,
                time_index_total,
                time_index_start,
                time_index_run,
                time_index_finish,
                ana04,
                running_type
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            """,
            values,
        )

def register_prev_run(
    json_obj: Dict[str, Any],
) -> None:
    """
    Register PastBox historical data.

    One PastBox record produces:
      1. one historical race in `races`
      2. one horse result in `horse_race_results`

    The historical race_id comes directly from the PastBox record.
    Registration uses the normalized ``races`` and
    ``horse_race_results`` tables.
    """

    conn = get_connection()
    cur = conn.cursor()

    registered_horses = 0
    registered_races = set()

    try:
        for horse in json_obj.get("horses", []):
            meta = horse.get("meta")

            if not isinstance(meta, dict):
                continue

            race_id = _none_if_empty(
                meta.get("race_id")
                or horse.get("previous_race_id")
            )

            if not race_id:
                # No PastBox / no historical race.
                continue

            # Extract race data for races table
            race_data = {
                "race_id": race_id,
                "place_num": meta.get("place_num"),
                "race_name": meta.get("race_name"),
                "race_condition": meta.get("race_condition"),
                "grade": meta.get("grade"),
                "tousu": meta.get("tousu"),
                "track": meta.get("track"),
                "distance": meta.get("distance"),
                "condition": meta.get("condition"),
                "bias": meta.get("bias"),
                "ichinuke": meta.get("ichinuke"),
                "jitenn": meta.get("jitenn"),
                "staus": meta.get("staus"),
                "pace": meta.get("pace"),
            }

            # Register race data
            _register_previous_race(cur, race_data)

            registered_races.add(race_id)

            # Remove race-specific data from meta for horse result
            horse_meta = meta.copy()
            race_specific_keys = [
                "place_num", "race_name","race_condition","grade", "tousu", "track", "distance",
                "condition", "bias", "ichinuke", "jitenn", "staus", "pace"
            ]
            for key in race_specific_keys:
                horse_meta.pop(key, None)

            _register_horse_result(
                cur,
                race_id,
                horse,
                horse_meta,
            )

            registered_horses += 1


        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()

        if not _is_sqlite_like(conn):
            conn.close()

    print(
        "Registered previous-run data: "
        f"{len(registered_races)} races, "
        f"{registered_horses} horse results."
    )


def register_races(
    races: List[Dict[str, Any]],
) -> None:
    

    print(f"Registered {len(races)} races.")
