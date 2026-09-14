"""Netkeiba fetcher entry point for the database-backed workflow."""

from datetime import datetime
import calendar
from typing import List

from src.netkeiba_fetcher.netkeiba_prevrun_fetch import (
    extract_prev_run_json,
    get_prev_run_text,
    get_race_ids_by_date,
)
from src.netkeiba_fetcher.db_register import (
    init_db,
    register_prev_run,
    register_race_fetch_status,
    update_race_fetch_status,
)


def fetch_netkeiba_data_by_date_range(start_date: str, end_date: str) -> List[str]:
    """Fetch netkeiba data for a given date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of race IDs that were processed
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    if start > end:
        raise ValueError("start_date must not be later than end_date")

    from src.jra_fetcher.db_helper import get_race_days

    race_days = get_race_days(
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
    )
    init_db()
    processed_race_ids = []

    for date_str in race_days:
        race_date = datetime.strptime(date_str, "%Y%m%d").date().isoformat()
        try:
            race_ids = get_race_ids_by_date(date_str)
            print(f"Found {len(race_ids)} races for date {date_str}")

            for race_id in race_ids:
                try:
                    register_race_fetch_status(race_id, race_date)
                    html_text = get_prev_run_text(race_id)
                    update_race_fetch_status(race_id, html_fetched=True)
                    parsed_data = extract_prev_run_json(html_text)
                    update_race_fetch_status(race_id, parsed=True)
                    register_prev_run(parsed_data)
                    update_race_fetch_status(race_id, registered=True)
                    print(f"Fetched race_id: {race_id}")
                    processed_race_ids.append(race_id)
                except Exception as e:
                    try:
                        update_race_fetch_status(
                            race_id,
                            error_message=str(e),
                        )
                    except Exception as status_error:
                        print(
                            f"Error recording status for race_id "
                            f"{race_id}: {status_error}"
                        )
                    print(f"Error processing race_id {race_id}: {e}")
        except Exception as e:
            print(f"Error fetching race IDs for date {date_str}: {e}")

    return processed_race_ids


def fetch_netkeiba_data_by_month(year: int, month: int) -> List[str]:
    """Fetch netkeiba data for a given month.

    Args:
        year: Year (e.g. 2023)
        month: Month (1-12)

    Returns:
        List of race IDs that were processed
    """
    # Generate start and end dates for the month
    start_date = f"{year:04d}-{month:02d}-01"
    
    # Calculate the last day of the month
    end_date = (
        f"{year:04d}-{month:02d}-"
        f"{calendar.monthrange(year, month)[1]:02d}"
    )
    
    return fetch_netkeiba_data_by_date_range(start_date, end_date)