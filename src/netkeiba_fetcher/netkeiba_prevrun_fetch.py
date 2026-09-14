
"""Extract previous-run information from Netkeiba PastBox HTML."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from bs4.element import Tag

from src.helpers.http_client import default_client

__all__ = ["extract_prev_run_json", "get_prev_run_text", "get_race_ids_by_date"]

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_RACE_ID_RE = re.compile(r"myrace_(\d{12})|race_id=(\d{12})|/race/(\d{12})/?")
_RACE_LIST_URL = "https://race.netkeiba.com/top/race_list_sub.html"
_NEWSPAPER_URL = "https://race.netkeiba.com/race/newspaper_master.html"
RAW_BASE = Path(__file__).resolve().parents[2] / "data" / "netkeiba" / "html"
NEWSPAPER_DIR = RAW_BASE / "newspaper"
RACE_LIST_DIR = RAW_BASE / "race_list"

_DUMMY_RUNNING_TYPES = {
    "＊＊＊＊型",
    "＊＊＊＊＊型",
    "****型",
}


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    value = re.sub(r"\s+", " ", value).strip()
    return value or None


def _to_int(value: Any, field_name: str = "") -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    text = _clean(str(value))
    if not text:
        return None

    match = re.search(r"-?\d+", text)
    if not match:
        return None

    try:
        return int(match.group())
    except ValueError:
        return None


def _to_float(value: Any, field_name: str = "") -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = _clean(str(value))
    if not text:
        return None

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return float(match.group())
    except ValueError:
        return None


def _extract_number(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    match = re.search(r"\d+", value)
    return match.group() if match else None


def _strip_parens(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    value = value.strip()
    value = value.strip("()")
    return value or None


def _detect_race_id(text: str) -> Optional[str]:
    """Detect the race id represented by the supplied newspaper HTML."""

    race_ids = _RACE_ID_RE.findall(text)

    if not race_ids:
        # Some HTML uses race_id=XXXXXXXXXXXX instead of /race/XXXXXXXXXXXX/.
        race_ids = re.findall(r"race_id[=/](\d{12})", text)

    if not race_ids:
        return None

    # The newspaper page can contain the same race id many times.
    # The most frequent id is the page's target race.
    counts: Dict[str, int] = {}
    for race_id in race_ids:
        counts[race_id] = counts.get(race_id, 0) + 1

    return max(counts, key=counts.get)


def _parse_jockey_block(
    dd: Optional[Tag],
) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    """Return (sex_age, jockey, weight) from the current race horse block."""

    if dd is None:
        return None, None, None

    barei = dd.select_one("span.Barei")
    sex_age = _clean(barei.get_text(" ", strip=True)) if barei else None

    jockey_tag = dd.select_one("a[href*='/jockey/']")
    jockey = None

    if jockey_tag is not None:
        jockey = _clean(jockey_tag.get_text(" ", strip=True))

        for change in jockey_tag.select(".Change"):
            change_text = _clean(change.get_text(" ", strip=True))
            if change_text and jockey:
                jockey = jockey.replace(change_text, "").strip()

    weight = None

    # Weight is normally the final direct span in the jockey block.
    direct_spans = dd.find_all("span", recursive=False)
    for span in reversed(direct_spans):
        value = _to_float(span.get_text(" ", strip=True))
        if value is not None:
            weight = value
            break

    return sex_age, jockey, weight


def _find_prev_box(dl: Tag) -> Tuple[Optional[Tag], Optional[Tag]]:
    """Find the first actual PastBox and the Rest item."""

    ul = dl.select_one("dd.Past_Wrapper ul.Past_Direction")

    if ul is None:
        return None, None

    rest_li = ul.select_one("li.Rest")

    for li in ul.select("li.Past"):
        box = li.select_one("div.PastBox")

        if box is None:
            continue

        classes = box.get("class") or []

        if "Past_Dummy" in classes:
            continue

        return box, rest_li

    return None, rest_li


def _parse_rest(rest_li: Tag) -> Dict[str, Any]:
    """Represent a horse for which no PastBox exists."""

    return {
        "previous_race_id": None,
        "previous_race": None,
        "pass_order": None,
        "speed_index": None,
        "running_style": None,
        "meta": {
            "rest": _clean(rest_li.get_text(" ", strip=True)),
        },
    }


def _parse_data01(data01: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Parse strings such as:

        08/15 新潟 3R

    into date/place/race-number components.
    """

    result: Dict[str, Optional[str]] = {
        "month_day": None,
        "place_num": None,
        "race_number": None,
    }

    if not data01:
        return result

    text = _clean(data01)
    if not text:
        return result

    date_match = re.search(r"(\d{1,2}/\d{1,2})", text)
    if date_match:
        result["month_day"] = date_match.group(1)

    race_match = re.search(r"([0-9]{1,2})R", text)
    if race_match:
        result["race_number"] = race_match.group(1)

    # Remove date and race number, leaving the venue.
    place = re.sub(r"\d{1,2}/\d{1,2}", "", text)
    place = re.sub(r"[0-9]{1,2}R", "", place)
    place = _clean(place)

    result["place_num"] = place

    return result


