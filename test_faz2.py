"""
test_faz2.py — Faz 2 (Web Scrapers & Telegram Bot) Kapsamlı Doğrulama Testi
Tüm scraper modüllerini, kaynak koordinatörünü, onay yöneticisini ve bot arayüzünü doğrular.
"""

import io
import logging
import sys

# Windows terminali için UTF-8 zorla
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

from colorama import init as colorama_init, Fore, Style
colorama_init(autoreset=True)

import config
config.dizinleri_olustur()

from scraper.rss_scraper import RSSScraper
from scraper.tev_scraper import TEVScraper
from scraper.turkiyeburslari_scraper import TurkiyeBurslariScraper
from scraper.isbank_scraper import IsBankasiScraper
from scraper.sabanci_scraper import SabanciScraper
from scraper.tupras_scraper import TuprasScraper
from scraper.ayb_scraper import AYBScraper
from scraper.kaynak_yonetici import KaynakYonetici
from telegram_bot.onay_yonetici import OnayYonetici
from telegram_bot.bot import TelegramOnayBotu


def test_scraperlar():
    print(f"\n{Fore.CYAN}{'━' * 60}")
    print(" 🧪 [1/4] BİREYSEL SCRAPER TESTLERİ")
    print(f"{'━' * 60}{Style.RESET_ALL}")

    testler = [
        ("TEV", TEVScraper),
        ("YTB Türkiye Bursları", TurkiyeBurslariScraper),
        ("İş Bankası", IsBankasiScraper),
        ("Sabancı Vakfı", SabanciScraper),
        ("TÜPRAŞ", TuprasScraper),
        ("Anadolu Vakfı", AYBScraper),
    ]

    basarili_sayisi = 0
    for isim, scraper_cls in testler:
        try:
            s = scraper_cls()
            duyurular = s.fetch_duyurular()
            if len(duyurular) > 0:
                print(f"  ✅ {Fore.GREEN}{isim:<25}{Style.RESET_ALL} -> {len(duyurular)} burs duyurusu çıkarıldı.")
                basarili_sayisi += 1
            else:
                print(f"  ⚠️ {Fore.YELLOW}{isim:<25}{Style.RESET_ALL} -> 0 burs bulundu (erişim kısıtı veya boş sayfa)")
        except Exception as e:
            print(f"  ❌ {Fore.RED}{isim:<25}{Style.RESET_ALL} -> HATA: {e}")

    print(f"\nSonuç: {basarili_sayisi}/{len(testler)} scraper başarıyla çalıştı.")
    assert basarili_sayisi >= 4, "En az 4 scraper başarıyla çalışmalıdır."


def test_kaynak_yonetici():
    print(f"\n{Fore.CYAN}{'━' * 60}")
    print(" 🧪 [2/4] KAYNAK YÖNETİCİSİ (KOORDİNATÖR) TESTİ")
    print(f"{'━' * 60}{Style.RESET_ALL}")

    yonetici = KaynakYonetici()
    # Mock modu testi
    mock_sonuc = yonetici.tara_ve_topla(mock_kullan=True)
    print(f"  ✅ Mock koordinasyonu: {len(mock_sonuc)} duyuru")
    assert len(mock_sonuc) == 3, "Mock scraper 3 burs döndürmeli."

    # RSS ve filtreleme testi
    toplam = yonetici.tara_ve_topla(filtrele_islenmis=False, limit_rss=3)
    print(f"  ✅ Canlı koordinasyon: Toplam {len(toplam)} burs duyurusu toplandı.")
    assert len(toplam) > 0, "Canlı koordinasyon en az 1 burs duyurusu bulmalıdır."


def test_onay_yonetici():
    print(f"\n{Fore.CYAN}{'━' * 60}")
    print(" 🧪 [3/4] TELEGRAM ONAY YÖNETİCİSİ TESTİ")
    print(f"{'━' * 60}{Style.RESET_ALL}")

    oy = OnayYonetici()
    test_id = "test_burs_999"
    oy.bekleyen_ekle(test_id, "Test Vakfı", "https://example.com/burs", "Test Özeti")

    bekleyenler = oy.bekleyenleri_getir()
    id_listesi = [b["burs_id"] for b in bekleyenler]
    assert test_id in id_listesi, "Eklenen test bursu bekleyenler arasında bulunmalıdır."
    print(f"  ✅ Bekleyen ekleme başarılı: {test_id}")

    oy.durum_guncelle(test_id, "onaylandi")
    assert test_id in oy.onayli_burs_idleri(), "Durum onaylandı olmalıdır."
    print(f"  ✅ Durum güncelleme başarılı: {test_id} -> onaylandi")


def test_telegram_bot():
    print(f"\n{Fore.CYAN}{'━' * 60}")
    print(" 🧪 [4/4] TELEGRAM BOT ARAYÜZÜ TESTİ")
    print(f"{'━' * 60}{Style.RESET_ALL}")

    bot = TelegramOnayBotu()
    print(f"  ✅ Bot başlatıldı. Aktiflik durumu: {bot.aktif}")
    
    # Pasif modda toplu onay güvenliği testi
    sonuc = bot.toplu_onay_iste([])
    assert sonuc is True, "Boş liste veya pasif mod True döndürmelidir."
    print("  ✅ Pasif mod ve güvenli arayüz doğrulandı.")


if __name__ == "__main__":
    print(f"{Fore.MAGENTA}════════════════════════════════════════════════════════════")
    print("   BURS OTOMASYONU FAZ 2 DOĞRULAMA TEST PAKETİ")
    print(f"════════════════════════════════════════════════════════════{Style.RESET_ALL}")

    test_scraperlar()
    test_kaynak_yonetici()
    test_onay_yonetici()
    test_telegram_bot()

    print(f"\n{Fore.GREEN}🎉 TÜM FAZ 2 BİLEŞENLERİ BAŞARIYLA DOĞRULANDI!{Style.RESET_ALL}\n")
