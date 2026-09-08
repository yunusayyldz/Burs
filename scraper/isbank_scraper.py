"""
scraper/isbank_scraper.py — Türkiye İş Bankası Burs ve Eğitim Destekleri Scraper'ı
İş Bankası'nın Altın Gençler ve Darüşşafaka ortaklı burs programlarını
bağımsız HamDuyuru nesneleri olarak ayrıştırır.
"""

import logging
import hashlib
from typing import List
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

ISBANK_BASE = "https://www.isbank.com.tr"
EGITIM_URL = f"{ISBANK_BASE}/bankamizi-taniyin/egitim"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class IsBankasiScraper(BaseScraper):
    """Türkiye İş Bankası eğitim ve başarı bursu programlarını çeken scraper."""

    kaynak_adi = "Türkiye İş Bankası"
    kaynak_url = EGITIM_URL

    def fetch_duyurular(self) -> List[HamDuyuru]:
        duyurular: List[HamDuyuru] = []
        logger.info(f"🔍 İş Bankası eğitim projeleri taranıyor: {self.kaynak_url}")

        hedef_programlar = [
            {
                "ad": "İş Bankası Altın Gençler Burs ve Başarı Ödülü",
                "url": f"{ISBANK_BASE}/bankamizi-taniyin/altin-gencler",
                "kod": "altin_gencler"
            },
            {
                "ad": "İş Bankası 81 İlden 81 Öğrenci Tam Burs Projesi",
                "url": f"{ISBANK_BASE}/bankamizi-taniyin/81-ilden-81-ogrenci",
                "kod": "81_il_81_ogrenci"
            }
        ]

        for prog in hedef_programlar:
            try:
                url = prog["url"]
                logger.info(f"   ↳ İş Bankası programı çekiliyor: {prog['ad']}")
                r = requests.get(url, headers=HEADERS, timeout=12)
                
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    
                    icerik = soup.get_text(separator="\n", strip=True)
                    ham_metin = (
                        f"Burs Programı: {prog['ad']}\n"
                        f"Kurum: Türkiye İş Bankası\n"
                        f"Detay Sayfası: {url}\n\n"
                        f"Program Bilgileri:\n{icerik[:3500]}"
                    )
                else:
                    ham_metin = (
                        f"Burs Programı: {prog['ad']}\n"
                        f"Kurum: Türkiye İş Bankası\n"
                        f"Detay Sayfası: {url}"
                    )

                benzersiz_id = "isbank_" + hashlib.md5(prog["kod"].encode()).hexdigest()[:10]
                duyurular.append(
                    HamDuyuru(
                        kaynak_url=url,
                        kurum_adi="Türkiye İş Bankası",
                        ham_metin=ham_metin,
                        benzersiz_id=benzersiz_id,
                        kaynak_adi=self.kaynak_adi
                    )
                )
            except Exception as ex:
                logger.warning(f"⚠️ İş Bankası çekme hatası ({prog['ad']}): {ex}")

        logger.info(f"✅ Türkiye İş Bankası kaynağından {len(duyurular)} adet burs programı ayrıştırıldı.")
        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = IsBankasiScraper()
    burslar = scraper.fetch_duyurular()
    print(f"\nİş Bankası'ndan toplam {len(burslar)} burs çekildi:")
    for b in burslar:
        print(f"- {b.benzersiz_id}: {b.kaynak_url}")
