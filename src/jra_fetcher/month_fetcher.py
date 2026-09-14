"""Fetch one or more months of JRA HTML while following previous links."""

import datetime
import os
from typing import Tuple

from src.jra_fetcher.config import DATA_DIR
from src.jra_fetcher.db_helper import save_jra_html_metadata
from src.jra_fetcher.html_page import save_html_file, get_saved_html_for_month
from src.jra_fetcher.html_parser import extract_doaction_params
from src.jra_fetcher.html_store import HtmlStore
from src.jra_fetcher.http.common_http import http_client
from src.jra_fetcher.month_metadata import get_missing_months, group_consecutive_months



def _needs_month_refresh(store: HtmlStore, file_name: str, target_month: str) -> bool:
    """Return whether a cached month was last updated during or before that month."""
    path = store.path(file_name)
    if not store.exists(file_name):
        return False
    timestamp_month = datetime.datetime.fromtimestamp(
        os.path.getmtime(path)
    ).strftime("%Y%m")
    return timestamp_month <= target_month


def shift_month(year_month: str, offset: int) -> str:
    """Move a YYYYMM value by ``offset`` months."""
    year = int(year_month[:4])
    month = int(year_month[4:6])
    total = year * 12 + month - 1 + offset
    return f"{total // 12:04d}{total % 12 + 1:02d}"


def fetch_month(
    base_url: str,
    target_month: str,
    url: str,
    cname: str,
    force_fetch: bool = False,
) -> tuple:
    """Fetch or reuse one month and return its previous-month link."""
    store = HtmlStore(DATA_DIR)
    file_name = f"monthdata_{target_month}"
    if (
        store.exists(file_name)
        and not force_fetch
        and not _needs_month_refresh(store, file_name, target_month)
    ):
        html = store.load(file_name)
    else:
        response = http_client.post(base_url + url, data={"cname": cname})
        response.raise_for_status()
        html = response.content.decode("shift_jis", errors="replace")
        store.save(html, file_name)

    links = extract_doaction_params(html, "前月", is_month_class=True)
    if not links:
        raise ValueError(f"{target_month}: 前月リンクが見つかりません。")

    previous_url, previous_cname = links[0]
    save_jra_html_metadata(
        year_month=target_month,
        prev_month_url=previous_url,
        cname=previous_cname,
        file_name=file_name,
    )
    return base_url, shift_month(target_month, -1), previous_url, previous_cname


def fetch_month_range(
    start_month: str,
    url: str,
    cname: str,
    end_month: str,
    base_url: str = "https://www.jra.go.jp",
    force_fetch: bool = False,
) -> tuple:
    """Fetch months from newer ``start_month`` back to ``end_month``."""
    target_month = start_month
    count = (
        int(start_month[:4]) * 12 + int(start_month[4:6])
        - int(end_month[:4]) * 12 - int(end_month[4:6])
        + 1
    )
    if count < 1:
        raise ValueError("start_month must not be older than end_month")

    for _ in range(count):
        base_url, target_month, url, cname = fetch_month(
            base_url, target_month, url, cname, force_fetch=force_fetch
        )
    return base_url, target_month, url, cname


def get_current_month_link(
    base_url: str = "https://www.jra.go.jp",
) -> Tuple[str, str, str, str]:
    """Fetch the current-month entry point and return its previous link."""
    target_month = datetime.date.today().strftime("%Y%m")

    response = http_client.get(base_url)
    response.raise_for_status()
    top_html = response.content.decode("shift_jis", errors="replace")
    save_html_file(top_html, f"html_top_{target_month}")

    url, cname = extract_doaction_params(top_html, "レース結果")[0]
    response = http_client.post(base_url + url, data={"cname": cname})
    response.raise_for_status()
    results_html = response.content.decode("shift_jis", errors="replace")
    save_html_file(results_html, f"html2_{target_month}")

    url, cname = extract_doaction_params(results_html, "過去レース結果検索")[0]
    return fetch_month(base_url, target_month, url, cname)


def build_missing_month_ranges(
    start_month: str,
    end_month: str,
    base_url: str = "https://www.jra.go.jp",
) -> list[dict]:
    """Build fetch arguments for each contiguous missing-month range."""
    missing_months = get_missing_months(start_month, end_month)
    result = []
    for range_start, range_end in group_consecutive_months(missing_months):
        anchor = shift_month(range_start, 1)
        saved_data = get_saved_html_for_month(anchor) or {}
        result.append({
            "start_month": range_start,
            "end_month": range_end,
            "url": saved_data.get("url"),
            "cname": saved_data.get("cname"),
            "base_url": base_url,
        })
    return result
