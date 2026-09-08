"""
scraper/sabanci_scraper.py — Sabancı Vakfı Burs Scraper'ı
Sabancı Vakfı'nın burs programlarını (Üniversiteye Giriş Bursu, Kalkınmada Öncelikli İller Bursu,
Engelli Öğrenciler Bursu) bağımsız HamDuyuru nesneleri olarak ayrıştırır.
Resilient HTTP & curl desteği içerir.
"""

import logging
import hashlib
import subprocess
from typing import List
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

SABANCI_BASE = "https://www.sabancivakfi.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _sayfa_getir(url: str, timeout: int = 12) -> str:
    """Önce requests dener, SSL veya ağ hatası olursa curl fallback kullanır."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass

    # curl fallback
    try:
        res = subprocess.run(
            ["curl.exe", "-s", "-L", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout + 5
        )
        if res.returncode == 0 and res.stdout:
            return res.stdout
    except Exception as e:
        logger.warning(f"⚠️ curl fallback hatası ({url}): {e}")

    return ""


class SabanciScraper(BaseScraper):
    """Sabancı Vakfı burs programlarını çeken scraper."""

    kaynak_adi = "Sabancı Vakfı"
    kaynak_url = f"{SABANCI_BASE}/burslar"

    def fetch_duyurular(self) -> List[HamDuyuru]:
        duyurular: List[HamDuyuru] = []
        logger.info(f"🔍 Sabancı Vakfı bursları taranıyor: {self.kaynak_url}")

        programlar = [
            {
                "ad": "Sabancı Vakfı - Üniversiteye Giriş Bursu",
                "url": f"{SABANCI_BASE}/tr/burslarinfo/universiteye-giris-bursu",
                "kod": "universiteye_giris"
            },
            {
                "ad": "Sabancı Vakfı - Kalkınmada Öncelikli İller Bursu",
                "url": f"{SABANCI_BASE}/tr/burslarinfo/diger-burslar",
                "kod": "kalkinmada_oncelikli_iller"
            },
            {
                "ad": "Sabancı Vakfı - Engelli Öğrenciler Burs Programı",
                "url": f"{SABANCI_BASE}/tr/burslarinfo/diger-burslar",
                "kod": "engelli_ogrenciler"
            }
        ]

        for prog in programlar:
            try:
                url = prog["url"]
                logger.info(f"   ↳ Sabancı programı çekiliyor: {prog['ad']}")
                html = _sayfa_getir(url)

                if html:
                    soup = BeautifulSoup(html, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    icerik = soup.get_text(separator="\n", strip=True)
                    ham_metin = (
                        f"Burs Programı: {prog['ad']}\n"
                        f"Kurum: Sabancı Vakfı\n"
                        f"Kaynak: {url}\n\n"
                        f"Detaylar ve Koşullar:\n{icerik[:3500]}"
                    )
                else:
                    ham_metin = (
                        f"Burs Programı: {prog['ad']}\n"
                        f"Kurum: Sabancı Vakfı\n"
                        f"Kaynak: {url}"
                    )

                benzersiz_id = "sabanci_" + hashlib.md5(prog["kod"].encode()).hexdigest()[:10]
                duyurular.append(
                    HamDuyuru(
                        kaynak_url=url,
                        kurum_adi="Sabancı Vakfı",
                        ham_metin=ham_metin,
                        benzersiz_id=benzersiz_id,
                        kaynak_adi=self.kaynak_adi
                    )
                )
            except Exception as ex:
                logger.warning(f"⚠️ Sabancı çekme hatası ({prog['ad']}): {ex}")

        logger.info(f"✅ Sabancı Vakfı kaynağından {len(duyurular)} adet burs programı ayrıştırıldı.")
        return duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SabanciScraper()
    burslar = scraper.fetch_duyurular()
    print(f"\nSabancı Vakfı'ndan toplam {len(burslar)} burs çekildi:")
    for b in burslar:
        print(f"- {b.benzersiz_id}: {b.kaynak_url}")
