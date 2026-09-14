"""Utility functions used throughout the project.

Only minimal date parsing / formatting helpers are provided as
placeholders for future implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

__all__ = ["parse_date", "format_date"]


def parse_date(date_str: str) -> datetime:  # pragma: no cover
    """Parse a date string in ``YYYYMMDD`` format.

    Parameters
    ----------
    date_str:
        A string in ``YYYYMMDD`` format.
    Returns
    -------
    datetime
        Parsed datetime instance.
    """
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid date format: {date_str}") from exc


def format_date(dt: datetime, fmt: str = "%Y-%m-%d") -> str:  # pragma: no cover
    """Format a :class:`datetime` into a string.

    Parameters
    ----------
    dt:
        The datetime to format.
    fmt:
        Format string passed to :meth:`datetime.strftime`.
    Returns
    -------
    str
        Formatted string.
    """
    return dt.strftime(fmt)
