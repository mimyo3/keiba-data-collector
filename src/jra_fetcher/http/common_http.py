#!/usr/bin/env python3
"""
Common HTTP handling module for JRA access with rate limiting and monitoring.
"""

import time
import requests
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import json

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HttpRequestInfo:
    """HTTPリクエスト情報"""
    timestamp: datetime
    method: str
    url: str
    status_code: Optional[int] = None
    response_size: int = 0
    wait_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

class JRAHttpClient:
    """JRA用の共通HTTPクライアント"""
    
    def __init__(self, 
                 request_interval: float = 2.0,
                 timeout: int = 10,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        初期化
        
        Parameters
        ----------
        request_interval : float
            リクエスト間隔（秒）
        timeout : int
            タイムアウト時間（秒）
        max_retries : int
            最大リトライ回数
        retry_delay : float
            リトライ間隔（秒）
        """
        self.request_interval = request_interval
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 通信履歴を保持
        self.request_history: list[HttpRequestInfo] = []
        
        # 最後のリクエスト時刻
        self.last_request_time: Optional[datetime] = None
        
        # リクエスト間隔制御用のロック
        self._request_lock = False
        
    def _wait_for_interval(self):
        """リクエスト間隔を待機"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            wait_time = max(0, self.request_interval - elapsed)
            if wait_time > 0:
                logger.info(f"リクエスト間隔待機: {wait_time:.2f}秒")
                time.sleep(wait_time)
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        HTTPリクエストを実行
        
        Parameters
        ----------
        method : str
            HTTPメソッド（GET/POSTなど）
        url : str
            リクエストURL
        **kwargs : dict
            その他のリクエストパラメータ
            
        Returns
        -------
        requests.Response
            レスポンスオブジェクト
            
        Raises
        ------
        requests.RequestException
            HTTPリクエストエラー
        """
        # リクエスト間隔を待機
        self._wait_for_interval()
        
        # タイムアウトとリトライ設定
        kwargs.setdefault('timeout', self.timeout)
        
        # リクエスト送信
        start_time = datetime.now()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)
                break
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(f"リクエスト失敗 (試行 {attempt + 1}/{self.max_retries + 1}): {e}")
                    time.sleep(self.retry_delay * (2 ** attempt))  # 指数バックオフ
                else:
                    raise
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # リクエスト情報を記録
        request_info = HttpRequestInfo(
            timestamp=start_time,
            method=method,
            url=url,
            status_code=response.status_code,
            response_size=len(response.content),
            wait_time=response_time,
            success=True
        )
        
        self.request_history.append(request_info)
        self.last_request_time = end_time
        
        logger.info(f"HTTP {method} {url} - ステータス: {response.status_code}, "
                     f"サイズ: {len(response.content)}バイト, "
                     f"時間: {response_time:.2f}秒")
        
        return response
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GETリクエスト"""
        return self._make_request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POSTリクエスト"""
        return self._make_request('POST', url, **kwargs)
    
# グローバルインスタンス（設定はconfigで管理）
http_client = JRAHttpClient()
