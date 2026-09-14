"""Database-backed month metadata and month-range helpers."""

from datetime import datetime
from pathlib import Path
import re

from src.jra_fetcher.db_helper import (
    get_all_jra_html_metadata,
    get_jra_html_metadata_by_year_month,
)





def get_missing_months(start_month: str, end_month: str) -> list[str]:
    """Return months that are absent or stale from start to end.

    A cached month is considered current only when its file timestamp is later
    than the month represented by the file. Files updated during that month or
    earlier are included so the workflow can refresh them.
    """
    from src.jra_fetcher.html_page import get_saved_html_for_month

    missing_months = []
    current_month = end_month
    while current_month <= start_month:
        metadata = get_saved_html_for_month(current_month)
        if _month_needs_refresh(current_month, metadata):
            missing_months.append(current_month)
        year = int(current_month[:4])
        month = int(current_month[4:6])
        if month == 12:
            current_month = f"{year + 1:04d}01"
        else:
            current_month = f"{year:04d}{month + 1:02d}"
    missing_months.reverse()

    # Also refresh stale months already present anywhere in the database.
    metadata_by_month = {}
    for metadata in get_all_jra_html_metadata():
        raw_month = str(metadata.get("year_month", ""))
        month = raw_month[:6]
        if not re.fullmatch(r"\d{6}", month):
            continue
        current = metadata_by_month.get(month)
        if current is None or (
            metadata.get("file_name") == f"monthdata_{month}"
            and current.get("file_name") != f"monthdata_{month}"
        ):
            metadata_by_month[month] = metadata

    for month, metadata in metadata_by_month.items():
        if _month_needs_refresh(month, metadata):
            missing_months.append(month)

    return sorted(set(missing_months), reverse=True)


def _month_needs_refresh(year_month: str, metadata: dict | None) -> bool:
    """Return whether a month's saved HTML is absent or not newer than it."""
    if not metadata or not metadata.get("file_name"):
        return True

    file_path = Path(__file__).resolve().parent / "data" / metadata["file_name"]
    try:
        saved_month = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y%m")
    except OSError:
        return True
    return saved_month <= year_month


def group_consecutive_months(missing_months: list[str]) -> list[tuple[str, str]]:
    """Group newer-to-older missing months into contiguous ranges."""
    if not missing_months:
        return []

    def month_total(value: str) -> int:
        return int(value[:4]) * 12 + int(value[4:6])

    groups = []
    start = previous = missing_months[0]
    for month in missing_months[1:]:
        if month_total(previous) - month_total(month) == 1:
            previous = month
        else:
            groups.append((start, previous))
            start = previous = month
    groups.append((start, previous))
    return groups
