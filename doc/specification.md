# 競馬データ収集・登録システム 仕様書

## 1. 目的

本プロジェクトは、JRA および Netkeiba の競馬関連HTMLを収集し、必要な情報を抽出・正規化して MySQL に保存することを目的とする。  
主な目的は、過去レース結果、開催日、レース基本情報、馬券データの再利用可能な基盤を構築することである。

---

## 2. 対象範囲

### 2.1 対象データ
- JRA の月次レース結果ページ HTML
- JRA の当月・前月遷移リンクと検索パラメータ
- JRA の開催日一覧
- Netkeiba の過去成績（PastBox）HTML
- Netkeiba のレース情報と競走馬別結果情報

### 2.2 対象外
- UI や Web API の提供
- 一般ユーザー向けのフロントエンド
- 収集対象の自動更新スケジューラ
- 直接の分析処理（予測・評価）は別モジュールとして管理

---

## 3. システム概要

本システムは、取得層・解析層・保存層の3層構成で設計されている。

1. 取得層
   - JRA から HTML を取得する
   - Netkeiba の過去成績 HTML を取得する
2. 解析層
   - HTML からレース日・レースID・馬情報を抽出する
   - 正規表現と DOM 解析を用いて必要フィールドを抽出する
3. 保存層
   - MySQL に metadata / race / result / status を保存する

---

## 4. 主要モジュール一覧

### 4.1 JRA 取得関連
- `src/jra_fetcher/config.py`
  - 収集対象のベースパスや保存先ディレクトリを定義する
- `src/jra_fetcher/http/common_http.py`
  - HTTP クライアントの共通処理を定義する
- `src/jra_fetcher/month_fetcher.py`
  - 月単位の HTML 取得、前月リンク追跡、範囲取得を実行する
- `src/jra_fetcher/html_page.py`
  - HTML ファイルの保存・再利用・メタデータ検索を行う
- `src/jra_fetcher/html_parser.py`
  - JRA HTML に含まれるリンクやレース日情報を抽出する
- `src/jra_fetcher/html_store.py`
  - ローカル保存用の HTML ストアを管理する
- `src/jra_fetcher/db_helper.py`
  - JRA 用メタデータと開催日データの DB 永続化を担当する
- `src/jra_fetcher/race_day_workflow.py`
  - 保存済み HTML から race_days を抽出し登録する
- `src/jra_fetcher/workflow.py`
  - JRA の一連の取得から登録までの上位フローを定義する

### 4.2 Netkeiba 取得関連
- `src/netkeiba_fetcher/db_schema.py`
  - races / horse_race_results / race_fetch_status のテーブル定義
- `src/netkeiba_fetcher/db_register.py`
  - DB 初期化、race status 更新、past run などの登録処理を実装する
- `src/netkeiba_fetcher/netkeiba_prevrun_fetch.py`
  - Netkeiba の過去成績HTMLからレース/馬の結果を抽出する

### 4.3 共通基盤
- `src/backend/db_config.py`
  - MySQL 接続設定を環境変数から読み込み、接続情報を生成する
- `src/helpers/db_helper.py`
  - 共通 DB 補助処理を提供する
- `src/helpers/http_client.py`
  - HTTP セッションや共通リクエスト設定を提供する

---

## 5. 主要処理フロー

### 5.1 JRA の HTML 取得フロー

1. 取得対象の年月範囲を `start_month` / `end_month` で受け取る
2. `fetch_jra_html_workflow` が現在月のメタデータ存在を確認する
3. 既存データがあれば不足分のみ取得する
4. JRA のトップページから「レース結果」→「過去レース結果検索」へのリンクを抽出する
5. `fetch_month_range` で月ごとに前月リンクを辿りながら HTML を取得する
6. 取得した HTML はローカル保存され、 `jra_html_metadata` に保存される
7. 必要に応じて `update_race_days_table` により race_days の抽出・格納を実行する

#### 経路
- `src/jra_fetcher/workflow.py` → `fetch_jra_html_workflow` → `build_missing_month_ranges` / `fetch_month_range` → `fetch_month` → `save_jra_html_metadata`

### 5.2 JRA の開催日登録フロー

- `extract_race_days` により月別 HTML 内の開催日一覧を抽出する
- 抽出結果を `save_race_day` で DB に格納する
- `race_days` テーブルには各開催日の年月日と関連する月情報が保存される

### 5.3 Netkeiba の過去成績取得フロー

1. `netkeiba_prevrun_fetch.py` が HTML を読込む
2. レースIDやレース名、距離、開催場所などを抽出する
3. 馬毎の結果データを整形し、`races` と `horse_race_results` へ分離して登録する
4. `race_fetch_status` で HTML 取得・解析・登録の状態を管理する

---

## 6. データモデル

### 6.1 JRA 連携テーブル

#### `jra_html_metadata`
| カラム | 型 | 内容 |
|---|---|---|
| id | INTEGER | 主キー |
| year_month | VARCHAR(8) | 対象年月（例: 202401） |
| prev_month_url | VARCHAR(30) | 前月リンク情報 |
| cname | VARCHAR(30) | JRA の検索パラメータ |
| file_name | VARCHAR(500) | 保存ファイル名 |
| created_at | TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | 更新日時 |

