"""Database helper utilities.

This module provides low-level database connection and query helpers
used throughout the project.  All functions use ``mysql.connector`` for the
current project.
"""

from __future__ import annotations

import mysql.connector
import os
from typing import Any, Iterable, Tuple

from dotenv import load_dotenv

load_dotenv()

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", ""),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", ""),
}

if os.getenv("MYSQL_SOCKET"):
    MYSQL_CONFIG["unix_socket"] = os.getenv("MYSQL_SOCKET")


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
