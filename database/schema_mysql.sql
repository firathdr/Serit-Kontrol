-- MySQL şeması. Yalnızca MySQL kullanacaksan gerekir:
--   mysql -u root -p -e "CREATE DATABASE serit_kontrol CHARACTER SET utf8mb4;"
--   mysql -u root -p serit_kontrol < database/schema_mysql.sql
-- Ardından database/mysql.example.json dosyasını mysql.json olarak kopyala.

CREATE TABLE IF NOT EXISTS araclar (
    arac_id       INT          NOT NULL,
    saat          DOUBLE,
    serit_id      INT,
    ihlal_durumu  TINYINT(1)   NOT NULL DEFAULT 0,
    video_name    VARCHAR(255) NOT NULL,
    KEY idx_araclar_video (video_name, arac_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS arac_goruntu (
    arac_id       INT          NOT NULL,
    goruntu       LONGBLOB,
    giris_zamani  DOUBLE,
    video_name    VARCHAR(255) NOT NULL,
    KEY idx_arac_goruntu_video (video_name, arac_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS kullanicilar (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    isim      VARCHAR(255),
    username  VARCHAR(255) NOT NULL UNIQUE,
    password  VARCHAR(255) NOT NULL,
    rol       VARCHAR(32)  NOT NULL DEFAULT 'kullanici'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- Sütun sırası önemli: api/main.py güncellenen kaydın itiraz_durumu alanına
-- konumdan (index 6) erişiyor.
CREATE TABLE IF NOT EXISTS itiraz_kayit (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(255) NOT NULL,
    arac_id        INT          NOT NULL,
    video_name     VARCHAR(255) NOT NULL,
    durum          VARCHAR(32),
    sebep          TEXT,
    itiraz_durumu  VARCHAR(32) DEFAULT 'beklemede',
    KEY idx_itiraz_kayit_video (video_name, arac_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
