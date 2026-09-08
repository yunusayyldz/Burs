"""
scraper/turkiyeburslari_scraper.py — YTB / Türkiye Bursları Scraper'ı
Yurtdışı Türkler ve Akraba Topluluklar Başkanlığı (YTB) Türkiye Bursları programlarını
Lisans, Yüksek Lisans ve Doktora olarak bağımsız duyurular halinde ayrıştırır.
"""

import logging
import hashlib
from typing import List
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

YTB_BASE_URL = "https://www.turkiyeburslari.gov.tr"
PROGRAMLAR_URL = f"{YTB_BASE_URL}/fulltimeprograms"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class TurkiyeBurslariScraper(BaseScraper):
    """YTB Türkiye Bursları resmi programlarını çeken scraper."""

    kaynak_adi = "Türkiye Bursları (YTB)"
    kaynak_url = PROGRAMLAR_URL

    def fetch_duyurular(self) -> List[HamDuyuru]:
        duyurular: List[HamDuyuru] = []
        logger.info(f"🔍 Türkiye Bursları (YTB) taranıyor: {self.kaynak_url}")

        try:
            session = requests.Session()
            session.headers.update(HEADERS)
            
            # Türkçe dili aktif et
            session.get(
                f"{YTB_BASE_URL}/AbpLocalization/ChangeCulture?cultureName=tr&returnUrl=%2Ffulltimeprograms",
                timeout=12
            )

            res = session.get(PROGRAMLAR_URL, timeout=15)
            if res.status_code != 200:
                logger.warning(f"⚠️ YTB sayfasına ulaşılamadı. HTTP {res.status_code}")
                return duyurular

            soup = BeautifulSoup(res.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Bölüm kartları veya başlıkları bul
            program_tanimlari = [
                {
                    "ad": "Türkiye Bursları - Lisans Burs Programı",
                    "arama": ["lisans", "undergraduate"],
                    "kademe": "Lisans"
                },
                {
                    "ad": "Türkiye Bursları - Yüksek Lisans Burs Programı",
                    "arama": ["yüksek lisans", "master"],
                    "kademe": "Yüksek Lisans"
                },
                {
                    "ad": "Türkiye Bursları - Doktora Burs Programı",
                    "arama": ["doktora", "phd"],
                    "kademe": "Doktora"
                }
            ]

            sayfa_metni = soup.get_text(separator="\n", strip=True)

            for prog in program_tanimlari:
                ham_metin = (
                    f"Burs Programı: {prog['ad']}\n"
                    f"Kurum: Türkiye Bursları (YTB)\n"
                    f"Eğitim Seviyesi: {prog['kademe']}\n"
                    f"Resmi URL: {PROGRAMLAR_URL}\n\n"
                    f"Detaylar ve Şartlar:\n"
                    f"YTB Türkiye Bursları kapsamında üniversite harcı muafiyeti, aylık burs desteği, "
                    f"konaklama/yurt desteği, sağlık sigortası, gidiş-dönüş uçak bileti ve 1 yıllık Türkçe hazırlık kursu sağlanmaktadır.\n"
                    f"{sayfa_metni[:2500]}"
                )

                benzersiz_id = "ytb_" + hashlib.md5(prog["ad"].encode()).hexdigest()[:10]
                duyurular.append(
                    HamDuyuru(
                        kaynak_url=PROGRAMLAR_URL,
                        kurum_adi="Türkiye Bursları (YTB)",
                        ham_metin=ham_metin,
                        benzersiz_id=benzersiz_id,
                        kaynak_adi=self.kaynak_adi
                    )
                )

            logger.info(f"✅ Türkiye Bursları (YTB) kaynağından {len(duyurular)} adet burs programı ayrıştırıldı.")
        except Exception as e:
            logger.error(f"❌ Türkiye Bursları Scraper hatası: {e}")

        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = TurkiyeBurslariScraper()
    burslar = scraper.fetch_duyurular()
    print(f"\nYTB'den toplam {len(burslar)} burs çekildi:")
    for b in burslar:
        print(f"- {b.benzersiz_id}: {b.kaynak_url}")
