"""Database helper utilities.

This module provides low-level database connection and query helpers
used throughout the project.  All functions use ``mysql.connector`` for the
current project.
"""

from __future__ import annotations

import mysql.connector
from typing import Any, Iterable, Tuple

# from core.db_config import MYSQL_CONFIG
from src.backend.db_config import MYSQL_CONFIG


def get_connection() -> mysql.connector.MySQLConnection:
    """Return a database connection for MySQL.

    Returns
    -------
    mysql.connector.MySQLConnection
        A connected MySQL connection.
    """
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    return conn


def execute(
    connection: mysql.connector.MySQLConnection,
    sql: str,
    params: Tuple[Any, ...] | Iterable[Any] | None = None,
) -> mysql.connector.cursor.MySQLCursor:
    """Execute an SQL statement.

    Parameters
    ----------
    connection:
        The database connection obtained from :func:`get_connection`.
    sql:
        The SQL statement to execute.
    params:
        Optional parameters for prepared statements.

    Returns
    -------
    mysql.connector.cursor.MySQLCursor
        The cursor with execution results.
    """
    cur = connection.cursor()
    if params is not None:
        cur.execute(sql, tuple(params))
    else:
        cur.execute(sql)
    return cur
