# ============================================================
# services/log.py — 渔获日记服务
# 复用 stats.py 的数据库连接模式（本地 SQLite / Turso 自动切换）
# ============================================================

import os
import json
import base64
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

SYD_TZ = ZoneInfo("Australia/Sydney")

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")
USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

DB_PATH = Path(__file__).parent.parent / "data" / "stats.db"
MAX_PHOTOS = 4
MAX_PHOTO_BYTES = 3 * 1024 * 1024


def _get_connection():
    if USE_TURSO:
        import libsql_client
        return libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN)
    else:
        import sqlite3
        return sqlite3.connect(DB_PATH)


@contextmanager
def _db_cursor():
    conn = _get_connection()
    try:
        if USE_TURSO:
            yield conn
        else:
            yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def _execute(sql: str, params: tuple = ()):
    with _db_cursor() as cursor:
        cursor.execute(sql, params)
        if not USE_TURSO:
            return cursor.lastrowid


def _query_one(sql: str, params: tuple = ()):
    with _db_cursor() as cursor:
        if USE_TURSO:
            result = cursor.execute(sql, params)
            rows = result.rows
            return rows[0] if rows else None
        else:
            cursor.execute(sql, params)
            return cursor.fetchone()


def _query_all(sql: str, params: tuple = ()):
    with _db_cursor() as cursor:
        if USE_TURSO:
            result = cursor.execute(sql, params)
            return result.rows
        else:
            cursor.execute(sql, params)
            return cursor.fetchall()


def _init_db():
    if not USE_TURSO:
        DB_PATH.parent.mkdir(exist_ok=True)
    _execute('''
        CREATE TABLE IF NOT EXISTS fishing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fish_date DATE NOT NULL,
            spot_name TEXT NOT NULL,
            author TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            fish_caught TEXT DEFAULT '[]',
            photos TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')


_init_db()


def add_entry(
    fish_date: str,
    spot_name: str,
    author: str,
    notes: str,
    fish_caught: list,
    photos: list,
) -> int:
    """添加一条渔获记录，photos 为 bytes 列表。返回新记录 id。"""
    safe_photos = [
        p for p in (photos or [])[:MAX_PHOTOS]
        if len(p) <= MAX_PHOTO_BYTES
    ]
    fish_json = json.dumps(fish_caught, ensure_ascii=False)
    photos_json = json.dumps(
        [base64.b64encode(p).decode() for p in safe_photos],
        ensure_ascii=False,
    )
    created_at = datetime.now(SYD_TZ).isoformat()
    rowid = _execute(
        '''INSERT INTO fishing_log
               (fish_date, spot_name, author, notes, fish_caught, photos, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (fish_date, spot_name, author or "", notes or "", fish_json, photos_json, created_at),
    )
    if rowid is None:
        result = _query_one("SELECT id FROM fishing_log ORDER BY id DESC LIMIT 1")
        return result[0] if result else None
    return rowid


def get_entries(limit: int = 100) -> list:
    """返回最新 limit 条记录，每条为 dict。photos 字段为 bytes 列表。"""
    rows = _query_all(
        '''SELECT id, fish_date, spot_name, author, notes, fish_caught, photos, created_at
           FROM fishing_log
           ORDER BY fish_date DESC, id DESC
           LIMIT ?''',
        (limit,),
    )
    entries = []
    for row in rows:
        entries.append({
            "id": row[0],
            "fish_date": row[1],
            "spot_name": row[2],
            "author": row[3] or "",
            "notes": row[4] or "",
            "fish_caught": json.loads(row[5] or "[]"),
            "photos": [base64.b64decode(p) for p in json.loads(row[6] or "[]")],
            "created_at": row[7] or "",
        })
    return entries


def delete_entry(entry_id: int) -> None:
    """删除指定记录。"""
    _execute("DELETE FROM fishing_log WHERE id = ?", (entry_id,))
