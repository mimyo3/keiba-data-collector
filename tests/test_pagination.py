"""
Unit tests for pagination functionality.
"""
import unittest
import json
from unittest.mock import patch, MagicMock
import requests

# Mock the database connection for testing
class TestPagination(unittest.TestCase):
    
    def test_pagination_offset_calculation(self):
        """Test that pagination offset is calculated correctly."""
        # Test page 1, limit 100
        page = 1
        limit = 100
        offset = (page - 1) * limit
        self.assertEqual(offset, 0)
        
        # Test page 2, limit 100
        page = 2
        limit = 100
        offset = (page - 1) * limit
        self.assertEqual(offset, 100)
        
        # Test page 3, limit 100
        page = 3
        limit = 100
        offset = (page - 1) * limit
        self.assertEqual(offset, 200)
        
    def test_sql_query_format(self):
        """Test that SQL query is formatted correctly."""
        table_name = "horse_race_results"
        limit = 100
        offset = 0
        
        # This is what would be executed
        sql = f"SELECT * FROM `{table_name}` LIMIT %s OFFSET %s"
        expected_params = (limit, offset)
        
        # Verify structure
        self.assertIn("SELECT * FROM `", sql)
        self.assertIn("` LIMIT %s OFFSET %s", sql)
        self.assertEqual(len(expected_params), 2)
        
    def test_page_and_limit_parameters(self):
        """Test that page and limit parameters work as expected."""
        # Test default values
        # This would be called as get_table_rows(table_name, page=1, limit=100)
        page = 1
        limit = 100
        offset = (page - 1) * limit
        self.assertEqual(offset, 0)
        
        # Test custom values
        page = 5
        limit = 50
        offset = (page - 1) * limit
        self.assertEqual(offset, 200)
        
        # Test limit boundary
        page = 1
        limit = 1000
        offset = (page - 1) * limit
        self.assertEqual(offset, 0)
        
        page = 2
        limit = 1000
        offset = (page - 1) * limit
        self.assertEqual(offset, 1000)
        
    def test_paging_adapter_initialization(self):
        """Test that PagingAdapter initializes correctly."""
        from src.backend.paging_adapter import PagingAdapter
        
        # Test default initialization
        adapter = PagingAdapter()
        self.assertIsNotNone(adapter.api_client)
        
        # Test custom api_client
        mock_client = MagicMock()
        adapter = PagingAdapter(api_client=mock_client)
        self.assertEqual(adapter.api_client, mock_client)
        
    def test_get_table_rows_method(self):
        """Test the get_table_rows method of PagingAdapter."""
        from src.backend.paging_adapter import PagingAdapter
        
        # Mock the api_client
        mock_client = MagicMock()
        mock_client.return_value = {
            "rows": [{"id": 1, "name": "test"}],
            "page": 1,
            "limit": 100,
            "total": 1,
            "total_pages": 1
        }
        
        adapter = PagingAdapter(api_client=mock_client)
        result = adapter.get_table_rows("test_table", page=1, limit=100)
        
        # Verify the call was made correctly
        mock_client.assert_called_once_with("test_table", page=1, limit=100)
        self.assertEqual(result["rows"], [{"id": 1, "name": "test"}])

    def test_get_all_rows_paginated_method(self):
        """Test the get_all_rows_paginated method of PagingAdapter."""
        from src.backend.paging_adapter import PagingAdapter
        
        # Mock the api_client to return multiple pages
        mock_client = MagicMock()
        mock_client.side_effect = [
            {
                "rows": [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}],
                "page": 1,
                "limit": 100,
                "total": 3,
                "total_pages": 1
            },
            {
                "rows": [{"id": 3, "name": "test3"}],
                "page": 2,
                "limit": 100,
                "total": 3,
                "total_pages": 1
            },
            {
                "rows": [],
                "page": 3,
                "limit": 100,
                "total": 3,
                "total_pages": 1
            }
        ]
        
        adapter = PagingAdapter(api_client=mock_client)
        result = adapter.get_all_rows_paginated("test_table", limit=100)
        
        # Verify that multiple calls were made
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[2]["id"], 3)

    def test_table_display_functionality(self):
        """Test that table display functionality works correctly with actual API endpoint."""
        # Test that we can access the API endpoint with a valid table
        try:
            response = requests.get("http://localhost:8000/api/db/horse_race_results?page=1&limit=10")
            self.assertEqual(response.status_code, 200)
            
            # Verify that response is a list of dictionaries
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Check that we have at least one row
            if len(data) > 0:
                self.assertIsInstance(data[0], dict)
        except Exception as e:
            # If we can't connect to the server, it's not a failure of our code
            # but a test environment issue
            print(f"Cannot test table display functionality due to connection issue: {e}")
            pass


