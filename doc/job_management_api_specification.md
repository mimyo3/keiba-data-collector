# 収集ジョブ用管理 API 仕様書

## 1. 概要

この仕様書は、競馬データ収集ジョブを管理・制御するための API を定義する。  
現状コードでは収集処理は Python 関数として実装されており、`JRA` の月次 HTML 取得や `Netkeiba` の過去成績解析を DB に登録するフローが実体化されている。

本 API は、これらの処理を外部から起動・監視・再試行するための管理 API として設計する。

- 基本 URL: `/api/v1/jobs`
- 形式: JSON
- 認証: 未実装（管理者用前提）
- 目的: 収集ジョブの開始、進捗確認、再実行、失敗追跡

---

## 2. 目的

管理 API は次の機能を提供する。

- JRA 収集ジョブの起動
- Netkeiba 収集ジョブの起動
- 収集状態の取得
- 失敗したジョブの再実行
- ジョブの進捗とエラー内容の確認

---

## 3. 現状コードとの対応

### 3.1 JRA 関連ジョブ

`src/jra_fetcher/workflow.py` に `run_jra_workflow(start_month, end_month)` があり、以下を順番に実行する。

1. `fetch_jra_html_workflow(start_month, end_month)`
2. 月次ごとの `update_race_days_table(target_month)`

これは「月範囲の HTML 収集 → 開催日抽出」をまとめたジョブである。

### 3.2 Netkeiba 関連ジョブ

`src/netkeiba_fetcher/db_register.py` の以下関数がジョブの状態管理に対応している。

- `register_race_fetch_status(...)`
- `update_race_fetch_status(...)`

この状態管理により、各 race_id の `html_fetched`, `parsed`, `registered` を追跡できる。

---

## 4. 共通ルール

### 4.1 HTTP メソッド

- POST: ジョブの開始
- GET: ジョブ/状態の確認
- PATCH: ジョブ状態の更新
- DELETE: 中止または削除（任意）

### 4.2 返却形式

成功時:

```json
{
  "status": "success",
  "data": {},
  "message": "OK"
}
```

失敗時:

```json
{
  "status": "error",
  "error": {
    "code": "JOB_INVALID_STATE",
    "message": "Job cannot be restarted while running"
  }
}
```

### 4.3 ステータスコード

- 200: 成功
- 201: ジョブ開始成功
- 202: ジョブ受付済み
- 400: パラメータ不正
- 404: ジョブ未存在
- 409: 実行中または状態衝突
- 500: サーバーエラー

---

## 5. ジョブ定義

### 5.1 ジョブ種別一覧

| job_type | 内容 | 対応ソース |
|---|---|---|
| jra_month_fetch | JRA の期間別 HTML 取得 | `src/jra_fetcher/workflow.py` |
| jra_race_day_extract | JRA の開催日抽出 | `src/jra_fetcher/race_day_workflow.py` |
| netkeiba_prev_run_fetch | Netkeiba の過去成績取得 | `src/netkeiba_fetcher/netkeiba_prevrun_fetch.py` |
| netkeiba_register | Netkeiba データの DB 登録 | `src/netkeiba_fetcher/db_register.py` |

### 5.2 ジョブ状態

| status | 説明 |
|---|---|
| queued | キュー待ち |
| running | 実行中 |
| success | 正常終了 |
| failed | 失敗 |
| cancelled | キャンセル |
| partial | 部分成功 |

---

## 6. エンドポイント一覧

## 6.1 ジョブ起動

### POST /api/v1/jobs

ジョブを新規作成し、実行を要求する。

#### リクエスト例

```json
{
  "job_type": "jra_month_fetch",
  "params": {
    "start_month": "202406",
    "end_month": "202401"
  },
  "priority": 10
}
```

#### 返却例

```json
{
  "status": "success",
  "data": {
    "job_id": "job_20260914_001",
    "job_type": "jra_month_fetch",
    "status": "queued"
  }
}
```

#### バリデーション

- `job_type` は定義済みの種類であること
- `start_month` / `end_month` は `YYYYMM` 形式であること
- `start_month` は `end_month` 以上の古い月を指定しないこと

---

## 6.2 ジョブ一覧

### GET /api/v1/jobs

ジョブ一覧を取得する。

#### Query パラメータ

| パラメータ | 型 | 説明 |
|---|---|---|
| job_type | string | ジョブ種別で絞り込み |
| status | string | 実行状態で絞り込み |
| limit | integer | 取得件数上限 |
| offset | integer | 取得開始位置 |

