"""
main.py — Burs Otomasyonu Ana Orkestratör (Faz 2)
Uçtan uca pipeline: Gerçek Web Scraper -> Telegram Onayı (Mod B) -> AI Analiz -> TTS -> Video -> YouTube

Kullanım:
    python main.py                           # Gerçek scraper'lar + Telegram onayı + YouTube yükleme
    python main.py --dry-run                 # YouTube'a yüklemeden yerel video üret
    python main.py --mock --dry-run          # Mock scraper ile hızlı yerel test
    python main.py --telegram-devre-disi     # Telegram onaysız doğrudan üretim
    python main.py --sadece-tara             # Yalnızca bursları tara ve listele (video üretmez)
    python main.py --onay-bekleyenler        # Bekleyen onay listesini göster
    python main.py --limit 3                 # En fazla 3 burs işle
"""

import argparse
import io
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Windows terminali için UTF-8 zorla
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from colorama import init as colorama_init, Fore, Style
from tabulate import tabulate

import config
from config import loglama_ayarla, dizinleri_olustur, api_anahtarlarini_dogrula
from scraper.base_scraper import HamDuyuru
from scraper.kaynak_yonetici import KaynakYonetici
from ai_analiz import burs_analiz_et, BursAnalizi
from seslendirici import seslendir
from video_olusturucu import video_olustur
from telegram_bot.bot import TelegramOnayBotu
from telegram_bot.onay_yonetici import OnayYonetici

colorama_init(autoreset=True)

# ─────────────────────────────────────────────
# Loglama
# ─────────────────────────────────────────────
loglama_ayarla(log_dosyasi=True)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# İşlenen Burslar Kaydı (Tekrar İşlemeyi Önler)
# ─────────────────────────────────────────────

def islenen_burslari_yukle() -> dict:
    """Daha önce işlenmiş bursları yükler."""
    if config.ISLENEN_BURSLAR_DOSYA.exists():
        try:
            with open(config.ISLENEN_BURSLAR_DOSYA, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"islenen_burslar.json okuma hatası: {e}")
    return {}


