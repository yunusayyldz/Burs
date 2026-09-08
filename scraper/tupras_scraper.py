"""
scraper/tupras_scraper.py — TÜPRAŞ Burs ve Sosyal Sorumluluk Programları Scraper'ı
TÜPRAŞ Mühendislik ve Teknoloji Burs Programı duyurularını HamDuyuru nesnelerine dönüştürür.
"""

import logging
import hashlib
from typing import List
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

TUPRAS_BASE = "https://www.tupras.com.tr"
YATIRIMLAR_URL = f"{TUPRAS_BASE}/toplumsal-yatirimlar-ve-sponsorluklarimiz"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class TuprasScraper(BaseScraper):
    """TÜPRAŞ burs ve eğitim desteği programlarını çeken scraper."""

    kaynak_adi = "TÜPRAŞ"
    kaynak_url = YATIRIMLAR_URL

    def fetch_duyurular(self) -> List[HamDuyuru]:
        duyurular: List[HamDuyuru] = []
        logger.info(f"🔍 TÜPRAŞ burs ve sosyal yatırımlar taranıyor: {self.kaynak_url}")

        programlar = [
            {
                "ad": "TÜPRAŞ - TEV Mühendislik ve Teknoloji Lisans Burs Programı",
                "detay": (
                    "TÜPRAŞ, Türk Eğitim Vakfı (TEV) iş birliğiyle mühendislik ve fen fakültelerinde "
                    "eğitim gören başarılı lisans öğrencilerine karşılıksız eğitim bursu, staj imkanı "
                    "ve mentorluk desteği sağlamaktadır. Burs süresi 9-10 ay olup her ay düzenli nakdi ödeme yapılır."
                ),
                "kod": "tupras_tev_muhendislik"
            }
        ]

        try:
            r = requests.get(self.kaynak_url, headers=HEADERS, timeout=12)
            ek_icerik = ""
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                ek_icerik = soup.get_text(separator="\n", strip=True)[:1500]

            for prog in programlar:
                ham_metin = (
                    f"Burs Programı: {prog['ad']}\n"
                    f"Kurum: TÜPRAŞ (Türkiye Petrol Rafinerileri A.Ş.) & TEV İş Birliği\n"
                    f"Kaynak URL: {self.kaynak_url}\n\n"
                    f"Açıklama ve Şartlar:\n{prog['detay']}\n\n"
                    f"Kurumsal Bilgi:\n{ek_icerik}"
                )

                benzersiz_id = "tupras_" + hashlib.md5(prog["kod"].encode()).hexdigest()[:10]
                duyurular.append(
                    HamDuyuru(
                        kaynak_url=self.kaynak_url,
                        kurum_adi="TÜPRAŞ",
                        ham_metin=ham_metin,
                        benzersiz_id=benzersiz_id,
                        kaynak_adi=self.kaynak_adi
                    )
                )

            logger.info(f"✅ TÜPRAŞ kaynağından {len(duyurular)} adet burs programı çıkarıldı.")
        except Exception as e:
            logger.error(f"❌ TÜPRAŞ Scraper hatası: {e}")

        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = TuprasScraper()
    burslar = scraper.fetch_duyurular()
    print(f"\nTÜPRAŞ'tan toplam {len(burslar)} burs çekildi:")
    for b in burslar:
        print(f"- {b.benzersiz_id}: {b.kaynak_url}")
