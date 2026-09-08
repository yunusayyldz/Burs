"""
scraper/ayb_scraper.py — Anadolu Vakfı (Anadolu Grubu) Burs Scraper'ı
Anadolu Vakfı yükseköğrenim burs programı şartlarını ve duyurularını
ayrıştırarak HamDuyuru nesnesine dönüştürür.
"""

import logging
import hashlib
from typing import List
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

ANADOLU_BASE = "https://www.anadoluvakfi.org.tr"
KAPSAM_URL = f"{ANADOLU_BASE}/egitim/burs-programi-kapsami"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class AYBScraper(BaseScraper):
    """Anadolu Eğitim ve Sosyal Yardım Vakfı burslarını çeken scraper."""

    kaynak_adi = "Anadolu Vakfı"
    kaynak_url = KAPSAM_URL

    def fetch_duyurular(self) -> List[HamDuyuru]:
        duyurular: List[HamDuyuru] = []
        logger.info(f"🔍 Anadolu Vakfı burs programı taranıyor: {self.kaynak_url}")

        try:
            r = requests.get(self.kaynak_url, headers=HEADERS, timeout=12)
            metin = ""
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                metin = soup.get_text(separator="\n", strip=True)

            ham_metin = (
                "Burs Programı: Anadolu Vakfı Yükseköğrenim Lisans Bursu\n"
                "Kurum: Anadolu Eğitim ve Sosyal Yardım Vakfı\n"
                f"Resmi URL: {self.kaynak_url}\n"
                "Başvuru Portalı: https://basvuru.anadoluvakfi.org.tr\n\n"
                f"Program Detayları:\n{metin[:3500]}"
            )

            benzersiz_id = "ayb_" + hashlib.md5("anadolu_vakfi_lisans".encode()).hexdigest()[:10]
            duyurular.append(
                HamDuyuru(
                    kaynak_url=self.kaynak_url,
                    kurum_adi="Anadolu Vakfı",
                    ham_metin=ham_metin,
                    benzersiz_id=benzersiz_id,
                    kaynak_adi=self.kaynak_adi
                )
            )

            logger.info(f"✅ Anadolu Vakfı kaynağından {len(duyurular)} adet burs duyurusu çıkarıldı.")
        except Exception as e:
            logger.error(f"❌ Anadolu Vakfı Scraper hatası: {e}")

        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = AYBScraper()
    burslar = scraper.fetch_duyurular()
    print(f"\nAnadolu Vakfı'ndan toplam {len(burslar)} burs çekildi:")
    for b in burslar:
        print(f"- {b.benzersiz_id}: {b.kaynak_url}")
