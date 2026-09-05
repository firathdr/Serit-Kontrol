-- SQLite şeması. `database/mysql.json` yoksa ilk bağlantıda otomatik uygulanır.

CREATE TABLE IF NOT EXISTS araclar (
    arac_id       INTEGER NOT NULL,
    saat          REAL,
    serit_id      INTEGER,
    ihlal_durumu  INTEGER NOT NULL DEFAULT 0,
    video_name    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS arac_goruntu (
    arac_id       INTEGER NOT NULL,
    goruntu       BLOB,
    giris_zamani  REAL,
    video_name    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS kullanicilar (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    isim      TEXT,
    username  TEXT NOT NULL UNIQUE,
    password  TEXT NOT NULL,
    rol       TEXT NOT NULL DEFAULT 'kullanici'
);

-- Sütun sırası MySQL şemasıyla aynı olmalı: api/main.py güncellenen kaydın
-- itiraz_durumu alanına konumdan (index 6) erişiyor.
CREATE TABLE IF NOT EXISTS itiraz_kayit (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT    NOT NULL,
    arac_id        INTEGER NOT NULL,
    video_name     TEXT    NOT NULL,
    durum          TEXT,
    sebep          TEXT,
    itiraz_durumu  TEXT DEFAULT 'beklemede'
);

CREATE INDEX IF NOT EXISTS idx_araclar_video ON araclar (video_name, arac_id);
CREATE INDEX IF NOT EXISTS idx_arac_goruntu_video ON arac_goruntu (video_name, arac_id);
CREATE INDEX IF NOT EXISTS idx_itiraz_kayit_video ON itiraz_kayit (video_name, arac_id);
