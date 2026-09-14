#!/usr/bin/env python3
import os
"""
Configuration module for JRA fetcher.
"""

# HTTP設定
HTTP_REQUEST_INTERVAL = 2.0  # 秒
HTTP_TIMEOUT = 10          # 秒
HTTP_MAX_RETRIES = 3         # 最大リトライ回数
HTTP_RETRY_DELAY = 1.0         # リトライ間隔（秒）

# JRAサイト設定
JRA_BASE_URL = "https://www.jra.go.jp"

# データ保存設定
PROJECT_ROOT = os.path.dirname(
	os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "jra", "html")
FIXTURE_DIR = "tests/fixtures"

# ログ設定
LOG_LEVEL = "INFO"