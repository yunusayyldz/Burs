"""
config.py — Merkezi yapılandırma ve ortam yönetimi
Burs Otomasyonu Sistemi
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Ortam değişkenlerini yükle
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# Temel dizin tanımları
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()

# ─────────────────────────────────────────────
# API Anahtarları ve Kimlik Bilgileri
# ─────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_CLIENT_SECRETS_PATH: Path = BASE_DIR / os.getenv("YOUTUBE_CLIENT_SECRETS_PATH", "client_secrets.json")
YOUTUBE_TOKEN_PATH: Path = BASE_DIR / os.getenv("YOUTUBE_TOKEN_PATH", "token.json")

# Telegram (Faz 2)
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ─────────────────────────────────────────────
# Dizin Yapısı
# ─────────────────────────────────────────────
CIKTI_DIR = BASE_DIR / "ciktilar"
SES_DIR = CIKTI_DIR / "sesler"
KART_DIR = CIKTI_DIR / "kartlar"
VIDEO_DIR = CIKTI_DIR / "videolar"
VERI_DIR = BASE_DIR / "veriler"
ISLENEN_BURSLAR_DOSYA = VERI_DIR / "islenen_burslar.json"
ONAY_BEKLEYENLER_DOSYA = VERI_DIR / "onay_bekleyenler.json"
KAYNAKLAR_DOSYA = VERI_DIR / "kaynaklar.json"


def dizinleri_olustur() -> None:
    """Gerekli dizinleri otomatik oluşturur."""
    dizinler = [SES_DIR, KART_DIR, VIDEO_DIR, VERI_DIR]
    for dizin in dizinler:
        dizin.mkdir(parents=True, exist_ok=True)
    logging.info("✅ Dizin yapısı hazır.")


# ─────────────────────────────────────────────
# Gemini Modeli Yapılandırması
# ─────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MAX_DENEME = 3  # JSON parse hatası durumunda yeniden deneme sayısı

# ─────────────────────────────────────────────
# Edge-TTS Yapılandırması
# ─────────────────────────────────────────────
TTS_SES = "tr-TR-AhmetNeural"
TTS_RATE = "-5%"      # Konuşma hızı (biraz yavaş = daha anlaşılır)
TTS_PITCH = "-2Hz"    # Ses perdesi

# ─────────────────────────────────────────────
# Video Yapılandırması
# ─────────────────────────────────────────────
@dataclass
class VideoConfig:
    """YouTube Shorts video parametreleri."""
    genislik: int = 1080
    yukseklik: int = 1920
    fps: int = 24              # 24fps: Shorts uyumlu, %20 daha hızlı render
    fade_in_sure: float = 0.5     # saniye
    fade_out_sure: float = 0.8    # saniye
    min_video_sure: float = 15.0  # saniye (Shorts minimum)
    max_video_sure: float = 60.0  # saniye (Shorts maksimum)
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    ffmpeg_preset: str = "veryfast"  # ultrafast/superfast/veryfast/faster/fast/medium

VIDEO_CONFIG = VideoConfig()


# ─────────────────────────────────────────────
# Renk Paleti (Video Kartı)
# ─────────────────────────────────────────────
@dataclass
class RenkPaleti:
    """Koyu tema renk paleti."""
    arka_plan_1: tuple = (10, 10, 26)         # #0A0A1A — derin koyu lacivert
    arka_plan_2: tuple = (26, 26, 62)         # #1A1A3E — koyu mor
    kart_arkaplan: tuple = (30, 30, 55, 230)  # RGBA — yarı saydam kart
    vurgu_sari: tuple = (255, 215, 0)         # #FFD700 — altın sarısı
    vurgu_mavi: tuple = (64, 156, 255)        # #409CFF — canlı mavi
    vurgu_yesil: tuple = (0, 230, 118)        # #00E676 — neon yeşil
    baslik_beyaz: tuple = (255, 255, 255)     # #FFFFFF
    metin_gri: tuple = (180, 180, 200)        # #B4B4C8
    cta_renk: tuple = (255, 90, 90)           # #FF5A5A — CTA kırmızısı

RENKLER = RenkPaleti()


# ─────────────────────────────────────────────
# 8 Zorunlu Burs Kriteri
# ─────────────────────────────────────────────
class BursKriteri(Enum):
    """8 zorunlu burs kriteri tanımı."""
    MADDI_TUTAR = "maddi_tutar"
    CAKISMA_DURUMU = "cakisma_durumu"
    EGITIM_TURU = "egitim_turu"
    BOLUM_KRITERI = "bolum_kriteri"
    BASARI_KRITERI = "basari_kriteri"
    YAN_HAKLAR = "yan_haklar"
    GERI_ODEME = "geri_odeme"
    BASVURU_TAKVIMI = "basvuru_takvimi"


# ─────────────────────────────────────────────
# YouTube Yapılandırması
# ─────────────────────────────────────────────
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_KATEGORI_ID = "27"   # Education
YOUTUBE_VARSAYILAN_GIZLILIK = "public"
YOUTUBE_CHUNK_BOYUTU = 256 * 1024  # 256 KB — resumable upload chunk

# ─────────────────────────────────────────────
# Loglama Yapılandırması
# ─────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = logging.INFO


def loglama_ayarla(log_dosyasi: bool = False) -> None:
    """Uygulama genelinde loglama ayarları."""
    handlers = [logging.StreamHandler()]
    if log_dosyasi:
        handlers.append(logging.FileHandler(BASE_DIR / "otomasyon.log", encoding="utf-8"))
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=handlers,
    )


# ─────────────────────────────────────────────
# API Anahtarı Doğrulaması
# ─────────────────────────────────────────────
def api_anahtarlarini_dogrula(youtube_gerekli: bool = False) -> bool:
    """
    Zorunlu API anahtarlarını kontrol eder.

    Args:
        youtube_gerekli: YouTube yükleme yapılacaksa True

    Returns:
        Tüm zorunlu anahtarlar mevcutsa True
    """
    hatalar = []

    if not GEMINI_API_KEY:
        hatalar.append(
            "❌ GEMINI_API_KEY bulunamadı!\n"
            "   → .env dosyasına ekleyin: GEMINI_API_KEY=your_key\n"
            "   → Anahtar almak için: https://aistudio.google.com/app/apikey"
        )

    if youtube_gerekli and not YOUTUBE_CLIENT_SECRETS_PATH.exists():
        hatalar.append(
            f"❌ YouTube client_secrets.json bulunamadı: {YOUTUBE_CLIENT_SECRETS_PATH}\n"
            "   → Google Cloud Console'dan 'Desktop App' tipi OAuth 2.0 istemcisi oluşturun\n"
            "   → JSON'ı indirip proje köküne koyun"
        )

    if hatalar:
        for hata in hatalar:
            print(hata)
        return False

    return True
