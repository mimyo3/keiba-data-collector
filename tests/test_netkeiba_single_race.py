from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import MagicMock, call, patch

from fastapi import HTTPException

from src.backend.server import (
    fetch_netkeiba_race_data,
    get_registered_race_card,
)
from src.netkeiba_fetcher.api_entry import (
    fetch_netkeiba_data_by_date_range,
    fetch_netkeiba_previous_runs,
    fetch_and_register_race_card,
)
from src.netkeiba_fetcher.db_register import init_db, register_race_card_entries
from src.netkeiba_fetcher.netkeiba_prevrun_fetch import get_prev_run_text
from src.netkeiba_fetcher.race_card import extract_race_card_entries
from src.netkeiba_fetcher.race_date_repair import (
    repair_race_dates_from_cached_newspapers,
)


RACE_CARD_HTML = """
<html>
  <head>
    <meta property="og:url" content="https://race.netkeiba.com/race/shutuba.html?race_id=202610010101">
    <link rel="canonical" href="https://race.netkeiba.com/race/shutuba.html?race_id=202610010101">
    <title>2歳未勝利 出馬表 | 2026年10月1日 東京1R - netkeiba</title>
  </head>
  <table class="Shutuba_Table">
    <tr class="HorseList">
      <td class="Waku1">2</td>
      <td class="Umaban2">3</td>
      <td class="CheckMark"><select><option>◎</option></select></td>
      <td class="HorseInfo">
        <span class="HorseName">
          <a href="https://db.netkeiba.com/horse/2024101234">テストホース</a>
        </span>
      </td>
      <td class="Barei">牡3</td>
      <td>57.0</td>
      <td class="Jockey"><a>テスト騎手</a></td>
      <td class="Trainer"><span class="Label1">美浦</span><a>テスト厩舎</a></td>
      <td class="Weight">480(+2)</td>
      <td class="Popular">4.5</td>
      <td class="Popular_Ninki">2</td>
      <td class="FavRegist">お気に入り</td>
      <td class="FavMemo">お気に入りメモ</td>
      <td class="Note0">馬メモ</td>
    </tr>
  </table>
</html>
"""

NEWSPAPER_HTML = """
<html>
  <head>
    <meta property="og:url" content="https://race.netkeiba.com/race/newspaper_master.html?race_id=202610020301">
    <link rel="canonical" href="https://race.netkeiba.com/race/newspaper_master.html?race_id=202610020301">
    <title>3歳以上障害未勝利 | 2026年7月4日 小倉1R - netkeiba</title>
  </head>
</html>
"""


