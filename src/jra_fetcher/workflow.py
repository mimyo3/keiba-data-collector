"""Top-level workflow for fetching JRA HTML and registering race days."""

from src.jra_fetcher.html_workflow import fetch_jra_html_workflow
from src.jra_fetcher.race_day_workflow import update_race_days_table


def run_jra_workflow(start_month: str, end_month: str) -> None:
    """Fetch a month range and register its race days in the database."""
    _validate_month(start_month)
    _validate_month(end_month)
    if start_month < end_month:
        raise ValueError("start_month must not be older than end_month")

    fetch_jra_html_workflow(start_month, end_month)
    for target_month in _iter_months(start_month, end_month):
        update_race_days_table(target_month)


def _validate_month(year_month: str) -> None:
    if (
        not isinstance(year_month, str)
        or len(year_month) != 6
        or not year_month.isdigit()
        or not 1 <= int(year_month[4:6]) <= 12
    ):
        raise ValueError(
            f"年月は YYYYMM 形式で指定してください: {year_month!r}"
        )


def _iter_months(start_month: str, end_month: str):
    year, month = int(start_month[:4]), int(start_month[4:])
    end_value = int(end_month[:4]) * 12 + int(end_month[4:])

    while year * 12 + month >= end_value:
        yield f"{year:04d}{month:02d}"
        month -= 1
        if month == 0:
            year -= 1
            month = 12