def _parse_track_distance(value: Optional[str]) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse Data09 such as:

        芝1800
        ダ1200
        障3000

    into (track, distance).
    """

    if not value:
        return None, None

    text = _clean(value)
    if not text:
        return None, None

    match = re.search(r"(\d+)", text)

    if not match:
        return text, None

    distance = int(match.group(1))
    track = text[: match.start()].strip()

    return track or None, distance


def _parse_corners(
    data20: Optional[Tag],
) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """
    Return:

        huri1, corner1, corner2, corner3, corner4, bias_side

    Data20 can contain:

        <span class="Corner Note">13<span>鈍</span></span>
        <span class="Corner">12</span>
        ...
        <span class="Bias">中走</span>
    """

    if data20 is None:
        return None, None, None, None, None, None

    huri1 = None
    first_corner = None

    note = data20.select_one("span.Corner.Note")

    if note is not None:
        nested = note.find("span")

        if nested is not None:
            huri1 = _clean(nested.get_text(" ", strip=True))

        # Remove nested annotation before obtaining the corner number.
        if nested is not None:
            nested.extract()

        first_corner = _clean(note.get_text(" ", strip=True))

    corners: List[str] = []

    for corner in data20.select("span.Corner"):
        value = _clean(corner.get_text(" ", strip=True))

        if value:
            corners.append(value)

    if first_corner is not None:
        # The Note corner was already included in the selector.
        if corners:
            corners[0] = first_corner
        else:
            corners.append(first_corner)

    while len(corners) < 4:
        corners.append(None)  # type: ignore[arg-type]

    bias_tag = data20.select_one("span.Bias")
    bias_side = (
        _clean(bias_tag.get_text(" ", strip=True))
        if bias_tag is not None
        else None
    )

    return (
        huri1,
        corners[0],
        corners[1],
        corners[2],
        corners[3],
        bias_side,
    )


def _parse_level_counts(box: Tag) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse the PastBox LevelCount values.

    These are the race-level mainrank/subrank values.
    """

    mainrank = None
    subrank = None

    for data in box.select("div.LevelCount span.Data"):
        line = _clean(data.get_text(" ", strip=True))

        if not line:
            continue

        match = re.search(r"勝ち\s*(\d+)", line)
        if match:
            mainrank = int(match.group(1))

        match = re.search(r"複勝\s*(\d+)", line)
        if match:
            subrank = int(match.group(1))

    return mainrank, subrank


def _parse_grade(box: Tag) -> Optional[str]:
    """Return the grade displayed by the PastBox, when present."""

    grade = box.select_one(".Icon_GradeType")

    if grade is None:
        return None

    return _clean(grade.get_text(" ", strip=True))