def islenen_burslara_ekle(burs_id: str, kayit: dict) -> None:
    """İşlenmiş bursu kayıt dosyasına ekler."""
    mevcut = islenen_burslari_yukle()
    mevcut[burs_id] = {
        **kayit,
        "isleme_zamani": datetime.now().isoformat(),
    }
    with open(config.ISLENEN_BURSLAR_DOSYA, "w", encoding="utf-8") as f:
        json.dump(mevcut, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Tek Burs Pipeline
# ─────────────────────────────────────────────

def burs_isle(
    duyuru: HamDuyuru,
    dry_run: bool = False,
    sadece_video: bool = False,
    telegram_bot: Optional[TelegramOnayBotu] = None,
) -> dict:
    """
    Tek bir burs duyurusunu uçtan uca işler.

    Args:
        duyuru: Ham burs duyurusu
        dry_run: True ise YouTube'a yükleme yapılmaz
        sadece_video: True ise sadece video üretilir
        telegram_bot: Bildirimler için Telegram botu

    Returns:
        İşlem sonucu sözlüğü
    """
    baslangic = time.time()
    burs_id = duyuru.benzersiz_id

    print(f"\n{'═' * 60}")
    print(f"{Fore.CYAN}📋 İŞLENİYOR: {duyuru.kurum_adi} [{burs_id}]{Style.RESET_ALL}")
    print(f"{'═' * 60}")

    sonuc = {
        "burs_id": burs_id,
        "kurum": duyuru.kurum_adi,
        "durum": "bekliyor",
        "hata": None,
        "ses_yolu": None,
        "video_yolu": None,
        "youtube_id": None,
        "youtube_url": None,
    }

    try:
        # ── ADIM 1: AI Analiz
        print(f"\n{Fore.YELLOW}[1/4] 🤖 AI Analiz (Gemini 2.5 Flash)...{Style.RESET_ALL}")
        analiz: BursAnalizi = burs_analiz_et(duyuru.ham_metin, burs_id)

        print(f"     ✅ {Fore.GREEN}{analiz.burs_adi}{Style.RESET_ALL}")
        print(f"        Aylık: {Fore.GREEN}₺{analiz.maddi_tutar.aylik_tl:,}{Style.RESET_ALL} | "
              f"Narrasyon: {len(analiz.narrasyon_metni.split())} kelime")

        # ── ADIM 2: TTS Ses Üretimi
        print(f"\n{Fore.YELLOW}[2/4] 🎙️ TTS Ses Üretimi (AhmetNeural)...{Style.RESET_ALL}")
        ses_yolu, ses_suresi = seslendir(analiz.narrasyon_metni, burs_id)
        sonuc["ses_yolu"] = str(ses_yolu)

        print(f"     ✅ {ses_yolu.name} ({ses_suresi:.1f}s)")

        # ── ADIM 3: Video Oluşturma
        print(f"\n{Fore.YELLOW}[3/4] 🎬 Video Render (Pillow + MoviePy)...{Style.RESET_ALL}")
        video_yolu = video_olustur(analiz, ses_yolu, ses_suresi)
        sonuc["video_yolu"] = str(video_yolu)

        boyut_mb = video_yolu.stat().st_size / (1024 * 1024)
        print(f"     ✅ {video_yolu.name} ({boyut_mb:.1f} MB)")

        # ── ADIM 4: YouTube Yükleme
        if not dry_run and not sadece_video:
            print(f"\n{Fore.YELLOW}[4/4] 📤 YouTube'a Yükleniyor...{Style.RESET_ALL}")

            from youtube_yukleyici import video_yukle
            youtube_id = video_yukle(
                video_yolu=video_yolu,
                burs_adi=analiz.burs_adi,
                kurum=analiz.kurum,
                narrasyon_metni=analiz.narrasyon_metni,
                basvuru_portal=analiz.basvuru_portal,
                basvuru_son_tarih=analiz.basvuru_son_tarih,
                egitim_turu=analiz.egitim_turu,
            )

            if youtube_id:
                sonuc["youtube_id"] = youtube_id
                sonuc["youtube_url"] = f"https://www.youtube.com/shorts/{youtube_id}"
                print(f"     ✅ {Fore.GREEN}https://www.youtube.com/shorts/{youtube_id}{Style.RESET_ALL}")
                if telegram_bot:
                    telegram_bot.video_tamamlandi_bildir(
                        burs_adi=analiz.burs_adi,
                        youtube_url=sonuc["youtube_url"],
                    )
            else:
                logger.warning("YouTube yüklemesi başarısız oldu.")
        else:
            mod = "dry-run" if dry_run else "sadece-video"
            print(f"\n{Fore.MAGENTA}[4/4] ⏭️  YouTube yüklemesi atlandı ({mod} modu){Style.RESET_ALL}")
            if telegram_bot:
                telegram_bot.video_tamamlandi_bildir(
                    burs_adi=analiz.burs_adi,
                    video_yolu=str(video_yolu)
                )

        sure = time.time() - baslangic
        sonuc["durum"] = "basarili"
        sonuc["isleme_suresi_sn"] = round(sure, 1)

        print(f"\n{Fore.GREEN}✅ TAMAMLANDI: {analiz.burs_adi} ({sure:.1f}s){Style.RESET_ALL}")

    except Exception as e:
        sure = time.time() - baslangic
        sonuc["durum"] = "hata"
        sonuc["hata"] = str(e)
        sonuc["isleme_suresi_sn"] = round(sure, 1)

        logger.error(f"❌ Hata — {burs_id}: {e}", exc_info=True)
        print(f"\n{Fore.RED}❌ HATA: {burs_id} — {e}{Style.RESET_ALL}")

    return sonuc


# ─────────────────────────────────────────────
# Ana Fonksiyon
# ─────────────────────────────────────────────

def ana_calis(args: argparse.Namespace) -> None:
    """Ana orkestrasyon fonksiyonu."""

    # Başlık
    print(f"\n{Fore.CYAN}{'━' * 60}")
    print(f"  🎓 BURS OTOMASYONU — YouTube Shorts Fabrikası (Faz 2)")
    print(f"  Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    if args.dry_run:
        print(f"  {Fore.YELLOW}⚠️  DRY-RUN MODU — YouTube yüklemesi yapılmayacak")
    if args.mock:
        print(f"  {Fore.MAGENTA}🧪 MOCK MODU — Test verileri kullanılıyor")
    print(f"{'━' * 60}{Style.RESET_ALL}\n")

    # Dizinleri hazırla
    dizinleri_olustur()

    onay_yonetici = OnayYonetici()

    # Özel mod: Onay bekleyenleri listele
    if args.onay_bekleyenler:
        bekleyenler = onay_yonetici.bekleyenleri_getir()
        print(f"\n{Fore.CYAN}📋 TELEGRAM ONAYI BEKLEYEN BURSLAR ({len(bekleyenler)}){Style.RESET_ALL}")
        if bekleyenler:
            tablo = [[b["burs_id"], b["kurum_adi"], b["eklenme_zamani"][:19], b["kaynak_url"]] for b in bekleyenler]
            print(tabulate(tablo, headers=["ID", "Kurum", "Eklenme", "URL"], tablefmt="rounded_outline"))
        else:
            print("Bekleyen burs yok.")
        return

    # Özel mod: Toplu onayla / reddet
    if args.onayla_hepsi:
        adet = onay_yonetici.toplu_onayla()
        print(f"{Fore.GREEN}✅ {adet} adet burs onaylandı.{Style.RESET_ALL}")
        return
    if args.reddet_hepsi:
        adet = onay_yonetici.toplu_reddet()
        print(f"{Fore.RED}❌ {adet} adet burs reddedildi.{Style.RESET_ALL}")
        return

    # API anahtarlarını doğrula
    youtube_gerekli = not args.dry_run and not getattr(args, "sadece_video", False) and not args.sadece_tara
    if not api_anahtarlarini_dogrula(youtube_gerekli=youtube_gerekli):
        sys.exit(1)

    # Scraper koordinatörü ile bursları topla
    yonetici = KaynakYonetici()
    duyurular = yonetici.tara_ve_topla(
        filtrele_islenmis=not args.zorla,
        mock_kullan=args.mock,
        limit_rss=args.limit_rss
    )

    # Belirli bir ID filtresi var mı?
    if args.burs_id:
        duyurular = [d for d in duyurular if d.benzersiz_id == args.burs_id]
        if not duyurular:
            print(f"{Fore.RED}❌ Belirtilen ID bulunamadı: {args.burs_id}{Style.RESET_ALL}")
            sys.exit(1)
        print(f"{Fore.YELLOW}🎯 Filtre uygulandı: {args.burs_id}{Style.RESET_ALL}")

    # Limit kısıtlaması
    if args.limit and args.limit > 0:
        duyurular = duyurular[:args.limit]
        print(f"{Fore.YELLOW}🔢 Limit uygulandı: En fazla {len(duyurular)} burs işlenecek.{Style.RESET_ALL}")

    if not duyurular:
        print(f"{Fore.GREEN}✨ İşlenecek yeni burs bulunamadı (tümü daha önce işlenmiş).{Style.RESET_ALL}")
        return

    # Yalnızca tarama modu
    if args.sadece_tara:
        print(f"\n{Fore.GREEN}🔎 Tarama tamamlandı. Bulunan burslar:{Style.RESET_ALL}")
        tablo = [[d.benzersiz_id, d.kurum_adi, d.kaynak_adi, d.kaynak_url[:60]] for d in duyurular]
        print(tabulate(tablo, headers=["ID", "Kurum", "Kaynak", "URL"], tablefmt="rounded_outline"))
        return

    # ── Telegram Onay Mekanizması (Mod B: Toplu Onay)
    telegram_bot = TelegramOnayBotu()
    if not args.telegram_devre_disi and telegram_bot.aktif:
        print(f"\n{Fore.CYAN}📲 Telegram üzerinden operatör onayı isteniyor...{Style.RESET_ALL}")
        onay_verildi = telegram_bot.toplu_onay_iste(duyurular, timeout_sn=args.onay_timeout)
        if not onay_verildi:
            print(f"{Fore.RED}❌ Operatör tarafından onaylanmadı veya süre doldu. Pipeline durduruluyor.{Style.RESET_ALL}")
            return
        print(f"{Fore.GREEN}✅ Operatör onayı alındı! Video üretimi başlatılıyor...{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.YELLOW}⚡ Telegram onayı atlandı (Doğrudan üretim modu){Style.RESET_ALL}\n")

    # ── Pipeline Döngüsü
    sonuclar = []
    islenen = islenen_burslari_yukle()

    for i, duyuru in enumerate(duyurular, 1):
        burs_id = duyuru.benzersiz_id

        # Daha önce başarıyla işlendiyse atla (zorla yoksa)
        if burs_id in islenen and islenen[burs_id].get("durum") == "basarili" and not args.zorla:
            print(f"\n{Fore.MAGENTA}⏭️  Atlanıyor (zaten işlendi): {burs_id}{Style.RESET_ALL}")
            continue

        sonuc = burs_isle(
            duyuru=duyuru,
            dry_run=args.dry_run,
            sadece_video=getattr(args, "sadece_video", False),
            telegram_bot=telegram_bot,
        )
        sonuclar.append(sonuc)

        # Başarılı ise kaydet
        if sonuc["durum"] == "basarili":
            islenen_burslara_ekle(burs_id, sonuc)

        # API rate limit ve YouTube quota koruması beklemesi
        if i < len(duyurular) and not args.dry_run:
            bekleme = 10
            print(f"\n⏳ Sonraki burs için {bekleme}s bekleniyor...")
            time.sleep(bekleme)

    # ── Özet Rapor Tablosu
    print(f"\n\n{'═' * 60}")
    print(f"{Fore.CYAN}📊 ÖZET RAPOR{Style.RESET_ALL}")
    print(f"{'═' * 60}")

    if sonuclar:
        tablo_verisi = []
        for s in sonuclar:
            durum_rengi = Fore.GREEN if s["durum"] == "basarili" else Fore.RED
            tablo_verisi.append([
                s["burs_id"],
                s["kurum"],
                f"{durum_rengi}{s['durum'].upper()}{Style.RESET_ALL}",
                s.get("isleme_suresi_sn", "-"),
                s.get("youtube_url") or s.get("video_yolu", "-") or "-",
            ])

        print(tabulate(
            tablo_verisi,
            headers=["Burs ID", "Kurum", "Durum", "Süre(s)", "Çıktı"],
            tablefmt="rounded_outline",
        ))

        basarili = sum(1 for s in sonuclar if s["durum"] == "basarili")
        hatali = len(sonuclar) - basarili
        print(f"\n✅ Başarılı: {basarili}  ❌ Hatalı: {hatali}")
    else:
        print("İşlenen burs bulunamadı.")

    print(f"\n🏁 Tamamlandı: {datetime.now().strftime('%H:%M:%S')}")


# ─────────────────────────────────────────────
# Argüman Parser
# ─────────────────────────────────────────────

def argumanlari_ayarla() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Burs Otomasyonu — YouTube Shorts Fabrikası (Faz 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py                              Tam otonom gerçek tarama + Telegram onayı + YouTube
  python main.py --dry-run --limit 2          Gerçek kaynaklardan 2 burs çek ve yerel video üret
  python main.py --mock --dry-run             Mock veriyle hızlı yerel test
  python main.py --sadece-tara                Yalnızca burs kaynaklarını tara ve listele
  python main.py --telegram-devre-disi        Telegram onayı beklemeden doğrudan üret
  python main.py --onay-bekleyenler           Kuyrukta bekleyen bursları göster
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="YouTube'a yüklemeden pipeline'ı yerel test eder",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Gerçek scraper yerine mock verileri kullanır",
    )
    parser.add_argument(
        "--telegram-devre-disi",
        action="store_true",
        default=False,
        help="Telegram onayını devre dışı bırakır (otomatik onay)",
    )
    parser.add_argument(
        "--sadece-tara",
        action="store_true",
        default=False,
        help="Yalnızca bursları tara ve listele, video üretme",
    )
    parser.add_argument(
        "--sadece-video",
        action="store_true",
        default=False,
        help="Sadece video üret, YouTube'a yükleme yapma",
    )
    parser.add_argument(
        "--onay-bekleyenler",
        action="store_true",
        default=False,
        help="Telegram onayı bekleyen bursları listeler",
    )
    parser.add_argument(
        "--onayla-hepsi",
        action="store_true",
        default=False,
        help="Kuyrukta bekleyen tüm bursları onaylar",
    )
    parser.add_argument(
        "--reddet-hepsi",
        action="store_true",
        default=False,
        help="Kuyrukta bekleyen tüm bursları reddeder",
    )
    parser.add_argument(
        "--id",
        dest="burs_id",
        type=str,
        default=None,
        help="Sadece belirtilen ID'li bursu işle",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="En fazla kaç bursun işleneceğini belirler",
    )
    parser.add_argument(
        "--limit-rss",
        type=int,
        default=5,
        help="RSS kaynağından en fazla kaç burs çekileceği (varsayılan: 5)",
    )
    parser.add_argument(
        "--onay-timeout",
        type=int,
        default=300,
        help="Telegram onay bekleme süresi saniye cinsinden (varsayılan: 300s)",
    )
    parser.add_argument(
        "--zorla",
        action="store_true",
        default=False,
        help="Daha önce işlenmiş bursları yeniden işle",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Detaylı debug çıktısı",
    )

    return parser


# ─────────────────────────────────────────────
# Giriş Noktası
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argumanlari_ayarla()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        ana_calis(args)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Kullanıcı tarafından durduruldu.{Style.RESET_ALL}")
        sys.exit(0)
