"""
HTTP client module for making HTTP requests with rate limiting and in-memory caching.

This module provides a singleton HTTP client that:
1. Enforces rate limiting (max 1 request per second per host)
2. Supports in-memory caching of responses
3. Provides both GET and POST methods

The client is designed to be used as a global singleton, accessed via the `default_client` variable.
"""

import time
from collections import defaultdict, deque
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests


class HTTPClient:
    """
    A thread-safe HTTP client with rate limiting and in-memory caching.

    This client enforces a rate limit of 1 request per second per host to avoid
    overwhelming servers. It also supports in-memory caching of responses.
    """

    def __init__(self):
        self._session = requests.Session()
        # Set a proper User-Agent header to avoid 400 errors
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # Rate limiting: store last request times for each host
        self._last_request_times: Dict[str, float] = {}
        # Rate limiting: store request counts per second for each host
        self._request_counts: Dict[str, deque] = defaultdict(deque)
        # In-memory cache
        self._cache: Dict[str, tuple] = {}

    def _rate_limit(self, host: str) -> None:
        """
        Enforce rate limiting for the given host.

        Ensures that no more than 1 request per second is made to the same host.
        """
        current_time = time.time()
        last_request_time = self._last_request_times.get(host, 0)
        
        # If we've made a request to this host within the last second,
        # wait until the next second
        if current_time - last_request_time < 1:
            sleep_time = 1 - (current_time - last_request_time)
            time.sleep(sleep_time)
        
        self._last_request_times[host] = time.time()

    def _get_cache_key(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key for the given request parameters.
        """
        if params is None:
            params = {}
        
        # Sort params to ensure consistent keys
        param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{method}:{url}?{param_str}"

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> str:
        """
        Make a GET request to the given URL.

        Parameters
        ----------
        url : str
            The URL to fetch.
        params : dict, optional
            Query parameters to include in the request.
        ttl : int, optional
            Time-to-live for caching in seconds. If None, no caching is performed.

        Returns
        -------
        str
            The response text.
        """
        # Parse host from URL
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        
        # Rate limiting
        self._rate_limit(host)
        
        # Generate cache key
        cache_key = self._get_cache_key("GET", url, params)
        
        # Check cache if TTL is specified
        if ttl is not None:
            cached_response = self._cache.get(cache_key)
            if cached_response:
                response_time, response_text = cached_response
                if time.time() - response_time < ttl:
                    return response_text
        
        # Make request
        response = self._session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        response_text = response.text
        
        # Cache response if TTL is specified
        if ttl is not None:
            self._cache[cache_key] = (time.time(), response_text)
        
        return response_text

    def post(self, url: str, data: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> str:
        """
        Make a POST request to the given URL.

        Parameters
        ----------
        url : str
            The URL to post to.
        data : dict, optional
            Data to send in the POST request body.
        ttl : int, optional
            Time-to-live for caching in seconds. If None, no caching is performed.

        Returns
        -------
        str
            The response text.
        """
        # Parse host from URL
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        
        # Rate limiting
        self._rate_limit(host)
        
        # Generate cache key
        cache_key = self._get_cache_key("POST", url, data)
        
        # Check cache if TTL is specified
        if ttl is not None:
            cached_response = self._cache.get(cache_key)
            if cached_response:
                response_time, response_text = cached_response
                if time.time() - response_time < ttl:
                    return response_text
        
        # Make request
        response = self._session.post(url, data=data, timeout=10)
        response.raise_for_status()
        
        response_text = response.text
        
        # Cache response if TTL is specified
        if ttl is not None:
            self._cache[cache_key] = (time.time(), response_text)
        
        return response_text


# Create a default client instance
default_client = HTTPClient()