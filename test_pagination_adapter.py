"""Test file for pagination adapter."""

import unittest
from unittest.mock import patch, MagicMock
from src.backend.paging_adapter import PagingAdapter, _wrap_api_call


class TestPagingAdapter(unittest.TestCase):
    """Test cases for the PagingAdapter class."""

    def test_wrap_api_call_with_response(self):
        """Test _wrap_api_call with a Response object."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.content = b'[{"id": 1, "name": "test"}]'
        mock_response.headers = {"X-Total-Rows": "10"}
        
        # Mock the get_table_rows function
        with patch('src.backend.paging_adapter.get_table_rows', return_value=mock_response):
            result = _wrap_api_call("test_table", page=1, limit=100)
            
            self.assertEqual(result["rows"], [{"id": 1, "name": "test"}])
            self.assertEqual(result["page"], 1)
            self.assertEqual(result["limit"], 100)
            self.assertEqual(result["total"], 10)
            self.assertEqual(result["total_pages"], 1)

    def test_wrap_api_call_with_dict(self):
        """Test _wrap_api_call with a dict (fallback case)."""
        # Mock the get_table_rows function to return a dict directly
        mock_result = [{"id": 1, "name": "test"}]
        
        with patch('src.backend.paging_adapter.get_table_rows', return_value=mock_result):
            result = _wrap_api_call("test_table", page=1, limit=100)
            
            self.assertEqual(result["rows"], [{"id": 1, "name": "test"}])
            self.assertEqual(result["page"], 1)
            self.assertEqual(result["limit"], 100)
            self.assertEqual(result["total"], 10)
            self.assertEqual(result["total_pages"], 1)

    def test_paging_adapter_initialization(self):
        """Test PagingAdapter initialization."""
        adapter = PagingAdapter()
        self.assertIsNotNone(adapter.api_client)

    def test_get_table_rows(self):
        """Test get_table_rows method."""
        # Create a mock response
        mock_response = MagicMock()
        mock_response.content = b'[{"id": 1, "name": "test"}]'
        mock_response.headers = {"X-Total-Rows": "10"}
        
        # Mock the get_table_rows function
        with patch('src.backend.paging_adapter.get_table_rows', return_value=mock_response):
            adapter = PagingAdapter()
            result = adapter.get_table_rows("test_table", page=1, limit=100)
            
            self.assertEqual(result["rows"], [{"id": 1, "name": "test"}])
            self.assertEqual(result["page"], 1)
            self.assertEqual(result["limit"], 100)
            self.assertEqual(result["total"], 10)


if __name__ == '__main__':
    unittest.main()