def _parse_prev_box(box: Tag) -> Dict[str, Any]:
    """
    Parse one PastBox.

    A PastBox contains both:
      - race-level historical information
      - this horse's historical result

    The returned dictionary intentionally keeps both sets of information
    together. DB registration later separates them into `races` and
    `horse_race_results`.
    """

    def g(*classes: str) -> Optional[str]:
        for cls in classes:
            tag = box.select_one("span." + cls)
            if tag is not None:
                return _clean(tag.get_text(" ", strip=True))
        return None

    # ------------------------------------------------------------
    # Historical race id
    # ------------------------------------------------------------
    anchor = box.select_one("a[href*='/race/']")
    if anchor is None:
        anchor = box.select_one("a[href*='race_id=']")

    race_id = None

    if anchor is not None:
        href = anchor.get("href", "")

        match = re.search(r"/race/(\d{12})", href)

        if match is None:
            match = re.search(r"race_id[=/](\d{12})", href)

        if match:
            race_id = match.group(1)

    # ------------------------------------------------------------
    # Race header
    # ------------------------------------------------------------
    data01 = g("Data01")
    data01_info = _parse_data01(data01)

    race_name_tag = box.select_one("span.Data02 .RaceName")

    if race_name_tag is not None:
        race_name = _clean(race_name_tag.get_text(" ", strip=True))
    else:
        race_name = g("Data02")

    # Data09 = track + distance, e.g. 芝1800
    track, distance = _parse_track_distance(g("Data09"))

    # Data03 = race condition, e.g. 国際 ハンデ
    race_condition_tag = box.select_one("span.Data03")

    race_condition = None

    if race_condition_tag is not None:
        race_condition = _clean(
            race_condition_tag.get_text(" ", strip=True)
        )

    # Data11 = actual track condition, e.g. 良
    condition_tag = box.select_one("span.Data11")

    condition = None

    if condition_tag is not None:
        # Ana03 is a development/pace type and is NOT the track condition.
        ana03 = condition_tag.select_one(".Ana03")

        if ana03 is not None:
            ana03.extract()

        condition = _clean(condition_tag.get_text(" ", strip=True))

    # ------------------------------------------------------------
    # Race-level values
    # ------------------------------------------------------------
    mainrank, subrank = _parse_level_counts(box)
    grade = _parse_grade(box)

    data20 = box.select_one("span.Data20")

    (
        huri1,
        corner1,
        corner2,
        corner3,
        corner4,
        bias_side,
    ) = _parse_corners(data20)

    bias_type = g("Ana01")
    bias_shift = g("Ana02")

    bias_parts = [
        value
        for value in (bias_type, bias_shift, bias_side)
        if value
    ]

    bias = bias_type

    # ------------------------------------------------------------
    # Horse result values
    # ------------------------------------------------------------
    popularity = _to_int(_extract_number(g("Data07")))
    post = _to_int(_extract_number(g("Data06")))
    field_size = _to_int(_extract_number(g("Data05")))

    tyakujun_tag = box.select_one("span.Data04 .Num")
    tyakujun = (
        _to_int(tyakujun_tag.get_text(" ", strip=True))
        if tyakujun_tag is not None
        else None
    )

    time = g("Data12")

    # Data13 is pace (S/H/M/etc.), NOT margin.
    pace = g("Data13")

    # Ana02 is the historical margin.
    margin = g("Ana02")

    develop_type = g("Ana03")

    historical_jockey = g("Data14")
    historical_weight = _to_float(g("Data15"))

    horse_weight_text = g("Data16")
    horse_weight = _to_int(horse_weight_text)

    weight_change = _to_int(_strip_parens(g("Data17")))

    first_half = _to_float(g("Data19"))
    second_half = _to_float(g("Data21"))

    # ------------------------------------------------------------
    # Time index
    # ------------------------------------------------------------
    time_index_total = _to_int(g("TimeIndex01"))

    time_index_detail = None

    ti_tag = box.select_one("span.TimeIndex02")

    if ti_tag is not None:
        numbers = _NUM_RE.findall(ti_tag.get_text(" ", strip=True))

        if numbers:
            time_index_detail = [int(number) for number in numbers]

    time_index_start = None
    time_index_run = None
    time_index_finish = None

    if time_index_detail:
        if len(time_index_detail) >= 1:
            time_index_start = time_index_detail[0]
        if len(time_index_detail) >= 2:
            time_index_run = time_index_detail[1]
        if len(time_index_detail) >= 3:
            time_index_finish = time_index_detail[2]

    # ------------------------------------------------------------
    # Other analysis values
    # ------------------------------------------------------------
    running_type = g("Ana05")
    ana04 = g("Ana04")

    # Existing parser semantics:
    # pass_order = third corner
    # speed_index = TimeIndex01
    pass_order = _to_int(corner3)
    speed_index = time_index_total

    # ------------------------------------------------------------
    # Combined historical record
    # ------------------------------------------------------------
    meta = {
        # race-level
        "race_id": race_id,
        "race_date": (
            race_id[:8]
            if race_id and len(race_id) == 12
            else None
        ),
        "place_num": data01_info["place_num"],
        "race_number": data01_info["race_number"],
        "race_name": race_name,
        "grade": grade,
        "race_condition": race_condition,
        "condition": condition,
        "tousu": field_size,
        "distance": distance,
        "track": track,
        "bias": bias,
        "ichinuke": (
            str(mainrank)
            if mainrank is not None
            else None
        ),
        "jitenn": (
            str(subrank)
            if subrank is not None
            else None
        ),
        "staus": develop_type,
        "pace": pace,
        "mainrank": mainrank,
        "subrank": subrank,

        # horse-level
        "post": post,
        "popularity": popularity,
        "tyakujun": tyakujun,
        "time": time,
        "margin": margin,
        "develop_type": develop_type,
        "weight": historical_weight,
        "horse_weight": horse_weight,
        "weight_change": weight_change,
        "sex_age": None,
        "jockey": historical_jockey,
        "first_half": first_half,
        "second_half": second_half,
        "corners": (
            ",".join(
                value for value in
                (corner1, corner2, corner3, corner4)
                if value is not None
            )
            if any(
                value is not None
                for value in (corner1, corner2, corner3, corner4)
            )
            else None
        ),
        "huri1": huri1,
        "corner1": corner1,
        "corner2": corner2,
        "corner3": corner3,
        "corner4": corner4,
        "corner_position": bias_side,
        "time_index_detail": (
            time_index_detail[0]
            if time_index_detail
            else None
        ),
        "distance_value": distance,
        "time_index_total": time_index_total,
        "time_index_start": time_index_start,
        "time_index_run": time_index_run,
        "time_index_finish": time_index_finish,
        "pass_order": pass_order,
        "speed_index": speed_index,
        "running_style": running_type,
        "running_type": running_type,
        "ana04": ana04,
        "bias_type": bias_type,
        "bias_shift": bias_shift,
        "bias_side": bias_side,
    }

    return {
        "previous_race_id": race_id,
        "previous_race": data01,
        "pass_order": pass_order,
        "speed_index": speed_index,
        "running_style": running_type,
        "running_type": running_type,
        "meta": meta,
    }


