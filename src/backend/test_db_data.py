"""Test database data insertion utilities."""

from typing import List, Dict, Any
from src.helpers.db_helper import get_connection


def insert_test_data(table_name: str, data: List[Dict[str, Any]]) -> int:
    """Insert test data into the specified table.

    Args:
        table_name: Name of the table to insert data into
        data: List of dictionaries containing the data to insert

    Returns:
        Number of rows inserted
    """
    if not data:
        return 0

    connection = get_connection()
    try:
        cursor = connection.cursor()
        # Get column names from the table
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = [row[0] for row in cursor.fetchall()]

        # Create INSERT query
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join([f'`{col}`' for col in columns])
        query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"

        # Insert data
        for row in data:
            values = [row.get(col, None) for col in columns]
            cursor.execute(query, tuple(values))

        connection.commit()
        return cursor.rowcount
    except Exception as e:
        print(f"Error inserting test data into {table_name}: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()


def insert_sample_race_data() -> int:
    """Insert sample race data for testing purposes.

    Returns:
        Number of rows inserted
    """
    sample_data = [
        {
            "id": 1,
            "name": "サンプルレース1",
            "date": "2023-01-01",
            "venue": "東京",
            "race_number": 1,
            "distance": 2000,
            "grade": "G1"
        },
        {
            "id": 2,
            "name": "サンプルレース2",
            "date": "2023-01-02",
            "venue": "中山",
            "race_number": 2,
            "distance": 1600,
            "grade": "G2"
        },
        {
            "id": 3,
            "name": "サンプルレース3",
            "date": "2023-01-03",
            "venue": "函館",
            "race_number": 3,
            "distance": 2200,
            "grade": "G3"
        }
    ]

    return insert_test_data("races", sample_data)


def insert_sample_horse_race_data() -> int:
    """Insert sample horse race result data for testing purposes.

    Returns:
        Number of rows inserted
    """
    sample_data = [
        {
            "id": 1,
            "race_id": 1,
            "horse_name": "サンプル馬1",
            "jockey": "田中騎手",
            "trainer": "田中調教師",
            "weight": 550,
            "time": "2:25.0",
            "odds": 1.2
        },
        {
            "id": 2,
            "race_id": 1,
            "horse_name": "サンプル馬2",
            "jockey": "佐藤騎手",
            "trainer": "佐藤調教師",
            "weight": 560,
            "time": "2:27.5",
            "odds": 2.5
        },
        {
            "id": 3,
            "race_id": 2,
            "horse_name": "サンプル馬3",
            "jockey": "鈴木騎手",
            "trainer": "鈴木調教師",
            "weight": 540,
            "time": "2:30.0",
            "odds": 3.0
        }
    ]

    return insert_test_data("horse_race_results", sample_data)
