"""
scraper/rss_scraper.py — RSS / Atom Feed Scraper
feedparser tabanlı genel RSS okuyucu ve burs duyurusu filtreleyici.
"""

import logging
import hashlib
from typing import List, Optional
import feedparser
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

BURS_ANAHTAR_KELIMELER = [
    "burs", "bursu", "burslar", "bursiyer", "bursiyeri",
    "burs başvurusu", "karşılıksız burs", "öğrenci bursu",
    "eğitim bursu", "lisans bursu", "yüksek lisans bursu"
]


class RSSScraper(BaseScraper):
    """Genel RSS ve Atom beslemelerini okuyarak burs duyurularını süzen scraper."""

    kaynak_adi = "RSS Beslemesi"
    kaynak_url = "https://news.google.com/rss/search?q=üniversite+burs+başvuruları+when:7d&hl=tr&gl=TR&ceid=TR:tr"

    def __init__(self, rss_url: Optional[str] = None, kaynak_adi: str = "RSS Beslemesi"):
        if rss_url:
            self.kaynak_url = rss_url
        self.kaynak_adi = kaynak_adi

    def _burs_ile_ilgili_mi(self, baslik: str, ozet: str) -> bool:
        """Başlık veya özette burs ile ilgili anahtar kelimeler geçiyor mu?"""
        metin = f"{baslik} {ozet}".lower()
        return any(kelime in metin for kelime in BURS_ANAHTAR_KELIMELER)

    def fetch_duyurular(self) -> List[HamDuyuru]:
        """RSS kaynağından duyuruları çeker ve HamDuyuru nesnelerine dönüştürür."""
        duyurular: List[HamDuyuru] = []
        logger.info(f"📡 RSS beslemesi taranıyor: {self.kaynak_url}")

        try:
            feed = feedparser.parse(
                self.kaynak_url,
                agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            if feed.bozo and not feed.entries:
                logger.warning(f"⚠️ RSS parse uyarısı / hatası: {feed.get('bozo_exception', 'Bilinmeyen hata')}")
                return duyurular

            for entry in feed.entries:
                baslik = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                ozet = getattr(entry, "summary", "").strip()
                if not ozet:
                    ozet = getattr(entry, "description", "").strip()

                if not baslik or not link:
                    continue

                if not self._burs_ile_ilgili_mi(baslik, ozet):
                    continue

                # Temiz ham metin oluştur
                ham_metin = f"Başlık: {baslik}\nÖzet: {ozet}\nKaynak Bağlantı: {link}"
                benzersiz_id = "rss_" + hashlib.md5(link.encode()).hexdigest()[:10]

                # Kurum adını başlık veya kaynaktan kestir
                kaynak_bilgisi = getattr(entry, "source", {})
                kurum_adi = kaynak_bilgisi.get("title", "RSS Burs Duyurusu") if isinstance(kaynak_bilgisi, dict) else "RSS Burs Duyurusu"

                duyurular.append(
                    HamDuyuru(
                        kaynak_url=link,
                        kurum_adi=kurum_adi,
                        ham_metin=ham_metin,
                        benzersiz_id=benzersiz_id,
                        kaynak_adi=self.kaynak_adi
                    )
                )

            logger.info(f"✅ RSS kaynağından {len(duyurular)} adet burs duyurusu bulundu.")
        except Exception as e:
            logger.error(f"❌ RSS Scraper hatası ({self.kaynak_url}): {e}")

        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = RSSScraper()
    sonuclar = scraper.fetch_duyurular()
    print(f"Toplam {len(sonuclar)} duyuru bulundu.")
    for d in sonuclar[:3]:
        print(f"\n- Kurum: {d.kurum_adi}\n  URL: {d.kaynak_url}\n  ID: {d.benzersiz_id}")
