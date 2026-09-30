import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.backend.server import get_table_data
from unittest.mock import Mock, patch

def test_api_endpoint():
    # テスト用のモックデータを設定
    mock_data = [
        {"id": 1, "name": "race_result_1"},
        {"id": 2, "name": "race_result_2"},
        {"id": 3, "name": "race_result_3"},
        {"id": 4, "name": "race_result_4"},
        {"id": 5, "name": "race_result_5"}
    ]

    # モックデータベース接続とカーソルを設定
    with patch('src.backend.server.get_connection') as mock_get_connection:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # テストデータを設定
        mock_cursor.fetchall.return_value = mock_data

        # カーソルのfetchoneメソッドがtotalを返すように設定
        mock_cursor.fetchone.return_value = {"total": 5}

        # APIエンドポイントを呼び出す
        result = get_table_data("horse_race_results", limit=100, offset=0)

        print("APIエンドポイント呼び出し結果:")
        print(f"データ件数: {len(result['data'])}")
        print(f"Totalフィールド: {result['pagination']['total']}")
        print(f"Limit: {result['pagination']['limit']}")
        print(f"Offset: {result['pagination']['offset']}")
        print(f"ページ: {result['pagination']['page']}")
        print(f"総ページ数: {result['pagination']['total_pages']}")

        # 結果の確認
        assert len(result['data']) == 5, "データ件数が正しいか確認"
        assert result['pagination']['total'] == 5, "Totalフィールドが正しいか確認"
        assert result['pagination']['limit'] == 100, "Limitパラメータが正しいか確認"
        assert result['pagination']['offset'] == 0, "Offsetパラメータが正しいか確認"
        assert result['pagination']['page'] == 1, "ページが正しいか確認"
        assert result['pagination']['total_pages'] == 1, "総ページ数が正しいか確認"

        print("テスト成功: APIエンドポイントは期待通りに動作しました。")

if __name__ == "__main__":
    test_api_endpoint()