def _parse_horse(dl: Tag) -> Optional[Dict[str, Any]]:
    """Parse one horse block and its first available PastBox."""

    horse_name_tag = dl.select_one("dt.HorseName")

    if horse_name_tag is None:
        return None

    horse_name = _clean(horse_name_tag.get_text(" ", strip=True))

    if not horse_name:
        return None

    horse_link = horse_name_tag.select_one(
    "a[href*='horse_id='], a[href*='/horse/']"
    )
    horse_id = None

    if horse_link is not None:
        href = horse_link.get("href", "")

        match = re.search(r"[?&]horse_id=(\d+)", href)

        if match is None:
            match = re.search(r"/horse/(\d+)/", href)

        if match:
            horse_id = match.group(1)

    jockey_block = dl.select_one("dd.Jockey")

    sex_age, jockey, weight = _parse_jockey_block(jockey_block)

    running_type_tag = dl.select_one("dd.RunningType")
    running_type = (
        _clean(running_type_tag.get_text(" ", strip=True))
        if running_type_tag is not None
        else None
    )

    if running_type in _DUMMY_RUNNING_TYPES:
        running_type = None

    horse_no = None

    horse_no_tag = dl.select_one(
        "span.Num, span.HorseNo, span.Umaban"
    )

    if horse_no_tag is not None:
        horse_no = _to_int(
            horse_no_tag.get_text(" ", strip=True)
        )

    horse: Dict[str, Any] = {
        "horse_no": horse_no,
        "horse_id": horse_id,
        "horse_name": horse_name,
        "jockey": jockey,
        "sex_age": sex_age,
        "weight": weight,
        "running_type": running_type,
        "previous_race_id": None,
        "previous_race": None,
        "pass_order": None,
        "speed_index": None,
        "running_style": None,
        "meta": None,
    }

    box, rest_li = _find_prev_box(dl)

    if box is not None:
        horse.update(_parse_prev_box(box))

        # The historical PastBox weight/sex-age/jockey values take
        # precedence over the current target-race block where available.
        meta = horse.get("meta")

        if isinstance(meta, dict):
            meta["sex_age"] = sex_age

        # Current target race's sex_age is intentionally only used as
        # horse identity information. It is not used as historical race
        # data other than the requested horse field.
    elif rest_li is not None:
        horse.update(_parse_rest(rest_li))

    return horse


