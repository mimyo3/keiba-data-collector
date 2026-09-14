# API 仕様書（計画版）

## 1. 概要

本ドキュメントは、競馬データ収集プロジェクトに対する API 仕様を定義する。  
現状のリポジトリには HTTP API サーバーは実装されておらず、実際のデータ収集・登録処理は MySQL への保存が中心である。  
そのため、本書の API は「将来の公開 API / 管理 API / data access API」として設計した仕様書として扱う。

- 基本 URL: `/api/v1`
- 形式: JSON
- 文字コード: UTF-8
- 認証: 未実装（現状は none）

---

## 2. 目的

API は次の用途を想定する。

- 収集済みのレース情報を検索する
- 1 レース単位で詳細を取得する
- 馬ごとの成績を照会する
- 収集状態を管理・確認する
- 収集ジョブの再実行状態を確認する

---

## 3. 実装状況の整理

現状のコードを見ると、以下のデータ保存処理が存在する。

- JRA HTML 収集と metadata 保存
- JRA race_days 抽出
- Netkeiba モジュールによるレース情報・馬成績抽出
- MySQL に `races`, `horse_race_results`, `race_fetch_status` を保存

しかし、これらは HTTP エンドポイントではなく、Python ベースのデータ取得処理として構成されている。  
したがって、本 API 仕様は、DB に蓄積したデータを外部から参照・管理するための公開設計として定義する。

---

## 4. 共通ルール

### 4.1 HTTP メソッド

- GET: 参照
- POST: 新規作成または登録
- PUT/PATCH: 更新
- DELETE: 削除（必要時）

### 4.2 レスポンス形式

成功時は JSON オブジェクトで返す。

```json
{
  "status": "success",
  "data": {},
  "message": "OK"
}
```

エラー時は次の形式とする。

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "race_id is invalid"
  }
}
```

### 4.3 ステータスコード

- 200: 成功
- 201: 作成成功
- 400: リクエスト不正
- 404: 対象無し
- 409: 重複
- 500: サーバー内部エラー

### 4.4 日付形式

- 日付: `YYYY-MM-DD`
- 年月: `YYYYMM`
- race_id: `YYYYMMDDxxxx`（12 桁前後）

---

## 5. 認証

現時点では未定義。  
将来的には以下の方式が候補となる。

- API Key
- JWT
- 管理者専用セッション認証

現状の設計では管理者向けの内部利用を想定し、公開 API には認証を必須としない方針も選択可能である。

---

## 6. エンドポイント一覧

## 6.1 ヘルスチェック

### GET /api/v1/health

API の稼働状態を確認する。

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "ok": true,
    "service": "keiba-api",
    "time": "2026-09-14T12:34:56Z"
  }
}
```

---

## 6.2 レース情報

### GET /api/v1/races

条件付きでレース情報一覧を返す。

#### Query パラメータ

| パラメータ | 型 | 必須 | 説明 |
|---|---|---:|---|
| race_id | string | No | レースID で絞り込み |
| date | string | No | `YYYY-MM-DD` 形式 |
| race_name | string | No | レース名で部分一致 |
| place_num | string | No | 開催地番号 |
| track | string | No | 馬場種別 |
| limit | integer | No | 最大件数（デフォルト 50） |
| offset | integer | No | 取得開始位置 |

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "race_id": "202406010101",
        "race_date": "2024-06-01",
        "race_name": "東京3R",
        "place_num": "1",
        "track": "芝",
        "distance": 1200,
        "condition": "良",
        "bias": "内",
        "rank": 3,
        "tousu": 16
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

---

### GET /api/v1/races/{race_id}

指定した race_id の詳細を取得する。

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "race_id": "202406010101",
    "race_date": "2024-06-01",
    "race_name": "東京3R",
    "place_num": "1",
    "track": "芝",
    "distance": 1200,
    "condition": "良",
    "bias": "内",
    "ichinuke": "1",
    "jitenn": "-",
    "pace": "4",
    "rank": 3,
    "tousu": 16
  }
}
```

#### 404 例

```json
{
  "status": "error",
  "error": {
    "code": "RACE_NOT_FOUND",
    "message": "race_id 202406010101 was not found"
  }
}
```

---

## 6.3 レース結果

### GET /api/v1/races/{race_id}/results

1 レースに紐づく競走馬の成績一覧を取得する。

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "race_id": "202406010101",
    "results": [
      {
        "id": 1,
        "horse_name": "サクラローレル",
        "jockey": "田中勝",
        "post": 1,
        "popularity": 2,
        "tyakujun": 1,
        "time": "1:09.8",
        "margin": "1.0",
        "weight": 480.0,
        "horse_weight": 470,
        "weight_change": 10,
        "first_half": "35.2",
        "second_half": "34.6"
      }
    ]
  }
}
```

