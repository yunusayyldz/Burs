# 🎓 Burs Otomasyonu — YouTube Shorts Fabrikası

Türkiye'deki yükseköğrenim burs duyurularını resmi kaynaklardan otomatik olarak tarayan, Gemini 2.5 Flash ile 8 kriterli analiz yapan, Edge-TTS (AhmetNeural) ile seslendiren, Pillow ve FFmpeg ile dikey (9:16) YouTube Shorts videoları üreten ve YouTube Data API v3 ile kanala yükleyen **%100 ücretsiz, açık kaynaklı** otonom Python içerik fabrikası.

---

## 🏛 Temel Mimari Prensipleri

1. **Ayrıştırma İlkesi (Bölünemezlik):** Aynı kurum veya vakıf (TEV, YTB, İş Bankası vb.) birden fazla burs sağlasa dahi her program tek tek ayrıştırılarak bağımsız bir YouTube Shorts videosu ve bağımsız bir veri kaydı olarak işlenir.
2. **8 Zorunlu Kriter:** Maddi Tutar, Çakışma Durumu, Eğitim Türü, Bölüm Kriteri, Başarı Şartı, Yan Haklar, Geri Ödeme Şartı, Başvuru Takvimi.
3. **Sıfır Maliyet:** Google AI Studio (Gemini Flash), Edge-TTS, FFmpeg, YouTube Data API v3 ve yerel Python araçları.

---

## 🌐 Desteklenen Burs Kaynakları (Faz 2)

| Kaynak | Hedef Kurum / Servis | Yöntem |
|---|---|---|
| **TEV Scraper** | Türk Eğitim Vakfı (5 Bağımsız Burs) | Canlı HTML Parser |
| **YTB Scraper** | Türkiye Bursları (Lisans, YL, Doktora) | Çok Dilli Web Parser |
| **İş Bankası Scraper** | Altın Gençler & 81 İlden 81 Öğrenci | Kurumsal Eğitim Portalı |
| **Sabancı Vakfı Scraper**| Üniversiteye Giriş, Kalkınma, Engelli Bursları | Resilient HTTP / Fallback |
| **TÜPRAŞ Scraper** | Mühendislik & Teknoloji Lisans Bursu | Sorumluluk Portalı |
| **Anadolu Vakfı Scraper**| Yükseköğrenim Lisans Bursu | Başvuru Sistemi |
| **RSS Scraper** | Google News & Üniversite Burs Haberleri | Günlük RSS / Atom Feed |

---

## 🚀 Hızlı Başlangıç

### 1. Repoyu Klonlayın
```bash
git clone https://github.com/yunusayyldz/Burs.git
cd Burs
```

### 2. Sanal Ortamı Hazırlayın
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Yapılandırma (`.env`)
`.env.example` dosyasını `.env` olarak kopyalayın ve API anahtarlarınızı girin:
```bash
copy .env.example .env
```
```env
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_CLIENT_SECRETS_PATH=client_secrets.json
TELEGRAM_BOT_TOKEN=your_bot_token_optional
TELEGRAM_CHAT_ID=your_chat_id_optional
```

---

## 🎬 Kullanım Seçenekleri

### 1. Sadece Bursları Tara ve Listele (Video Üretmez)
Tüm aktif kaynakları tarar, tekilleştirir ve terminalde tablo halinde listeler:
```bash
venv\Scripts\python.exe main.py --sadece-tara
```

### 2. Mock Moduyla Hızlı Test (API Anahtarı Gerekmez, ~8s)
```bash
venv\Scripts\python.exe main.py --mock --dry-run --telegram-devre-disi --limit 1
```

### 3. Gerçek Sitelerden 2 Burs Çekip Yerel Video Üret
```bash
venv\Scripts\python.exe main.py --dry-run --telegram-devre-disi --limit 2
```

### 4. Telegram Onay Botu ile Tam Otonom Üretim & YouTube Yükleme
```bash
venv\Scripts\python.exe main.py
```

### 5. Test Paketini Çalıştırma
```bash
venv\Scripts\python.exe test_faz2.py
```

---

## 📁 Dizin Yapısı

```
Burs/
├── scraper/                     # Modüler web ve RSS kazıma motoru
│   ├── base_scraper.py          # Soyut temel sınıf & HamDuyuru modeli
│   ├── tev_scraper.py           # TEV özel scraper (5 program)
│   ├── turkiyeburslari_scraper.py# YTB özel scraper (3 program)
│   ├── isbank_scraper.py        # İş Bankası özel scraper (2 program)
│   ├── sabanci_scraper.py       # Sabancı Vakfı scraper (3 program)
│   ├── tupras_scraper.py        # TÜPRAŞ burs scraper
│   ├── ayb_scraper.py           # Anadolu Vakfı burs scraper
│   ├── rss_scraper.py           # Genel Google News burs RSS okuyucu
│   ├── mock_scraper.py          # Test verileri
│   └── kaynak_yonetici.py       # Merkezi koordinatör ve tekilleştirici
│
├── telegram_bot/                # Operatör onay mekanizması
│   ├── bot.py                   # python-telegram-bot v22.x (Mod B Toplu Onay)
│   └── onay_yonetici.py         # Onay durumu persist yöneticisi
│
├── veriler/
│   └── kaynaklar.json           # Scraper kaynak yapılandırması
│
├── config.py                    # Merkezi yapılandırma ve parametreler
├── ai_analiz.py                 # Gemini 2.5 Flash 8 kriterli analiz motoru
├── seslendirici.py              # Microsoft Edge TTS entegrasyonu
├── video_olusturucu.py          # Pillow kart tasarımı + FFmpeg hızlı render
├── youtube_yukleyici.py         # YouTube Data API v3 yükleme motoru
├── main.py                      # Ana orkestratör
└── test_faz2.py                 # Faz 2 doğrulama test paketi
```

---

## 📄 Lisans
Bu proje MIT lisansı ile lisanslanmıştır.
