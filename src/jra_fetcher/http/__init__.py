#!/usr/bin/env python3
"""
HTTP handling package for JRA access.
"""

from .common_http import (
    JRAHttpClient,
    HttpRequestInfo
)

__all__ = [
    'JRAHttpClient',
    'HttpRequestInfo'
]