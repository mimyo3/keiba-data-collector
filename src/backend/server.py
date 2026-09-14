"""HTTP API and static frontend server for the keiba application."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.helpers.db_helper import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_BUILD = PROJECT_ROOT / "frontend" / "build"

app = FastAPI(title="Keiba API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/db/horse_race_results")
def horse_race_results() -> list[dict[str, Any]]:
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM horse_race_results ORDER BY id")
        return cursor.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="データベースに接続できません") from exc
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if FRONTEND_BUILD.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD / "static"), name="static")


@app.get("/{path:path}")
def frontend(path: str = "") -> FileResponse:
    index_file = FRONTEND_BUILD / "index.html"
    requested_file = FRONTEND_BUILD / path

    if requested_file.is_file():
        return FileResponse(requested_file)
    if index_file.is_file():
        return FileResponse(index_file)
    raise HTTPException(status_code=503, detail="フロントエンドをビルドしてください")