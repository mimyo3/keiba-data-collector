"""Application workflow for fetching a requested JRA month range."""

import datetime

from src.jra_fetcher.db_helper import get_jra_html_metadata_by_year_month
from src.jra_fetcher.month_fetcher import (
    build_missing_month_ranges,
    fetch_month_range,
    get_current_month_link,
)


def fetch_jra_html_workflow(
    start_month: str,
    end_month: str,
    base_url: str = "https://www.jra.go.jp",
) -> None:
    """Fetch missing JRA HTML from ``start_month`` back to ``end_month``."""
    try:
        current_month = datetime.date.today().strftime("%Y%m")
        get_jra_html_metadata_by_year_month(current_month)
        db_available = True
    except Exception:
        db_available = False

    print(f"[ワークフロー開始] {start_month} から {end_month} までのHTML取得")
    print(f"[DB利用] {'利用可能' if db_available else '利用不可'}")

    if db_available:
        if start_month == current_month:
            current_base_url, next_month, url, cname = get_current_month_link(
                base_url
            )
            if end_month == current_month:
                return
            fetch_month_range(
                start_month=next_month,
                url=url,
                cname=cname,
                end_month=end_month,
                base_url=current_base_url,
            )
            return

        ranges = build_missing_month_ranges(start_month, end_month, base_url)
        if any(not params["url"] or not params["cname"] for params in ranges):
            if start_month != current_month:
                raise ValueError(
                    f"{start_month} の取得開始情報がありません。"
                    f"{current_month} から先に取得してください。"
                )

            current_base_url, next_month, url, cname = get_current_month_link(
                base_url
            )
            if end_month == current_month:
                return
            fetch_month_range(
                start_month=next_month,
                url=url,
                cname=cname,
                end_month=end_month,
                base_url=current_base_url,
            )
            return

        for params in ranges:
            fetch_month_range(**params)
        if not ranges:
            print("  すべてのHTMLファイルが存在します")
        return

    current_base_url, start_month, url, cname = get_current_month_link(base_url)
    fetch_month_range(
        start_month=start_month,
        url=url,
        cname=cname,
        end_month=end_month,
        base_url=current_base_url,
    )