def extract_prev_run_json(text: str) -> Dict[str, Any]:
    """
    Extract PastBox historical data.

    The returned structure contains both race-level and horse-level data
    from each PastBox. Database registration is responsible for separating
    these values into `races` and `horse_race_results`.
    """

    soup = BeautifulSoup(text, "lxml")

    horses: List[Dict[str, Any]] = []

    for dl in soup.select("dl.HorseList"):
        horse = _parse_horse(dl)

        if horse is not None:
            horses.append(horse)

    return {
        "race_id": _detect_race_id(text),
        "horses": horses,
    }


def get_prev_run_text(
    race_id: str,
    *,
    force_fetch: bool = False,
    ttl: int | None = None,
) -> str:
    """Return the raw HTML of the netkeiba newspaper page for *race_id*.

    The page is fetched from
    ``https://race.sp.netkeiba.com/race/newspaper.html?race_id=<race_id>``
    via :data:`http_client.default_client` (inheriting its rate limiting
    and, when ``ttl`` is given, its in‑memory cache) and the original
    HTML is saved to ``data/raw/race_sp_newspaper_<race_id>.html``.

    If the raw file already exists and ``force_fetch`` is ``False``, the
    cached file is returned directly without any HTTP request.

    Parameters
    ----------
    race_id:
        The netkeiba race id (``YYYYMMDDRRRR``, 12 digits), as used in
        ``race_id=`` links throughout netkeiba pages.
    force_fetch:
        If ``True`` the raw file is ignored and a new HTTP request is sent.
    ttl:
        Optional time‑to‑live in seconds for the HTTP client's in‑memory
        cache.  When ``None`` (default) the client performs a fresh
        request (subject to its per‑host rate limit).

    Returns
    -------
    str
        Raw HTML of the newspaper page.

    Raises
    ------
    ValueError
        If *race_id* is not a 12‑digit string.
    requests.HTTPError
        If the server responds with a non‑2xx status code.
    """
    if not (isinstance(race_id, str) and race_id.isdigit() and len(race_id) == 12):
        raise ValueError(f"race_id は12桁の数字である必要があります: {race_id!r}")

    raw_file = NEWSPAPER_DIR / f"race_sp_newspaper_{race_id}.html"
    if raw_file.exists() and not force_fetch:
        print(f"キャッシュのnetkeiba HTMLを使用: {raw_file}")
        return raw_file.read_text(encoding="utf-8")

    print(f"netkeiba 競馬新聞 HTMLを取得中: race_id={race_id}")
    html = default_client.get(_NEWSPAPER_URL, params={"race_id": race_id}, ttl=ttl)
    NEWSPAPER_DIR.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(html, encoding="utf-8")
    print(f"netkeiba HTMLを {raw_file} に保存しました (race_id={race_id})")
    return html


