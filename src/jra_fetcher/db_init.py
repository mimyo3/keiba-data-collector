#!/usr/bin/env python3
"""Initialize JRA database tables.

This script creates the jra_html_metadata and race_days tables in the MySQL database.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.jra_fetcher.db_schema import JRA_HTML_METADATA_TABLE_SQL
from src.helpers.db_helper import get_connection


def init_jra_db():
    """Initialize both jra_html_metadata and race_days tables."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Create jra_html_metadata table
        cur.execute(JRA_HTML_METADATA_TABLE_SQL)
        
        # Create race_days table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS race_days (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                `year_month` VARCHAR(8) NOT NULL,
                race_day DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("JRA database tables created successfully.")
    except Exception as e:
        print(f"Error creating JRA database tables: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_jra_db()