class TestSingleRaceNetkeibaFetch(unittest.TestCase):
    def test_single_race_fetch_registers_parsed_previous_runs(self):
        race_id = "202610020301"
        parsed_data = {"race_id": race_id, "horses": [{"horse_name": "テスト馬"}]}

        with (
            patch("src.netkeiba_fetcher.api_entry.init_db") as init_db,
            patch(
                "src.netkeiba_fetcher.api_entry.register_race_fetch_status"
            ) as register_status,
            patch(
                "src.netkeiba_fetcher.api_entry.update_race_fetch_status"
            ) as update_status,
            patch(
                "src.netkeiba_fetcher.api_entry.get_prev_run_text",
                return_value=NEWSPAPER_HTML,
            ) as get_newspaper,
            patch(
                "src.netkeiba_fetcher.api_entry.extract_prev_run_json",
                return_value=parsed_data,
            ),
            patch(
                "src.netkeiba_fetcher.api_entry.register_prev_run"
            ) as register_previous_runs,
        ):
            fetch_netkeiba_previous_runs(race_id)

        init_db.assert_called_once_with()
        register_status.assert_called_once_with(race_id, "2026-07-04")
        get_newspaper.assert_called_once_with(race_id)
        register_previous_runs.assert_called_once_with(parsed_data)
        self.assertEqual(
            update_status.call_args_list,
            [
                call(race_id, html_fetched=True),
                call(race_id, parsed=True),
                call(race_id, registered=True),
            ],
        )

    def test_newspaper_html_is_saved_using_existing_cache_path(self):
        race_id = "202610010101"
        html = "<html><body>newspaper</body></html>"

        with TemporaryDirectory() as temp_dir:
            newspaper_dir = Path(temp_dir) / "newspaper"
            with (
                patch(
                    "src.netkeiba_fetcher.netkeiba_prevrun_fetch.NEWSPAPER_DIR",
                    newspaper_dir,
                ),
                patch(
                    "src.netkeiba_fetcher.netkeiba_prevrun_fetch.default_client.get",
                    return_value=html,
                ) as get,
            ):
                result = get_prev_run_text(race_id)

            self.assertEqual(result, html)
            self.assertEqual(
                (newspaper_dir / f"race_sp_newspaper_{race_id}.html").read_text(
                    encoding="utf-8"
                ),
                html,
            )
            get.assert_called_once_with(
                "https://race.netkeiba.com/race/newspaper_master.html",
                params={"race_id": race_id},
                ttl=None,
            )

    def test_single_race_endpoint_rejects_invalid_race_id(self):
        with self.assertRaises(HTTPException) as error:
            fetch_netkeiba_race_data("invalid")

        self.assertEqual(error.exception.status_code, 400)

    def test_registered_race_card_returns_only_the_requested_race(self):
        connection = MagicMock()
        connection.cursor.return_value.fetchall.return_value = [
            {
                "race_id": "202610020301",
                "race_date": date(2026, 7, 4),
                "horse_number": 3,
                "horse_name": "テストホース",
                "carried_weight": 57.0,
            }
        ]

        with patch(
            "src.backend.server.get_connection",
            return_value=connection,
        ):
            result = get_registered_race_card("202610020301")

        self.assertEqual(result["race_id"], "202610020301")
        self.assertEqual(result["entries"][0]["race_date"], "2026-07-04")
        self.assertEqual(result["entries"][0]["horse_name"], "テストホース")
        query, params = connection.cursor.return_value.execute.call_args.args
        self.assertIn("WHERE race_id = %s", query)
        self.assertEqual(params, ("202610020301",))
        self.assertNotIn("favorite", query.lower())
        self.assertNotIn("memo", query.lower())
        connection.close.assert_called_once_with()

    def test_registered_race_card_includes_horse_history_in_actual_date_order(self):
        connection = MagicMock()
        connection.cursor.return_value.fetchall.side_effect = [
            [
                {
                    "race_id": "202610020301",
                    "race_date": date(2026, 7, 4),
                    "horse_number": 3,
                    "horse_id": "horse-1",
                    "horse_name": "テストホース",
                }
            ],
            [
                {
                    "horse_id": "horse-1",
                    "race_id": "older-race",
                    "tyakujun": 4,
                    "time": "1:35.0",
                    "jockey": "騎手A",
                    "weight": Decimal("56.0"),
                    "horse_weight": 480,
                    "corners": "3-3",
                    "second_half": Decimal("35.2"),
                },
                {
                    "horse_id": "horse-1",
                    "race_id": "newer-race",
                    "post": 8,
                    "popularity": 2,
                    "tyakujun": 1,
                    "time": "1:34.0",
                    "margin": "クビ",
                    "jockey": "騎手B",
                    "weight": Decimal("57.0"),
                    "horse_weight": 482,
                    "weight_change": 2,
                    "first_half": Decimal("35.1"),
                    "corners": "1-1",
                    "huri1": "出遅れ",
                    "corner1": "1",
                    "corner2": "1",
                    "corner3": "2",
                    "corner4": "3",
                    "corner_position": "内",
                    "second_half": Decimal("34.1"),
                    "time_index_total": 90,
                    "time_index_start": 80,
                    "time_index_run": 85,
                    "time_index_finish": 95,
                    "running_type": "瞬発型",
                    "ana04": "接触",
                },
            ],
            [
                {"race_id": "older-race", "race_date": date(2025, 5, 1)},
                {"race_id": "newer-race", "race_date": date(2025, 6, 1)},
            ],
            [
                {
                    "race_id": "older-race",
                    "place_num": "東京",
                    "race_name": "青葉賞",
                    "grade": "GII",
                    "track": "芝",
                    "distance": 2400,
                    "condition": "良",
                    "pace": "S",
                },
                {
                    "race_id": "newer-race",
                    "place_num": "東京",
                    "race_name": "日本ダービー",
                    "race_condition": "3歳",
                    "grade": "GI",
                    "tousu": 18,
                    "track": "芝",
                    "distance": 2400,
                    "condition": "良",
                    "bias": "内有利",
                    "ichinuke": "3",
                    "jitenn": "5",
                    "staus": "持続戦",
                    "pace": "M",
                },
            ],
        ]

        with patch("src.backend.server.get_connection", return_value=connection):
            result = get_registered_race_card("202610020301")

        runs = result["entries"][0]["previous_runs"]
        self.assertEqual(
            [run["race_date"] for run in runs],
            ["2025-06-01", "2025-05-01"],
        )
        self.assertEqual(runs[0]["race_name"], "日本ダービー")
        self.assertEqual(runs[0]["second_half"], 34.1)
        self.assertEqual(runs[0]["corner_position"], "内")
        self.assertEqual(runs[0]["time_index_total"], 90)
        self.assertEqual(runs[0]["race_condition"], "3歳")
        self.assertEqual(runs[0]["staus"], "持続戦")
        queries = [
            call.args[0]
            for call in connection.cursor.return_value.execute.call_args_list
        ]
        self.assertTrue(any("WHERE horse_id IN" in query for query in queries))
        self.assertTrue(any("FROM race_fetch_status" in query for query in queries))

    def test_registered_race_card_endpoint_rejects_invalid_race_id(self):
        with self.assertRaises(HTTPException) as error:
            get_registered_race_card("not-a-race-id")

        self.assertEqual(error.exception.status_code, 400)

    def test_single_race_endpoint_returns_registration_result(self):
        race_id = "202610010101"

        with (
            patch(
                "src.backend.server.fetch_and_register_race_card",
                return_value=16,
            ) as fetch_race_card,
            patch(
                "src.backend.server.fetch_netkeiba_previous_runs"
            ) as fetch_previous_runs,
        ):
            result = fetch_netkeiba_race_data(race_id)

        fetch_race_card.assert_called_once_with(race_id)
        fetch_previous_runs.assert_called_once_with(race_id)
        self.assertEqual(result["race_id"], race_id)
        self.assertEqual(result["entry_count"], 16)
        self.assertIn("当日出馬表 16 頭", result["message"])
        self.assertIn("前走記録", result["message"])

    def test_race_card_parser_extracts_entry_fields_without_favorites_or_memos(self):
        entries = extract_race_card_entries(RACE_CARD_HTML, "202610010101")

        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0],
            {
                "race_id": "202610010101",
                "race_date": "2026-10-01",
                "frame_number": 2,
                "horse_number": 3,
                "horse_id": "2024101234",
                "horse_name": "テストホース",
                "sex_age": "牡3",
                "carried_weight": 57.0,
                "jockey": "テスト騎手",
                "trainer_area": "美浦",
                "trainer": "テスト厩舎",
                "horse_weight": 480,
                "weight_change": 2,
                "win_odds": 4.5,
                "popularity": 2,
            },
        )
        self.assertFalse(
            {"favorite", "favorite_memo", "horse_memo"}
            & entries[0].keys()
        )

    def test_race_card_parser_rejects_html_for_a_different_race(self):
        with self.assertRaisesRegex(ValueError, "race_id"):
            extract_race_card_entries(RACE_CARD_HTML, "202610010102")

    def test_page_date_is_taken_from_verified_title_not_race_id_prefix(self):
        from src.netkeiba_fetcher.race_card import extract_race_date

        self.assertEqual(
            extract_race_date(NEWSPAPER_HTML, "202610020301"),
            "2026-07-04",
        )

    def test_page_date_rejects_a_different_canonical_race_id(self):
        from src.netkeiba_fetcher.race_card import extract_race_date

        with self.assertRaisesRegex(ValueError, "ページID"):
            extract_race_date(NEWSPAPER_HTML, "202610020302")

    def test_existing_dates_are_repaired_from_matching_newspaper_pages(self):
        with TemporaryDirectory() as temp_dir:
            newspaper_dir = Path(temp_dir)
            (newspaper_dir / "race_sp_newspaper_202610020301.html").write_text(
                NEWSPAPER_HTML,
                encoding="utf-8",
            )
            connection = MagicMock()
            cursor = connection.cursor.return_value
            cursor.fetchall.side_effect = [
                [{"race_id": "202610020301"}],
                [{"race_id": "202610020301"}],
            ]
            cursor.rowcount = 1

            with (
                patch(
                    "src.netkeiba_fetcher.race_date_repair.NEWSPAPER_DIR",
                    newspaper_dir,
                ),
                patch(
                    "src.netkeiba_fetcher.race_date_repair.get_connection",
                    return_value=connection,
                ),
            ):
                result = repair_race_dates_from_cached_newspapers()

        self.assertEqual(result["status_rows_updated"], 1)
        self.assertEqual(result["race_card_rows_updated"], 1)
        self.assertEqual(result["races_verified"], 1)
        self.assertEqual(result["skipped"], {})
        self.assertEqual(cursor.executemany.call_count, 2)
        for call_args in cursor.executemany.call_args_list:
            sql, params = call_args.args
            self.assertIn("SET race_date = %s", sql)
            self.assertEqual(params, [("2026-07-04", "202610020301", "2026-07-04")])
        connection.commit.assert_called_once_with()

    def test_race_card_registration_creates_table_and_upserts_rows(self):
        connection = MagicMock()
        entries = extract_race_card_entries(RACE_CARD_HTML, "202610010101")

        with patch(
            "src.netkeiba_fetcher.db_register.get_connection",
            return_value=connection,
        ):
            init_db(connection)
            count = register_race_card_entries(entries)

        executed_sql = "\n".join(
            call.args[0] for call in connection.cursor.return_value.execute.call_args_list
        )
        self.assertEqual(count, 1)
        self.assertIn("CREATE TABLE IF NOT EXISTS race_card_entries", executed_sql)
        self.assertNotIn("favorite", executed_sql.lower())
        self.assertNotIn("memo", executed_sql.lower())
        connection.cursor.return_value.execute.assert_any_call(
            "DELETE FROM race_card_entries WHERE race_id = %s",
            ("202610010101",),
        )
        connection.cursor.return_value.executemany.assert_called_once()
        self.assertIn(
            "INSERT INTO race_card_entries",
            connection.cursor.return_value.executemany.call_args.args[0],
        )
        self.assertEqual(connection.commit.call_count, 2)

    def test_race_card_fetch_uses_parser_and_registration(self):
        race_id = "202610010101"
        entries = extract_race_card_entries(RACE_CARD_HTML, race_id)

        with (
            patch("src.netkeiba_fetcher.api_entry.init_db") as init_db,
            patch(
                "src.netkeiba_fetcher.api_entry.get_race_card_text",
                return_value=RACE_CARD_HTML,
            ) as fetch_html,
            patch(
                "src.netkeiba_fetcher.api_entry.register_race_card_entries",
                return_value=1,
            ) as register_entries,
        ):
            count = fetch_and_register_race_card(race_id)

        fetch_html.assert_called_once_with(race_id)
        init_db.assert_called_once_with()
        register_entries.assert_called_once_with(entries)
        self.assertEqual(count, 1)

    def test_date_range_fetch_uses_shared_single_race_workflow(self):
        race_id = "202610010101"

        with (
            patch(
                "src.jra_fetcher.db_helper.get_race_days",
                return_value=["20261001"],
            ),
            patch("src.netkeiba_fetcher.api_entry.init_db"),
            patch(
                "src.netkeiba_fetcher.api_entry.get_race_ids_by_date",
                return_value=[race_id],
            ),
            patch(
                "src.netkeiba_fetcher.api_entry._fetch_previous_runs"
            ) as fetch_previous_runs,
        ):
            result = fetch_netkeiba_data_by_date_range(
                "2026-10-01",
                "2026-10-01",
            )

        self.assertEqual(result, [race_id])
        fetch_previous_runs.assert_called_once_with(race_id, "2026-10-01")


if __name__ == "__main__":
    unittest.main()
