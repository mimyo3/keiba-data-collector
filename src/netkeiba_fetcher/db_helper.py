"""Database helper functions for netkeiba fetcher."""

from src.helpers.db_helper import get_connection


def get_races_from_db() -> list[dict]:
    """Get all races from the database.

    Returns:
        List of race dictionaries
    """
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM races")
        races = cur.fetchall()
        return races
    except Exception as e:
        print(f"Error fetching races from database: {e}")
        return []
    finally:
        conn.close()
