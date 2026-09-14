"""Pure HTML parsing units for JRA pages.

This module contains no I/O and no network access. Every function takes an
HTML string and returns parsed data, so each unit can be tested in isolation
with fixture HTML.

Parsing targets (verified against real JRA fixtures):
    * doAction('URL', 'CNAME') link parameters
    * previous-month navigation link (``div.month a``)
    * race days (``div.past_result_line_unit > div.head > h3.sub_header``)
"""

import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

__all__ = [
    "extract_doaction_params",
    "extract_race_days",
]

_DOACTION_RE = re.compile(r"doAction\(\s*'([^']+?)'\s*,\s*'([^']+?)'\s*\)")
_JP_DATE_RE = re.compile(r"(\d{1,2})月(\d{1,2})日")


def extract_doaction_params(
    html_text: str,
    search_text: str,
    is_month_class: bool = False,
) -> List[Tuple[str, str]]:
    """Extract doAction parameters (URL, CNAME) from links in an HTML string.

    Parameters
    ----------
    html_text : str
        HTML to parse (Unicode).
    search_text : str
        Link text to match (e.g. "レース結果", "過去レース結果検索").
    is_month_class : bool
        When True, only links inside ``<div class="month">`` are considered.

    Returns
    -------
    list of (url, cname) tuples, in document order.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    results: List[Tuple[str, str]] = []

    if is_month_class:
        targets = soup.select("div.month a")
    else:
        targets = [
            a_tag
            for a_tag in soup.find_all("a")
            if search_text in a_tag.get_text()
        ]

    for a_tag in targets:
        match = _DOACTION_RE.search(a_tag.get("onclick", ""))
        if match:
            results.append((match.group(1), match.group(2)))

    return results


def extract_race_days(html_text: str, year_month: str) -> List[str]:
    """Extract race days from a month data page.

    Race days are listed per ``div.past_result_line_unit`` block whose header
    (``h3.sub_header``) contains a Japanese date such as "8月15日（土曜）".
    The page has no ``<table>`` elements, so table-based extraction finds
    nothing on real JRA pages.

    Parameters
    ----------
    html_text : str
        Month data page HTML (Unicode).
    year_month : str
        Year and month of the page in YYYYMM format.

    Returns
    -------
    list of race day strings in YYYYMMDD format, sorted ascending.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    days: List[str] = []

    for unit in soup.select("div.past_result_line_unit"):
        header = unit.select_one("h3.sub_header")
        if header is None:
            continue
        match = _JP_DATE_RE.match(header.get_text(strip=True))
        if not match:
            continue
        day = int(match.group(2))
        days.append(f"{year_month}{day:02d}")

    return sorted(days)
