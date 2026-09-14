"""File storage for JRA HTML pages.

A thin, single-responsibility wrapper around the on-disk ``data/`` directory.
Saving and loading are symmetric (Shift_JIS), matching how JRA pages are
served.
"""

import os
from typing import Optional

__all__ = ["HtmlStore"]


class HtmlStore:
    """Stores fetched JRA HTML files under a base directory."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def path(self, file_name: str) -> str:
        return os.path.join(self.base_dir, file_name)

    def save(self, html_content: str, file_name: str) -> str:
        """Save HTML content (Shift_JIS) and return the full path."""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
        path = self.path(file_name)
        with open(path, "w", encoding="shift_jis") as f:
            f.write(html_content)
        return path

    def load(self, file_name: str) -> str:
        """Read and decode an HTML file. Raises FileNotFoundError if absent."""
        with open(self.path(file_name), "r", encoding="shift_jis") as f:
            return f.read()

    def exists(self, file_name: str) -> bool:
        return os.path.exists(self.path(file_name))
