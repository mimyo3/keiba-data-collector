"""Workflow for extracting and storing race days from saved month HTML."""

from src.jra_fetcher.db_helper import (
    get_jra_connection,
    get_jra_html_metadata_by_year_month,
    save_race_day,
)
from src.jra_fetcher.html_parser import extract_race_days
from src.jra_fetcher.html_store import HtmlStore
from src.jra_fetcher.config import DATA_DIR


def update_race_days_table(target_month: str) -> None:
    """Extract and save race days for a month already stored in metadata."""
    conn = get_jra_connection()
    conn.close()

    metadata = get_jra_html_metadata_by_year_month(target_month)
    if not metadata:
        print(f"No metadata found for month {target_month}")
        return

    html = HtmlStore(DATA_DIR).load(metadata["file_name"])
    for race_day in extract_race_days(html, target_month):
        save_race_day(target_month, race_day)

    print(f"Successfully updated race_days table for {target_month}")