#### 返却例

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "job_id": "job_20260914_001",
        "job_type": "jra_month_fetch",
        "status": "success",
        "created_at": "2026-09-14T12:00:00Z",
        "updated_at": "2026-09-14T12:05:00Z"
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

---

## 6.3 ジョブ詳細

### GET /api/v1/jobs/{job_id}

ジョブの詳細と実行情報を取得する。

#### 返却例

```json
{
  "status": "success",
  "data": {
    "job_id": "job_20260914_001",
    "job_type": "jra_month_fetch",
    "status": "running",
    "params": {
      "start_month": "202406",
      "end_month": "202401"
    },
    "progress": {
      "current": "202404",
      "total": 6,
      "percent": 66
    },
    "created_at": "2026-09-14T12:00:00Z",
    "updated_at": "2026-09-14T12:04:00Z",
    "started_at": "2026-09-14T12:01:00Z",
    "finished_at": null,
    "error_message": null
  }
}
```

---

## 6.4 ジョブ停止

### POST /api/v1/jobs/{job_id}/cancel

実行中ジョブを停止する要求を行う。

#### 返却例

```json
{
  "status": "success",
  "data": {
    "job_id": "job_20260914_001",
    "status": "cancelled"
  }
}
```

#### 失敗時

```json
{
  "status": "error",
  "error": {
    "code": "JOB_NOT_RUNNING",
    "message": "This job is not in a cancellable state"
  }
}
```

---

## 6.5 ジョブ再実行

### POST /api/v1/jobs/{job_id}/retry

失敗したジョブを再実行する。

#### リクエスト例

```json
{
  "force": true
}
```

#### 返却例

```json
{
  "status": "success",
  "data": {
    "job_id": "job_20260914_001",
    "new_job_id": "job_20260914_002",
    "status": "queued"
  }
}
```

#### ルール

- `status` が `failed` または `partial` の場合のみ再実行可能
- 実行中ジョブに対する再実行は `409` を返す

---

## 6.6 収集状態更新

### PATCH /api/v1/jobs/{job_id}/status

外部ジョブから進捗状況を更新する。

#### リクエスト例

```json
{
  "status": "running",
  "progress": {
    "current": "202404",
    "total": 6,
    "percent": 66
  },
  "error_message": null
}
```

#### 返却例

```json
{
  "status": "success",
  "data": {
    "job_id": "job_20260914_001",
    "updated": true
  }
}
```

---

## 7. ジョブモデル

```json
{
  "job_id": "string",
  "job_type": "jra_month_fetch|jra_race_day_extract|netkeiba_prev_run_fetch|netkeiba_register",
  "status": "queued|running|success|failed|cancelled|partial",
  "params": "object",
  "progress": {
    "current": "string|integer|null",
    "total": "string|integer|null",
    "percent": "integer|null"
  },
  "created_at": "ISO-8601 datetime",
  "updated_at": "ISO-8601 datetime",
  "started_at": "ISO-8601 datetime|null",
  "finished_at": "ISO-8601 datetime|null",
  "error_message": "string|null"
}
```

---

## 8. 収集状態との対応

`race_fetch_status` には以下の boolean が存在する。

- `html_fetched`
- `parsed`
- `registered`

管理 API では、この状態をジョブの細部進捗と対応させる。

| ジョブ状態 | DB状態 |
|---|---|
| queued | なし |
| running | 取得処理中 |
| success | html_fetched=TRUE, parsed=TRUE, registered=TRUE |
| failed | error_message に詳細を保存 |
| partial | 一部のレコードだけが完了 |

---

## 9. エラーコード一覧

| code | 説明 |
|---|---|
| JOB_NOT_FOUND | ジョブが存在しない |
| JOB_INVALID_STATE | 状態遷移が不正 |
| JOB_INVALID_PARAM | 必須パラメータ不正 |
| JOB_NOT_RUNNING | 停止可能な状態ではない |
| JOB_RETRY_FORBIDDEN | 再実行不可 |
| DB_ERROR | ジョブ保存または状態更新失敗 |

---

## 10. 拡張方針

- ジョブの永続化は DB テーブルへ移行する
- Job executor により非同期実行へ拡張する
- `queue` / `scheduler` を導入して定期収集を管理する
- ジョブごとのログ保存と監視データの収集を追加する

---

## 11. まとめ

本 API は、収集ジョブの起動・状態確認・停止・再試行を制御するための管理層として設計する。  
`run_jra_workflow` や `register_race_fetch_status` に対応するジョブ制御を、HTTP API 経由で管理できるようにし、収集の制御性と再試行性を高めることを目的とする。
