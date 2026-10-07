"""FastAPI server implementation for the keiba data API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.helpers.db_helper import get_connection
from src.jra_fetcher.html_workflow import fetch_jra_html_workflow
from src.jra_fetcher.race_day_workflow import update_race_days_table
from src.jra_fetcher.workflow import _iter_months, _validate_month
from src.netkeiba_fetcher.api_entry import (
    fetch_netkeiba_data_by_date_range,
    fetch_and_register_race_card,
    fetch_netkeiba_previous_runs,
)
from src.netkeiba_fetcher.netkeiba_prevrun_fetch import (
    NEWSPAPER_DIR,
    get_race_ids_by_date,
)
from src.netkeiba_fetcher.race_card import extract_newspaper_race_card_entries


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_BUILD = PROJECT_ROOT / "frontend" / "build"

app = FastAPI(title="Keiba API")

TABLES = {
    "horse_race_results",
    "html_saves",
    "jra_html_metadata",
    "race_days",
    "race_fetch_status",
    "race_card_entries",
    "races",
}


class JraFetchRequest(BaseModel):
    start_month: str
    end_month: str


class NetkeibaFetchRequest(BaseModel):
    start_date: str
    end_date: str


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _race_date_from_id(race_id: str | None) -> str | None:
    if not race_id or len(race_id) != 12 or not race_id[:8].isdigit():
        return None
    try:
        return datetime.strptime(race_id[:8], "%Y%m%d").date().isoformat()
    except ValueError:
        return None


@app.get("/api/db/{table_name}")
def get_table_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(1000000, ge=1),
    search: str = "",
    sort_by: str | None = None,
    sort_order: str = "asc",
) -> Response:
    """Return rows for one of the tables used by the existing UI."""
    if table_name not in TABLES:
        raise HTTPException(status_code=404, detail="Unknown table")

    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        table_columns = cursor.fetchall()
        column_names = [column["Field"] for column in table_columns]

        if sort_by is not None and sort_by not in column_names:
            raise HTTPException(status_code=400, detail="Unknown sort column")
        if sort_order.lower() not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")

        where_clause = ""
        search_params: tuple[str, ...] = ()
        search_term = search.strip()
        if search_term and column_names:
            search_conditions = [
                f"LOCATE(%s, CAST(`{column_name.replace('`', '``')}` AS CHAR)) > 0"
                for column_name in column_names
            ]
            where_clause = f" WHERE ({' OR '.join(search_conditions)})"
            search_params = tuple(search_term for _ in search_conditions)

        # Pagination totals must reflect the search results, not the full table.
        cursor.execute(
            f"SELECT COUNT(*) as total FROM `{table_name}`{where_clause}",
            search_params,
        )
        total_count = cursor.fetchone()['total']

        offset = (page - 1) * limit
        order_clause = ""
        if sort_by is not None:
            quoted_sort_column = sort_by.replace("`", "``")
            order_columns = [f"`{quoted_sort_column}` {sort_order.upper()}"]
            primary_keys = [
                column["Field"] for column in table_columns
                if column.get("Key") == "PRI" and column["Field"] != sort_by
            ]
            order_columns.extend(f"`{key.replace('`', '``')}` ASC" for key in primary_keys)
            order_clause = f" ORDER BY {', '.join(order_columns)}"

        cursor.execute(
            f"SELECT * FROM `{table_name}`{where_clause}{order_clause} LIMIT %s OFFSET %s",
            (*search_params, limit, offset),
        )
        result = [
            {key: _json_value(value) for key, value in row.items()}
            for row in cursor.fetchall()
        ]

        # Create a JSON string response
        import json
        json_content = json.dumps(result)

        # Create a custom response to include the total count in headers
        response = Response(content=json_content)
        response.headers["X-Total-Rows"] = str(total_count)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        connection.close()


@app.post("/api/jra/fetch-race-days")
def fetch_jra_race_days(request: JraFetchRequest) -> dict[str, Any]:
    """Run the existing JRA HTML and race-day registration steps."""
    try:
        _validate_month(request.start_month)
        _validate_month(request.end_month)
        if request.start_month < request.end_month:
            raise ValueError("start_month must not be older than end_month")

        fetch_jra_html_workflow(request.start_month, request.end_month)
        for target_month in _iter_months(request.start_month, request.end_month):
            update_race_days_table(target_month)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": (
            f"JRA開催日を {request.start_month} から "
            f"{request.end_month} まで取得・登録しました。"
        )
    }


@app.post("/api/netkeiba/fetch-data-by-date-range")
def fetch_netkeiba_data(request: NetkeibaFetchRequest) -> dict[str, Any]:
    """Run the existing Netkeiba date-range workflow."""
    try:
        race_ids = fetch_netkeiba_data_by_date_range(
            request.start_date,
            request.end_date,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": f"netkeiba情報を取得・登録しました。処理件数: {len(race_ids)}",
        "race_ids": race_ids,
    }


@app.get("/api/netkeiba/race-card/{race_id}")
def get_registered_race_card(race_id: str) -> dict[str, Any]:
    """Return the registered race-card entries for exactly one race."""
    if len(race_id) != 12 or not race_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="race_id は12桁の数字である必要があります",
        )

    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
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
            FROM race_card_entries
            WHERE race_id = %s
            ORDER BY horse_number
            """,
            (race_id,),
        )
        entries = [
            {key: _json_value(value) for key, value in row.items()}
            for row in cursor.fetchall()
        ]
        if not entries:
            newspaper_path = NEWSPAPER_DIR / f"race_sp_newspaper_{race_id}.html"
            if newspaper_path.is_file():
                newspaper_html = newspaper_path.read_text(encoding="utf-8")
                entries = extract_newspaper_race_card_entries(
                    newspaper_html,
                    race_id,
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        race_id,
                        (
                            SELECT race_date
                            FROM race_fetch_status
                            WHERE race_id = %s
                            LIMIT 1
                        ) AS race_date,
                        NULL AS frame_number,
                        post AS horse_number,
                        horse_id,
                        horse_name,
                        NULL AS sex_age,
                        weight AS carried_weight,
                        jockey,
                        NULL AS trainer_area,
                        NULL AS trainer,
                        horse_weight,
                        weight_change,
                        NULL AS win_odds,
                        popularity
                    FROM horse_race_results
                    WHERE race_id = %s
                    ORDER BY post
                    """,
                    (race_id, race_id),
                )
                entries = [
                    {
                        **{
                            key: _json_value(value)
                            for key, value in row.items()
                        },
                        "race_date": (
                            _json_value(row.get("race_date"))
                            or _race_date_from_id(race_id)
                        ),
                    }
                    for row in cursor.fetchall()
                ]

        horse_ids = sorted({
            entry["horse_id"]
            for entry in entries
            if entry.get("horse_id")
        })
        histories_by_horse: dict[str, list[dict[str, Any]]] = {
            horse_id: [] for horse_id in horse_ids
        }
        race_details: dict[str, dict[str, Any]] = {}
        if horse_ids:
            placeholders = ", ".join(["%s"] * len(horse_ids))
            cursor.execute(
                f"""
                SELECT
                    horse_id,
                    race_id,
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
                    running_type,
                    ana04
                FROM horse_race_results
                WHERE horse_id IN ({placeholders})
                """,
                tuple(horse_ids),
            )
            history_rows = cursor.fetchall()
            history_race_ids = sorted({
                row["race_id"]
                for row in history_rows
                if row.get("race_id")
            } | {race_id})

            race_dates: dict[str, str] = {}
            if history_race_ids:
                race_placeholders = ", ".join(
                    ["%s"] * len(history_race_ids)
                )
                cursor.execute(
                    f"""
                    SELECT race_id, race_date
                    FROM race_fetch_status
                    WHERE race_id IN ({race_placeholders})
                    """,
                    tuple(history_race_ids),
                )
                race_dates = {
                    row["race_id"]: _json_value(row["race_date"])
                    for row in cursor.fetchall()
                }

                cursor.execute(
                    f"""
                    SELECT race_id, place_num, race_name, race_condition, grade,
                           tousu, track, distance, `condition`, bias, ichinuke,
                           jitenn, staus, pace
                    FROM races
                    WHERE race_id IN ({race_placeholders})
                    """,
                    tuple(history_race_ids),
                )
                race_details = {
                    row["race_id"]: {
                        key: _json_value(value)
                        for key, value in row.items()
                    }
                    for row in cursor.fetchall()
                }

            for row in history_rows:
                horse_id = row.get("horse_id")
                history_race_id = row.get("race_id")
                if horse_id not in histories_by_horse:
                    continue
                history = {
                    key: _json_value(value)
                    for key, value in row.items()
                }
                history["race_date"] = race_dates.get(history_race_id)
                history.update(race_details.get(history_race_id, {}))
                histories_by_horse[horse_id].append(history)

            for horse_histories in histories_by_horse.values():
                horse_histories.sort(
                    key=lambda history: (
                        history["race_date"] is not None,
                        history["race_date"] or "",
                        history["race_id"] or "",
                    ),
                    reverse=True,
                )

        for entry in entries:
            horse_histories = histories_by_horse.get(entry.get("horse_id"), [])
            target_race_date = entry.get("race_date")
            previous_runs = []
            subsequent_runs = []
            race_day_result = None

            for history in horse_histories:
                if history.get("race_id") == race_id:
                    race_day_result = history
                    continue
                history_date = history.get("race_date")
                if not history_date or not target_race_date:
                    continue
                if history_date < target_race_date:
                    previous_runs.append(history)
                elif history_date > target_race_date:
                    subsequent_runs.append(history)

            previous_runs.sort(
                key=lambda history: (history["race_date"], history["race_id"]),
                reverse=True,
            )
            subsequent_runs.sort(
                key=lambda history: (history["race_date"], history["race_id"]),
            )
            race_day_result = {
                **(race_details.get(race_id, {})),
                **(race_day_result or {}),
                "race_id": race_id,
                "race_date": target_race_date,
                "post": (
                    (race_day_result or {}).get("post")
                    or entry.get("horse_number")
                ),
                "jockey": (
                    (race_day_result or {}).get("jockey")
                    or entry.get("jockey")
                ),
                "weight": (
                    (race_day_result or {}).get("weight")
                    or entry.get("carried_weight")
                ),
                "horse_weight": (
                    (race_day_result or {}).get("horse_weight")
                    or entry.get("horse_weight")
                ),
                "weight_change": (
                    (race_day_result or {}).get("weight_change")
                    if (race_day_result or {}).get("weight_change") is not None
                    else entry.get("weight_change")
                ),
            }
            entry["previous_runs"] = previous_runs
            entry["race_day_result"] = race_day_result
            entry["subsequent_runs"] = subsequent_runs[:2]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        connection.close()

    return {"race_id": race_id, "entries": entries}


@app.post("/api/netkeiba/fetch-race-data/{race_id}")
def fetch_netkeiba_race_data(race_id: str) -> dict[str, Any]:
    """Fetch and register previous-run data for one race-card link."""
    if len(race_id) != 12 or not race_id.isdigit():
        raise HTTPException(
            status_code=400,
            detail="race_id は12桁の数字である必要があります",
        )
    try:
        entry_count = fetch_and_register_race_card(race_id)
        fetch_netkeiba_previous_runs(race_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": (
            f"当日出馬表 {entry_count} 頭と前走記録を"
            "データベースに登録しました。"
        ),
        "race_id": race_id,
        "entry_count": entry_count,
    }


@app.get("/api/netkeiba/race-card-urls")
def get_netkeiba_race_card_urls(race_date: date | None = None) -> dict[str, Any]:
    """Return race-card URLs for the requested date, defaulting to today in Japan."""
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    target_date = race_date or today
    try:
        if target_date < today:
            connection = get_connection()
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT DISTINCT race_id
                    FROM race_card_entries
                    WHERE race_date = %s
                    """,
                    (target_date,),
                )
                race_ids = {row["race_id"] for row in cursor.fetchall()}
                cursor.execute(
                    """
                    SELECT race_id
                    FROM race_fetch_status
                    WHERE race_date = %s
                    """,
                    (target_date,),
                )
                race_ids.update(row["race_id"] for row in cursor.fetchall())
                cursor.execute(
                    """
                    SELECT race_id
                    FROM horse_race_results
                    WHERE race_id LIKE %s
                    """,
                    (f"{target_date:%Y%m%d}%",),
                )
                race_ids.update(row["race_id"] for row in cursor.fetchall())
                race_ids = sorted(race_ids)
            finally:
                connection.close()
        else:
            date_string = target_date.strftime("%Y%m%d")
            race_ids = get_race_ids_by_date(date_string)

        fetch_status_by_id: dict[str, dict[str, Any]] = {}
        if race_ids:
            connection = get_connection()
            try:
                cursor = connection.cursor(dictionary=True)
                placeholders = ", ".join(["%s"] * len(race_ids))
                cursor.execute(
                    f"""
                    SELECT race_id, html_fetched, parsed, registered, error_message
                    FROM race_fetch_status
                    WHERE race_id IN ({placeholders})
                    """,
                    tuple(race_ids),
                )
                fetch_status_by_id = {
                    row["race_id"]: {
                        "html_fetched": bool(row["html_fetched"]),
                        "parsed": bool(row["parsed"]),
                        "registered": bool(row["registered"]),
                        "error_message": row["error_message"],
                    }
                    for row in cursor.fetchall()
                }
            finally:
                connection.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "race_date": target_date.isoformat(),
        "race_cards": [
            {
                "race_id": race_id,
                "url": f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}",
                "fetch_status": fetch_status_by_id.get(race_id),
            }
            for race_id in race_ids
        ],
    }


if FRONTEND_BUILD.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")


@app.get("/", include_in_schema=False)
def frontend_index() -> FileResponse:
    """Serve the built React application at the single public root."""
    index = FRONTEND_BUILD / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="Frontend build is missing")
    return FileResponse(index)
