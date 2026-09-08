"""
scraper/tev_scraper.py — Türk Eğitim Vakfı (TEV) Burs Scraper'ı
TEV web sitesindeki burs programlarını tek tek ayrıştırıp HamDuyuru nesnelerine dönüştürür.
Ayrıştırma Kuralı: Lisans, Yüksek Lisans, Üstün Başarı vb. her biri bağımsız birer duyurudur.
"""

import logging
import hashlib
from typing import List
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

TEV_ANA_SAYFA = "https://www.tev.org.tr"
TEV_BURS_SAYFASI = "https://www.tev.org.tr/burs/tr"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


class TEVScraper(BaseScraper):
    """Türk Eğitim Vakfı (TEV) resmi burs duyurularını çeken scraper."""

    kaynak_adi = "Türk Eğitim Vakfı (TEV)"
    kaynak_url = TEV_BURS_SAYFASI

    def fetch_duyurular(self) -> List[HamDuyuru]:
        duyurular: List[HamDuyuru] = []
        logger.info(f"🔍 TEV burs sayfası taranıyor: {self.kaynak_url}")

        try:
            r = requests.get(self.kaynak_url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                logger.warning(f"⚠️ TEV sayfasına ulaşılamadı. HTTP {r.status_code}")
                return duyurular

            soup = BeautifulSoup(r.text, "html.parser")
            burs_linkleri = []

            # Burs programı linklerini tespit et
            for a in soup.find_all("a", href=True):
                href = a["href"]
                baslik = a.get_text(strip=True)
                if any(x in href for x in ["/Mesleki-Ortaogretim-Bursu", "/Universite-Egitim-Bursu", 
                                           "/Yuksek-Lisans-ve-Doktora-Basari-Bursu", "/Ustun-Basari-Bursu", 
                                           "/Ustun-Basari-Sanat-Bursu"]) or \
                   any(x in baslik.lower() for x in ["lisans bursu", "eğitim bursu", "üstün başarı bursu", "doktora başarı bursu"]):
                    
                    tam_url = urljoin(self.kaynak_url, href)
                    if (baslik, tam_url) not in burs_linkleri and baslik:
                        burs_linkleri.append((baslik, tam_url))

            # Her bir burs programının detay sayfasına git ve bağımsız HamDuyuru oluştur
            for baslik, url in burs_linkleri:
                try:
                    logger.info(f"   ↳ TEV Programı çekiliyor: {baslik} ({url})")
                    detay_res = requests.get(url, headers=HEADERS, timeout=12)
                    if detay_res.status_code == 200:
                        detay_soup = BeautifulSoup(detay_res.text, "html.parser")
                        # Gereksiz script, style, nav, footer temizle
                        for tag in detay_soup(["script", "style", "nav", "footer", "header"]):
                            tag.decompose()

                        icerik_div = detay_soup.find("main") or detay_soup.find("article") or detay_soup.find("div", class_="content") or detay_soup.body
                        metin = icerik_div.get_text(separator="\n", strip=True) if icerik_div else detay_soup.get_text(strip=True)
                        
                        # Metni çok uzatmamak için makul sınırda kes veya tamamını al
                        ham_metin = f"Burs Adı: TEV {baslik}\nKurum: Türk Eğitim Vakfı (TEV)\nDetay Sayfası: {url}\n\nİçerik:\n{metin[:4000]}"
                    else:
                        ham_metin = f"Burs Adı: TEV {baslik}\nKurum: Türk Eğitim Vakfı (TEV)\nDetay Sayfası: {url}"

                    benzersiz_id = "tev_" + hashlib.md5(url.encode()).hexdigest()[:10]
                    duyurular.append(
                        HamDuyuru(
                            kaynak_url=url,
                            kurum_adi="Türk Eğitim Vakfı (TEV)",
                            ham_metin=ham_metin,
                            benzersiz_id=benzersiz_id,
                            kaynak_adi=self.kaynak_adi
                        )
                    )
                except Exception as ex:
                    logger.warning(f"⚠️ TEV detay çekme hatası ({baslik}): {ex}")

            logger.info(f"✅ TEV kaynağından {len(duyurular)} adet bağımsız burs duyurusu çıkarıldı.")
        except Exception as e:
            logger.error(f"❌ TEV Scraper genel hatası: {e}")

        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = TEVScraper()
    burslar = scraper.fetch_duyurular()
    print(f"\nTEV'den toplam {len(burslar)} burs çekildi:")
    for b in burslar:
        print(f"- {b.benzersiz_id}: {b.kaynak_url}")