#### `race_days`
- `race_day_workflow` で生成される開催日データを格納する
- 主要項目は日付、レース開催情報、状態管理に関連する情報を含む想定

### 6.2 Netkeiba 連携テーブル

#### `races`
- レース共通情報を保存するテーブル
- 主キー: `race_id`
- 例: race_id, race_name, place_num, track, distance, condition, bias など

#### `horse_race_results`
- 各馬の成績を保存する詳細テーブル
- 主キー: id
- 例: race_id, horse_name, jockey, post, popularity, time, weight など

#### `race_fetch_status`
| カラム | 型 | 内容 |
|---|---|---|
| id | INTEGER | 主キー |
| race_id | VARCHAR(12) | 一意のレースID |
| race_date | DATE | 実施日 |
| html_fetched | BOOLEAN | HTML取得状態 |
| parsed | BOOLEAN | 解析完了状態 |
| registered | BOOLEAN | 登録完了状態 |
| error_message | TEXT | エラー内容 |
| updated_at | DATETIME | 更新日時 |

### 6.3 付随テーブル
- `kaishi_dates`
  - 開始日一覧を管理する
- `html_saves`
  - 保存元URL、保存先パス、HTML本体を記録する

---

## 7. 入出力インターフェース

### 7.1 JRA の入力
- `start_month` : 取得開始年月（例: `202401`）
- `end_month` : 取得終了年月（例: `202301`）
- `base_url` : JRA ベースURL

### 7.2 JRA の出力
- `data/jra/html/` 配下への HTML ファイル保存
- DB への metadata と開催日情報保存

### 7.3 Netkeiba の入力
- HTML を解析対象として読み込む
- 収集元URLや race ID を元に処理する

### 7.4 Netkeiba の出力
- `races` テーブルへのレース情報登録
- `horse_race_results` テーブルへの成績登録
- `race_fetch_status` への状態追跡

---

## 8. ルールと制約

### 8.1 日付/年月ルール
- JRA では月指定は `YYYYMM` 形式を前提とする
- `workflow.py` では `_validate_month` が `YYYYMM` と月範囲 1-12 を検証する
- `start_month` は `end_month` 以上の古い月を示す必要があり、範囲が逆転している場合はエラーとする

### 8.2 文字コード
- JRA ページは `shift_jis` を前提として読み込む
- 文字化け対策として `errors="replace"` で安全にデコードする

### 8.3 取得制御
- 既に保存済みの HTML が存在し、不要に再取得しないよう `force_fetch` と `cache` 判定を行う
- 月ごとの不足分だけを再取得する設計を持つ

### 8.4 DB 接続
- 接続情報は `src/backend/db_config.py` の `MYSQL_CONFIG` に集約される
- MySQL の環境変数 `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` を用いる

---

## 9. 例外・エラー処理

- 取得リンクが見つからない場合: `ValueError` を送出
- 月指定が不正な場合: `ValueError` を送出
- race ID が不正な場合: `_race_date_from_id` でバリデーションエラー
- 解析失敗時: `race_fetch_status.error_message` に記録する設計がある

---

## 10. 非機能要件

### 10.1 可用性
- 取得対象が DB に登録されていない場合でも、現在月基準の取得で対象の HTML を取得可能
- DB が利用できない状況でもローカルの HTML 保存を前提に動作可能な設計がある

### 10.2 保守性
- HTML 取得処理、抽出処理、DB 登録処理がモジュールごとに分離されている
- SQL 定義は `db_schema.py` に集中しており、テーブル定義の変更が容易

### 10.3 拡張性
- 新たな競馬サイトの追加や、異なるページ種別の抽出を行うために、別 fetcher / parser を追加しやすい
- `race_fetch_status` により収集状態の追跡と再実行の制御が可能

---

## 11. 制作上の留意点

- JRA と Netkeiba では HTML 構造が大きく異なるため、それぞれ独立した parser を持つべきである
- `race_id` の形式は `YYYYMMDD` + 連番 4 桁程度の形式を前提として扱うため、データ整合性に注意する
- 本システムはデータ収集と保存を主目的としており、分析モデルや API 提供は別責務として分離する設計が望ましい

---

## 12. 今後の改善候補

1. 定期実行ジョブの導入（cron / GitHub Actions / Airflow 等）
2. 収集結果ログの整備と監視の強化
3. Netkeiba / JRA のスクレイピング対象のバージョン差異への吸収
4. `races` / `horse_race_results` の整合性チェック処理の追加
5. API 層の実装（JSON 返却・検索機能）

---

## 13. 結論

本プロジェクトは、競馬データの取得・解析・保存を自動化する仕組みとして構成されている。  
JRA の月次 HTML 収集と Netkeiba の過去成績解析を組み合わせることで、レース日・レース情報・馬成績をデータベースに蓄積し、後続の分析や利用に利用可能な形で整備することを目的としている。