def get_race_ids_by_date(
    date: str,
    *,
    force_fetch: bool = False,
    ttl: int | None = None,
) -> list[str]:
    """指定された日付 (YYYYMMDD) の全 race_id をリストとして返す。

    ``https://race.netkeiba.com/top/race_list_sub.html?kaisai_date=YYYYMMDD``
    からレース一覧ページを取得し、HTML 内の href 属性から race_id (12桁) を抽出する。
    初回取得した HTML は ``data/raw/race_list_sub_YYYYMMDD.html`` にキャッシュされ、
    2 回目以降はキャッシュをそのまま使用して race_id の抽出のみを行う。

    Parameters
    ----------
    date:
        レース開催日 (YYYYMMDD 形式の 8 桁数字)。
    force_fetch:
        True にするとキャッシュを無視して毎回 HTTP 取得を行う。
    ttl:
        HTTP client の in-memory キャッシュの TTL (秒)。

    Returns
    -------
    list[str]
        race_id のリスト (各要素は YYYYMMDDRRRR 形式の 12 桁文字列)。

    Raises
    ------
    ValueError
        date が 8 桁数字でない場合に発生。
    requests.HTTPError
        サーバーが 2xx 以外のステータスを返した場合。

    Examples
    --------
    >>> ids = get_race_ids_by_date("20260725")
    >>> len(ids)
    36
    >>> ids[0]
    '202604020101'
    """
    if not (isinstance(date, str) and date.isdigit() and len(date) == 8):
        raise ValueError(f"日付は YYYYMMDD 形式の 8 桁数字である必要があります: {date!r}")

    raw_file = RACE_LIST_DIR / f"race_list_sub_{date}.html"

    if raw_file.exists() and not force_fetch:
        print(f"キャッシュのレース一覧 HTML を使用: {raw_file}")
        html = raw_file.read_text(encoding="utf-8")
    else:
        print(f"netkeiba レース一覧 HTML を取得中: kaisai_date={date}")
        html = default_client.get(_RACE_LIST_URL, params={"kaisai_date": date}, ttl=ttl)
        RACE_LIST_DIR.mkdir(parents=True, exist_ok=True)
        raw_file.write_text(html, encoding="utf-8")
        print(f"netkeiba レース一覧 HTML を {raw_file} に保存しました (date={date})")

    # HTML 解析して race_id を抽出
    soup = BeautifulSoup(html, "html.parser")
    race_ids: list[str] = []
    for tag in soup.find_all("a"):
        href = tag.get("href", "")
        # href属性からレースIDを抽出
        match = re.search(r"race_id=(\d{12})", href)
        if match:
            race_id = match.group(1)
            if race_id not in race_ids:
                race_ids.append(race_id)
        else:
            # myrace_形式のIDを抽出
            match = re.search(r"myrace_(\d{12})", href)
            if match:
                race_id = match.group(1)
                if race_id not in race_ids:
                    race_ids.append(race_id)

    print(f"{date} のレースを {len(race_ids)} 件取得しました: {race_ids}")
    return race_ids

