#!/bin/bash
# サーバー起動スクリプト
set -euo pipefail

cd "$(dirname "$0")"

# 環境変数を正しく読み込むために、.envファイルをsourceしてから起動
set -a
. .env
set +a

if (echo >/dev/tcp/127.0.0.1/8001) 2>/dev/null; then
	echo "8001番ポートはすでに使用中です。既存のサーバーを確認してください。" >&2
	exit 1
fi

# バックグラウンドで起動し、ログをファイルに吐かせて即座に終了
nohup python -m uvicorn src.backend.server:app --host 0.0.0.0 --port 8001 > uvicorn.log 2>&1 </dev/null &
server_pid=$!

sleep 1
if ! kill -0 "$server_pid" 2>/dev/null; then
	echo "サーバーの起動に失敗しました。uvicorn.logを確認してください。" >&2
	exit 1
fi

echo "サーバーを起動しました。PID: $server_pid"