---

## 6.4 馬別成績

### GET /api/v1/horses/{horse_name}/results

特定馬に紐づく過去成績を取得する。

#### Query パラメータ

| パラメータ | 型 | 説明 |
|---|---|---|
| limit | integer | 最大件数 |
| offset | integer | 取得開始位置 |

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "horse_name": "サクラローレル",
    "items": [
      {
        "race_id": "202406010101",
        "race_date": "2024-06-01",
        "race_name": "東京3R",
        "jockey": "田中勝",
        "time": "1:09.8",
        "popularity": 2
      }
    ],
    "total": 12
  }
}
```

---

## 6.5 一覧・検索系

### GET /api/v1/race-status

収集状態を確認する。

#### Query パラメータ

| パラメータ | 型 | 説明 |
|---|---|---|
| date | string | `YYYY-MM-DD` 形式 |
| registered | boolean | 登録済みか否か |
| parsed | boolean | 解析完了か否か |
| html_fetched | boolean | HTML取得済みか否か |

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "race_id": "202406010101",
        "race_date": "2024-06-01",
        "html_fetched": true,
        "parsed": true,
        "registered": true,
        "error_message": null,
        "updated_at": "2026-09-14T12:00:00Z"
      }
    ]
  }
}
```

---

### POST /api/v1/race-status

収集状態を新規作成または更新する。

#### リクエスト例

```json
{
  "race_id": "202406010101",
  "race_date": "2024-06-01",
  "html_fetched": true,
  "parsed": true,
  "registered": false
}
```

#### レスポンス例

```json
{
  "status": "success",
  "data": {
    "race_id": "202406010101",
    "updated": true
  }
}
```

---

## 7. データモデル

## 7.1 Race

```json
{
  "race_id": "string",
  "race_date": "YYYY-MM-DD",
  "race_name": "string",
  "place_num": "string",
  "rank": "integer|null",
  "tousu": "integer|null",
  "track": "string|null",
  "distance": "integer|null",
  "condition": "string|null",
  "bias": "string|null",
  "ichinuke": "string|null",
  "jitenn": "string|null",
  "staus": "string|null",
  "pace": "string|null"
}
```

## 7.2 HorseRaceResult

```json
{
  "id": "integer",
  "race_id": "string",
  "horse_name": "string",
  "jockey": "string|null",
  "post": "integer|null",
  "popularity": "integer|null",
  "tyakujun": "integer|null",
  "time": "string|null",
  "margin": "string|null",
  "weight": "number|null",
  "horse_weight": "integer|null",
  "weight_change": "integer|null",
  "first_half": "number|null",
  "second_half": "number|null",
  "corners": "string|null",
  "running_type": "string|null"
}
```

## 7.3 RaceFetchStatus

```json
{
  "id": "integer",
  "race_id": "string",
  "race_date": "YYYY-MM-DD",
  "html_fetched": "boolean",
  "parsed": "boolean",
  "registered": "boolean",
  "error_message": "string|null",
  "updated_at": "ISO-8601 datetime"
}
```

---

## 8. エラーレスポンス一覧

| code | 説明 |
|---|---|
| INVALID_PARAMETER | 必須パラメータが不足または不正 |
| RACE_NOT_FOUND | 対象レースが存在しない |
| HORSE_NOT_FOUND | 対象馬が存在しない |
| DB_ERROR | DB 接続またはクエリ失敗 |
| PARSE_ERROR | HTML 解析失敗 |
| NOT_IMPLEMENTED | 実装未完了の API |

---

## 9. 将来拡張案

- `/api/v1/summary` で日次レースサマリーを返す
- `/api/v1/analytics` で馬別・条件別の統計を返す
- `/api/v1/jobs` で収集ジョブの状態管理を行う
- `/api/v1/races/export` で CSV / JSON 形式でのエクスポートを行う

---

## 10. まとめ

本 API は、`races`、`horse_race_results`、`race_fetch_status` を中心に、競馬データの検索・照会・状態確認を行うための基盤として設計される。  
現在のコードベースでは HTTP API は未実装であるが、データベース上の集約情報を活用して将来的に利用可能な API として整理した仕様である。
