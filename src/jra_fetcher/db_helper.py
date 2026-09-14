"""Database helper functions for JRA fetcher."""

import re

import mysql.connector
from src.helpers.db_helper import get_connection


def get_jra_connection():
    """Get a MySQL connection for JRA operations."""
    return get_connection()




def save_jra_html_metadata(year_month: str, prev_month_url: str, cname: str,file_name: str) -> None:
    """Save JRA HTML metadata to the database."""
    conn = get_jra_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO jra_html_metadata (
                `year_month`, prev_month_url, cname, file_name
            ) VALUES (%s,  %s, %s, %s)
            """,
            (year_month, prev_month_url, cname, file_name)
        )
        conn.commit()
        print(f"JRA HTML metadata saved successfully: {file_name}")
    except Exception as e:
        print(f"Error saving JRA HTML metadata: {e}")
        raise
    finally:
        # Consume any unread results to avoid the "Unread result found" error
        try:
            while conn.unread_result:
                conn.consume_results()
        except:
            pass
        # Ensure connection is closed even if there's an error
        if conn.is_connected():
            conn.close()


def get_jra_html_metadata_by_year_month(year_month: str) -> dict:
    """Get JRA HTML metadata by year and month."""
    conn = get_jra_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT *
            FROM jra_html_metadata
            WHERE `year_month` = %s
            ORDER BY (file_name = CONCAT('monthdata_', %s)) DESC, id DESC
            LIMIT 1
            """,
            (year_month, year_month)
        )
        result = cur.fetchone()
        return result
    except Exception as e:
        print(f"Error getting JRA HTML metadata by year_month: {e}")
        raise
    finally:
        conn.close()


def get_all_jra_html_metadata() -> list[dict]:
    """Return all saved JRA HTML metadata rows, newest first."""
    conn = get_jra_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM jra_html_metadata ORDER BY id DESC")
        return cur.fetchall()
    except Exception as e:
        print(f"Error getting all JRA HTML metadata: {e}")
        raise
    finally:
        conn.close()








def save_race_day(year_month: str, race_day: str) -> None:
    """Save race day information to the database."""
    conn = get_jra_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO race_days (`year_month`, race_day)
            SELECT %s, %s
            FROM DUAL
            WHERE NOT EXISTS (
                SELECT 1
                FROM race_days
                WHERE `year_month` = %s AND race_day = %s
            )
            """,
            (year_month, race_day, year_month, race_day)
        )
        conn.commit()
        print(f"Race day saved successfully: {race_day}")
    except Exception as e:
        print(f"Error saving race day: {e}")
        raise
    finally:
        conn.close()


def get_race_days(start_date: str, end_date: str) -> list[str]:
    """Return stored race days in the requested inclusive date range."""
    conn = get_jra_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT race_day
            FROM race_days
            WHERE race_day BETWEEN %s AND %s
            ORDER BY race_day
            """,
            (start_date, end_date),
        )
        return [row[0].strftime("%Y%m%d") for row in cur.fetchall()]
    except Exception as exc:
        print(f"Error getting race days: {exc}")
        raise
    finally:
        conn.close()


