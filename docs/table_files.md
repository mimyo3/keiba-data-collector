# テーブル表示に関係するファイル

## ファイル一覧

1. **`src/backend/server.py`** - テーブル一覧の定義とAPIエンドポイントの実装
2. **`src/jra_fetcher/race_day_workflow.py`** - テーブル更新機能の実装

## テーブル一覧

- horse_race_results
- html_saves
- jra_html_metadata
- race_days
- race_fetch_status
- races

## APIエンドポイント

- `/api/db/{table_name}` - 指定テーブルのデータを取得