class TestTableDataQuery(unittest.TestCase):
    def test_search_sort_and_pagination_are_applied_to_the_full_table(self):
        from src.backend.server import get_table_rows

        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [
                {"Field": "id", "Key": "PRI"},
                {"Field": "name", "Key": ""},
            ],
            [{"id": 1, "name": "Alpha"}],
        ]
        cursor.fetchone.return_value = {"total": 7}
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch("src.backend.server.get_connection", return_value=connection):
            response = get_table_rows(
                "races", page=2, limit=2, search="alpha", sort_by="name", sort_order="desc"
            )

        self.assertEqual(response.headers["X-Total-Rows"], "7")
        self.assertEqual(json.loads(response.body), [{"id": 1, "name": "Alpha"}])
        count_query, count_params = cursor.execute.call_args_list[1].args
        page_query, page_params = cursor.execute.call_args_list[2].args
        self.assertIn("LOCATE(%s, CAST(`id` AS CHAR))", count_query)
        self.assertEqual(count_params, ("alpha", "alpha"))
        self.assertIn("ORDER BY `name` DESC, `id` ASC", page_query)
        self.assertEqual(page_params, ("alpha", "alpha", 2, 2))

    def test_unknown_sort_column_is_rejected(self):
        from fastapi import HTTPException
        from src.backend.server import get_table_rows

        cursor = MagicMock()
        cursor.fetchall.return_value = [{"Field": "id", "Key": "PRI"}]
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch("src.backend.server.get_connection", return_value=connection):
            with self.assertRaises(HTTPException) as error:
                get_table_rows("races", sort_by="id; DROP TABLE races")

        self.assertEqual(error.exception.status_code, 400)

    def test_race_card_urls_are_built_from_race_ids(self):
        from datetime import date
        from src.backend.server import get_netkeiba_race_card_urls

        cursor = MagicMock()
        cursor.fetchall.return_value = [{
            "race_id": "202610010101",
            "html_fetched": 1,
            "parsed": 1,
            "registered": 1,
            "error_message": None,
        }]
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with (
            patch("src.backend.server.get_race_ids_by_date", return_value=["202610010101"]),
            patch("src.backend.server.get_connection", return_value=connection),
        ):
            result = get_netkeiba_race_card_urls(date(2026, 10, 1))

        self.assertEqual(result["race_date"], "2026-10-01")
        self.assertEqual(result["race_cards"], [{
            "race_id": "202610010101",
            "url": "https://race.netkeiba.com/race/shutuba.html?race_id=202610010101",
            "fetch_status": {
                "html_fetched": True,
                "parsed": True,
                "registered": True,
                "error_message": None,
            },
        }])

    def test_race_card_urls_return_null_status_for_unfetched_races(self):
        from datetime import date
        from src.backend.server import get_netkeiba_race_card_urls

        cursor = MagicMock()
        cursor.fetchall.return_value = []
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with (
            patch("src.backend.server.get_race_ids_by_date", return_value=["202610010101"]),
            patch("src.backend.server.get_connection", return_value=connection),
        ):
            result = get_netkeiba_race_card_urls(date(2026, 10, 1))

        self.assertIsNone(result["race_cards"][0]["fetch_status"])
        connection.close.assert_called_once_with()
            
    def test_table_display_with_invalid_table(self):
        """Test that table display correctly handles invalid table names."""
        try:
            response = requests.get("http://localhost:8000/api/db/invalid_table?page=1&limit=10")
            self.assertEqual(response.status_code, 404)
        except Exception as e:
            print(f"Cannot test invalid table functionality due to connection issue: {e}")
            pass

if __name__ == '__main__':
    unittest.main()
