"""Veritabanı bağlantısı.

`database/mysql.json` varsa MySQL'e, yoksa proje kökündeki `data/serit.db`
SQLite dosyasına bağlanılır. Böylece depo klonlandığında hiçbir sunucu
kurmadan çalışır; MySQL isteğe bağlı kalır.

SQLite bağlantısı, projenin geri kalanının beklediği pymysql arayüzünü taklit
eden ince bir sarmalayıcıyla döner: `%s` yer tutucuları, `cursor(DictCursor)`
çağrısı ve MySQL'e özgü birkaç ifade otomatik çevrilir. Bu sayede aynı SQL iki
motorda da çalışır.
"""

import json
import os
import re
import sqlite3
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DATABASE_DIR.parent
MYSQL_CONFIG_PATH = DATABASE_DIR / "mysql.json"
SQLITE_SCHEMA_PATH = DATABASE_DIR / "schema_sqlite.sql"

_ANY_VALUE_RE = re.compile(r"ANY_VALUE\(\s*([^()]+?)\s*\)", re.IGNORECASE)
_TRUNCATE_RE = re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE)

# Şema aynı süreçte her bağlantıda yeniden çalıştırılmasın diye.
_prepared_sqlite_files = set()


def sqlite_path():
    """SQLite dosyasının yolu. `SERIT_SQLITE_PATH` ile değiştirilebilir."""
    override = os.environ.get("SERIT_SQLITE_PATH")
    return Path(override) if override else PROJECT_ROOT / "data" / "serit.db"


def use_mysql():
    """MySQL yapılandırması var mı?"""
    return MYSQL_CONFIG_PATH.exists()


def _to_sqlite(sql):
    """MySQL lehçesindeki sorguyu SQLite'ın anlayacağı hale getirir."""
    sql = _ANY_VALUE_RE.sub(r"\1", sql)
    sql = _TRUNCATE_RE.sub("DELETE FROM", sql)
    return sql.replace("%s", "?")


class _SqliteCursor:
    """pymysql kursorü gibi davranan sqlite3 kursörü."""

    def __init__(self, cursor, as_dict=False):
        self._cursor = cursor
        self._as_dict = as_dict

    def execute(self, sql, params=None):
        self._cursor.execute(_to_sqlite(sql), tuple(params or ()))
        return self

    def executemany(self, sql, params_seq):
        self._cursor.executemany(_to_sqlite(sql), params_seq)
        return self

    def _shape(self, row):
        if row is None or not self._as_dict:
            return row
        return {column[0]: row[index] for index, column in enumerate(self._cursor.description)}

    def fetchone(self):
        return self._shape(self._cursor.fetchone())

    def fetchall(self):
        return [self._shape(row) for row in self._cursor.fetchall()]

    def fetchmany(self, size=1):
        return [self._shape(row) for row in self._cursor.fetchmany(size)]

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()


class _SqliteConnection:
    """pymysql bağlantısı gibi davranan sqlite3 bağlantısı."""

    def __init__(self, connection):
        self._connection = connection

    def cursor(self, cursor_class=None):
        name = getattr(cursor_class, "__name__", "")
        return _SqliteCursor(self._connection.cursor(), as_dict="dict" in name.lower())

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def _prepare_sqlite(connection, path):
    if path in _prepared_sqlite_files:
        return
    connection.executescript(SQLITE_SCHEMA_PATH.read_text(encoding="utf-8"))
    _prepared_sqlite_files.add(path)


def get_connection():
    """Yapılandırmaya göre MySQL ya da SQLite bağlantısı döndürür."""
    if use_mysql():
        import pymysql

        with MYSQL_CONFIG_PATH.open(encoding="utf-8") as config_file:
            config = json.load(config_file)

        return pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            port=config.get("port", 3306),
            charset=config.get("charset", "utf8mb4"),
        )

    path = sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    _prepare_sqlite(connection, path)
    return _SqliteConnection(connection)
