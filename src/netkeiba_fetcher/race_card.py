"""Fetch and parse declared-horse data from Netkeiba race cards."""

from __future__ import annotations

import html as html_module
import re
from datetime import datetime
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from src.helpers.http_client import default_client

_RACE_CARD_URL = "https://race.netkeiba.com/race/shutuba.html"
_HORSE_ID_RE = re.compile(r"/horse/(\d+)")
_WEIGHT_RE = re.compile(r"(\d+)\s*\(\s*([+-]?\d+)\s*\)")
_NUMBER_RE = re.compile(r"\d+")
_RACE_DATE_RE = re.compile(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日")
_NEWSPAPER_WEIGHT_RE = re.compile(
    r"(\d+)\s*kg\s*\(\s*([+-]?\d+)\s*\)"
)
_HEAD_TAG_RE = re.compile(r"<(?:meta|link)\b[^>]*>", re.IGNORECASE)
_ATTRIBUTE_RE = re.compile(
    r"""([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))"""
)
_TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def get_race_card_text(race_id: str) -> str:
    """Fetch the Netkeiba race-card HTML for one race."""
    if not (
        isinstance(race_id, str)
        and race_id.isdigit()
        and len(race_id) == 12
    ):
        raise ValueError(f"race_id は12桁の数字である必要があります: {race_id!r}")

    return default_client.get(_RACE_CARD_URL, params={"race_id": race_id})


def _cell_text(cells: list[Any], index: int) -> str:
    if index >= len(cells):
        return ""
    return cells[index].get_text(" ", strip=True)


def _integer(value: str) -> int | None:
    match = _NUMBER_RE.search(value)
    return int(match.group()) if match else None


def _decimal(value: str) -> Decimal | None:
    match = re.search(r"\d+(?:\.\d+)?", value)
    return Decimal(match.group()) if match else None


def extract_race_date(html: str, race_id: str) -> str:
    """Extract the actual race date from a page verified to match race_id."""
    if not (
        isinstance(race_id, str)
        and race_id.isdigit()
        and len(race_id) == 12
    ):
        raise ValueError(f"race_id は12桁の数字である必要があります: {race_id!r}")

    header = html[:16_384]
    page_urls = []
    for tag_match in _HEAD_TAG_RE.finditer(header):
        attributes = {
            match.group(1).lower(): next(
                value for value in match.groups()[1:] if value is not None
            )
            for match in _ATTRIBUTE_RE.finditer(tag_match.group())
        }
        if (
            tag_match.group().lower().startswith("<meta")
            and attributes.get("property", "").lower() == "og:url"
            and attributes.get("content")
        ):
            page_urls.append(attributes["content"])
        elif (
            tag_match.group().lower().startswith("<link")
            and "canonical" in attributes.get("rel", "").lower().split()
            and attributes.get("href")
        ):
            page_urls.append(attributes["href"])

    page_race_ids = {
        race_ids[0]
        for page_url in page_urls
        if (race_ids := parse_qs(urlparse(page_url).query).get("race_id"))
    }
    if race_id not in page_race_ids:
        raise ValueError(
            f"取得したHTMLのページIDが一致しません: race_id={race_id}"
        )

    title_match = _TITLE_RE.search(header)
    title = (
        re.sub(r"\s+", " ", html_module.unescape(title_match.group(1))).strip()
        if title_match
        else ""
    )
    match = _RACE_DATE_RE.search(title)
    if match is None:
        raise ValueError(
            f"ページタイトルから開催日を取得できません: race_id={race_id}"
        )

    try:
        race_date = datetime(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        ).date()
    except ValueError as exc:
        raise ValueError(
            f"ページの開催日が不正です: race_id={race_id}"
        ) from exc

    return race_date.isoformat()


def extract_race_card_entries(
    html: str,
    race_id: str,
) -> list[dict[str, Any]]:
    """Parse race-card entries, deliberately excluding favorite and memo cells."""
    if not (
        isinstance(race_id, str)
        and race_id.isdigit()
        and len(race_id) == 12
    ):
        raise ValueError(f"race_id は12桁の数字である必要があります: {race_id!r}")

    race_date = extract_race_date(html, race_id)
    soup = BeautifulSoup(html, "html.parser")
    entries: list[dict[str, Any]] = []

    for row in soup.select("table.Shutuba_Table tr.HorseList"):
        cells = row.select("td")
        if len(cells) < 11:
            continue

        horse_link = cells[3].select_one(".HorseName a, a[href*='/horse/']")
        if horse_link is None:
            continue

        horse_name = horse_link.get_text(" ", strip=True)
        horse_id_match = _HORSE_ID_RE.search(horse_link.get("href", ""))
        jockey_link = cells[6].select_one("a")
        trainer_link = cells[7].select_one("a")
        trainer_area = cells[7].select_one(".Label1")
        weight_match = _WEIGHT_RE.search(_cell_text(cells, 8))

        entries.append(
            {
                "race_id": race_id,
                "race_date": race_date,
                "frame_number": _integer(_cell_text(cells, 0)),
                "horse_number": _integer(_cell_text(cells, 1)),
                "horse_id": (
                    horse_id_match.group(1) if horse_id_match else None
                ),
                "horse_name": horse_name,
                "sex_age": _cell_text(cells, 4) or None,
                "carried_weight": _decimal(_cell_text(cells, 5)),
                "jockey": (
                    jockey_link.get_text(" ", strip=True)
                    if jockey_link
                    else None
                ),
                "trainer_area": (
                    trainer_area.get_text(" ", strip=True)
                    if trainer_area
                    else None
                ),
                "trainer": (
                    trainer_link.get_text(" ", strip=True)
                    if trainer_link
                    else None
                ),
                "horse_weight": (
                    int(weight_match.group(1)) if weight_match else None
                ),
                "weight_change": (
                    int(weight_match.group(2)) if weight_match else None
                ),
                "win_odds": _decimal(_cell_text(cells, 9)),
                "popularity": _integer(_cell_text(cells, 10)),
            }
        )

    if not entries:
        raise ValueError(
            f"出馬表から登録対象の馬が見つかりません: race_id={race_id}"
        )

    if any(entry["horse_number"] is None for entry in entries):
        raise ValueError(f"出馬表に馬番がない行があります: race_id={race_id}")

    return entries


def extract_newspaper_race_card_entries(
    html: str,
    race_id: str,
) -> list[dict[str, Any]]:
    """Extract all current runners from a cached Netkeiba newspaper page."""
    race_date = extract_race_date(html, race_id)
    soup = BeautifulSoup(html, "html.parser")
    wrapper = soup.select_one(".HorseList_Wrapper")
    if wrapper is None:
        raise ValueError(f"出馬表一覧が新聞HTMLにありません: race_id={race_id}")

    horse_rows = wrapper.find_all("dl", class_="HorseList", recursive=False)
    type_rows = soup.select("div.Type")
    if not horse_rows or len(horse_rows) != len(type_rows):
        raise ValueError(
            f"新聞HTMLの出走馬情報が不完全です: race_id={race_id}, "
            f"出走馬={len(horse_rows)}, 馬情報={len(type_rows)}"
        )

    entries: list[dict[str, Any]] = []
    for row, type_row in zip(horse_rows, type_rows):
        direct_cells = row.find_all("dt", recursive=False)
        name_cell = row.find("dt", class_="HorseName", recursive=False)
        horse_link = (
            name_cell.select_one("a[href*='/horse/']")
            if name_cell is not None
            else None
        )
        jockey_cell = row.find("dd", class_="Jockey", recursive=False)
        if len(direct_cells) < 3 or horse_link is None or jockey_cell is None:
            raise ValueError(
                f"新聞HTMLの出走馬行を解析できません: race_id={race_id}"
            )

        horse_weight_match = _NEWSPAPER_WEIGHT_RE.search(
            type_row.select_one("dt.Horse07").get_text(" ", strip=True)
            if type_row.select_one("dt.Horse07") is not None
            else ""
        )
        jockey_link = jockey_cell.select_one("a[href*='/jockey/']")
        horse_id_match = _HORSE_ID_RE.search(horse_link.get("href", ""))
        jockey_name = (
            jockey_link.get_text(" ", strip=True)
            if jockey_link is not None
            else None
        )
        if jockey_link is not None and jockey_name:
            for change in jockey_link.select(".Change"):
                change_text = change.get_text(" ", strip=True)
                if change_text:
                    jockey_name = jockey_name.replace(change_text, "").strip()
        weight_text = next(
            (
                span.get_text(" ", strip=True)
                for span in reversed(jockey_cell.find_all("span", recursive=False))
                if _decimal(span.get_text(" ", strip=True)) is not None
            ),
            "",
        )

        entries.append(
            {
                "race_id": race_id,
                "race_date": race_date,
                "frame_number": _integer(direct_cells[0].get_text(" ", strip=True)),
                "horse_number": _integer(direct_cells[1].get_text(" ", strip=True)),
                "horse_id": horse_id_match.group(1) if horse_id_match else None,
                "horse_name": horse_link.get_text(" ", strip=True),
                "sex_age": (
                    jockey_cell.select_one(".Barei").get_text(" ", strip=True)
                    if jockey_cell.select_one(".Barei") is not None
                    else None
                ),
                "carried_weight": _decimal(weight_text),
                "jockey": (
                    jockey_name
                ),
                "trainer_area": None,
                "trainer": None,
                "horse_weight": (
                    int(horse_weight_match.group(1))
                    if horse_weight_match
                    else None
                ),
                "weight_change": (
                    int(horse_weight_match.group(2))
                    if horse_weight_match
                    else None
                ),
                "win_odds": None,
                "popularity": None,
            }
        )

    if any(entry["horse_number"] is None for entry in entries):
        raise ValueError(f"新聞HTMLに馬番がない出走馬があります: race_id={race_id}")

    return sorted(entries, key=lambda entry: entry["horse_number"])
