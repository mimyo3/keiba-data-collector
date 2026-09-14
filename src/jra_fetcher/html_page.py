"""HTML page fetching, persistence, and metadata lookup."""

import os
from typing import Optional

from src.jra_fetcher.config import DATA_DIR
from src.jra_fetcher.db_helper import get_jra_html_metadata_by_year_month



def save_html_file(html_content: str, file_name: str) -> None:
    """Save a fetched HTML page in the package data directory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    save_path = os.path.join(DATA_DIR, file_name)
    with open(save_path, "w", encoding="utf-8") as file:
        file.write(html_content)


def get_saved_html_for_month(month: str) -> Optional[dict]:
    """Return navigation metadata saved for a month, if available."""
    metadata = get_jra_html_metadata_by_year_month(month)
    if not metadata:
        return None
    file_name = metadata.get("file_name")
    return {
        "url": metadata.get("prev_month_url"),
        "cname": metadata.get("cname"),
        "file_name": file_name,
        "save_path": file_name,
    }
