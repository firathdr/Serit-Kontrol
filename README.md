# Şerit Kontrol Sistemi

Bu proje, video tabanlı araç tespiti, şerit ihlali analizi ve kullanıcı arayüzü ile yönetim sağlayan bütünleşik bir sistemdir. Hem masaüstü (PyQt5 GUI) hem de web tabanlı (Flask API) bileşenleri içerir.

## İçerik

- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Klasör Yapısı](#klasör-yapısı)
- [Kullanım](#kullanım)
- [API Endpointleri](#api-endpointleri)
- [Geliştirici Notları](#geliştirici-notları)
- [Lisans](#lisans)

---

## Özellikler

- **Video üzerinden araç tespiti ve takibi** (YOLO, DeepSORT, vb.)
- **Şerit ihlali tespiti** ve raporlanması
- **Kullanıcı arayüzü**: PyQt5 tabanlı modern masaüstü uygulaması
- **Web API**: Flask ile RESTful servisler (kullanıcı yönetimi, araç kayıtları, ihlal/itiraz işlemleri)
- **Veritabanı**: MySQL entegrasyonu
- **Kullanıcı rolleri**: Admin ve normal kullanıcı ayrımı
- **Video klip kesme, maske ve model seçimi**
- **Kolay genişletilebilir mimari**

---

## Kurulum

### 1. Ortamı Hazırlama

Python 3.8+ ve pip gereklidir. (Tavsiye: Sanal ortam kullanın)

```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\\Scripts\\activate)
pip install -r requirements.txt
```

### 2. Veritabanı Kurulumu

- `database/mysql.json` dosyasını kendi MySQL bilgilerinizle doldurun.
- Gerekli tabloları oluşturun (örnek SQL scripti ekleyin).

### 3. Modeller ve Maskeler

- `models/` klasörüne eğitimli YOLO veya diğer modellerinizi ekleyin.
- `masks/` klasörüne ilgili maske dosyalarını ekleyin.

---

## Klasör Yapısı

```
Staj/
├── app.py                # Hem API hem GUI'yi başlatır
├── api/                  # Flask tabanlı web API
├── core/                 # Video işleme, tespit, takip ve yardımcı modüller
├── gui/                  # PyQt5 arayüz dosyaları
├── database/             # Veritabanı bağlantı ve yardımcı dosyaları
├── models/               # Eğitimli derin öğrenme modelleri
├── masks/                # Görüntü maske dosyaları
├── videos/               # Test ve demo videoları
├── corridors/            # Şerit/corridor tanımları (JSON)
├── temp_clips/           # Geçici video klipleri
├── requirements.txt      # Tüm bağımlılıklar burada
├── README.md             # Bu dosya
└── ...                   # Diğer yardımcı dosyalar
```

---

## Kullanım

### Tüm Sistemi Başlatmak

```bash
python app.py
```
Bu komut ile hem Flask API hem de PyQt5 arayüzü aynı anda başlatılır.

### Sadece API'yi Başlatmak

```bash
cd api
python main.py
```

### Sadece GUI'yi Başlatmak

```bash
cd gui
python gui_pyqt.py
```

---

## API Endpointleri

Ana API dosyası: `api/main.py`

- `/api/registr` : Kullanıcı kaydı (POST)
- `/api/login` : Kullanıcı girişi (POST)
- `/api/araclar` : Araç kayıtlarını getir (GET)
- `/api/araclar/<video_name>/<arac_id>` : Belirli araca ait detay (GET/DELETE)
- `/api/itiraz_et` : İtiraz kaydı oluştur (POST)
- `/api/admin/kullanicilar` : Tüm kullanıcıları getir (admin)
- `/api/admin/yetkilendir` : Kullanıcıyı admin yap (admin)
- `/api/admin/kullanici-sil` : Kullanıcı sil (admin)
- `/api/admin/ihlaller` : Tüm ihlalleri getir (admin)
- `/api/admin/itirazlar` : Tüm itirazları getir (admin)
- `/api/admin/itiraz` : İtiraz durumunu güncelle (PUT)
- `/api/videos/<video_name>` : Video klip servisi (GET)
- `/api/itiraz_kayit/detay` : İtiraz detaylarını getir (GET)

---

## Geliştirici Notları

- **Modüler yapı**: Her ana fonksiyon ayrı bir modülde.
- **Model ve maske seçimi**: GUI üzerinden kolayca yapılabilir.
- **Veritabanı bağlantısı**: `database/db_config.py` üzerinden yönetilir.
- **Gelişmiş loglama**: `core/log.py` ve ilgili log dosyaları.
- **Testler**: `test.py`, `car_id_test.py` gibi dosyalar ile birim testler.

---

## Lisans

Bu proje MIT lisansı ile lisanslanmıştır. Ayrıntılar için `LICENSE` dosyasına bakınız.

---

Her türlü katkı, hata bildirimi ve öneri için lütfen iletişime geçin!