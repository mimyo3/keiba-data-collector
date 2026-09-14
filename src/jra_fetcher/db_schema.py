"""Database schema definitions for the JRA fetcher.

This module contains the SQL statements for creating and managing database tables
for JRA-related operations.
"""

# SQL statement to create the jra_html_metadata table
JRA_HTML_METADATA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jra_html_metadata (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    `year_month` VARCHAR(8) NOT NULL,
    prev_month_url VARCHAR(30),
    cname VARCHAR(30),
    file_name VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
"""

__all__ = ["JRA_HTML_METADATA_TABLE_SQL"]