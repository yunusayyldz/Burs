"""
scraper/kaynak_yonetici.py — Scraper Koordinatörü ve Kaynak Yöneticisi
Tüm aktif burs kaynaklarını sırayla çalıştırır, sonuçları toplar,
tekilleştirir ve daha önce işlenmiş bursları filtreler.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Type
import config
from scraper.base_scraper import BaseScraper, HamDuyuru
from scraper.tev_scraper import TEVScraper
from scraper.turkiyeburslari_scraper import TurkiyeBurslariScraper
from scraper.isbank_scraper import IsBankasiScraper
from scraper.sabanci_scraper import SabanciScraper
from scraper.tupras_scraper import TuprasScraper
from scraper.ayb_scraper import AYBScraper
from scraper.rss_scraper import RSSScraper
from scraper.mock_scraper import MockScraper

logger = logging.getLogger(__name__)

KAYITLI_SCRAPERS: Dict[str, Type[BaseScraper]] = {
    "tev": TEVScraper,
    "turkiyeburslari": TurkiyeBurslariScraper,
    "isbank": IsBankasiScraper,
    "sabanci": SabanciScraper,
    "tupras": TuprasScraper,
    "ayb": AYBScraper,
    "rss_haberler": RSSScraper,
}


class KaynakYonetici:
    """Tüm aktif burs kaynaklarını koordine eden merkezi yönetici."""

    def __init__(self, kaynaklar_dosyasi: Path = config.KAYNAKLAR_DOSYA):
        self.kaynaklar_dosyasi = kaynaklar_dosyasi
        self.kaynak_ayarlari = self._kaynak_ayarlarini_yukle()

    def _kaynak_ayarlarini_yukle(self) -> dict:
        """veriler/kaynaklar.json dosyasından yapılandırmayı okur."""
        if self.kaynaklar_dosyasi.exists():
            try:
                with open(self.kaynaklar_dosyasi, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ kaynaklar.json okunamadı ({e}), varsayılan ayarlar kullanılıyor.")
        return {}

    def _islenmis_idleri_getir(self) -> set:
        """Daha önce işlenmiş bursların ID kümesini döndürür."""
        if config.ISLENEN_BURSLAR_DOSYA.exists():
            try:
                with open(config.ISLENEN_BURSLAR_DOSYA, "r", encoding="utf-8") as f:
                    veriler = json.load(f)
                    return set(veriler.keys())
            except Exception as e:
                logger.warning(f"⚠️ islenen_burslar.json okuma hatası: {e}")
        return set()

    def tara_ve_topla(
        self,
        filtrele_islenmis: bool = True,
        mock_kullan: bool = False,
        limit_rss: int = 15,
    ) -> List[HamDuyuru]:
        """
        Tüm aktif scraper'ları çalıştırıp toplanan burs duyurularını döndürür.

        Args:
            filtrele_islenmis: True ise daha önce işlenmiş bursları eler
            mock_kullan: True ise sadece mock scraper kullanılır
            limit_rss: RSS kaynağından en fazla kaç burs alınacağı

        Returns:
            List[HamDuyuru]: İşlenmeye hazır ham duyuru nesneleri
        """
        if mock_kullan:
            logger.info("🧪 Mock modu aktif: Yalnızca MockScraper çalıştırılıyor.")
            mock_scraper = MockScraper()
            duyurular = mock_scraper.fetch_duyurular()
            if filtrele_islenmis:
                islenmis_idleri = self._islenmis_idleri_getir()
                duyurular = [d for d in duyurular if d.benzersiz_id not in islenmis_idleri]
            return duyurular

        toplanan_duyurular: List[HamDuyuru] = []
        islenmis_idleri = self._islenmis_idleri_getir() if filtrele_islenmis else set()
        gorulen_idleri = set()

        # Kaynak yapılandırmasını kontrol et
        kaynak_listesi = self.kaynak_ayarlari.get("kaynaklar", [])
        
        # Eğer kaynaklar.json boşsa veya bulunamadıysa varsayılan listeyi kullan
        if not kaynak_listesi:
            kaynak_listesi = [{"id": k_id, "aktif": True} for k_id in KAYITLI_SCRAPERS.keys()]

        logger.info(f"🚀 Toplam {len(kaynak_listesi)} kaynak için tarama başlatılıyor...")

        for k_bilgi in kaynak_listesi:
            k_id = k_bilgi.get("id")
            aktif = k_bilgi.get("aktif", True)

            if not aktif:
                logger.info(f"⏸️ Kaynak pasif: {k_id}")
                continue

            scraper_sinif = KAYITLI_SCRAPERS.get(k_id)
            if not scraper_sinif:
                logger.warning(f"⚠️ Bilinmeyen scraper ID: {k_id}")
                continue

            try:
                logger.info(f"⏳ [{k_id.upper()}] taranıyor...")
                scraper_obj = scraper_sinif()
                duyurular = scraper_obj.fetch_duyurular()

                # RSS ise adet sınırla
                if k_id == "rss_haberler" and limit_rss > 0:
                    duyurular = duyurular[:limit_rss]

                yeni_sayac = 0
                for d in duyurular:
                    if d.benzersiz_id in gorulen_idleri:
                        continue
                    if filtrele_islenmis and d.benzersiz_id in islenmis_idleri:
                        logger.debug(f"Zaten işlenmiş: {d.benzersiz_id}")
                        continue

                    gorulen_idleri.add(d.benzersiz_id)
                    toplanan_duyurular.append(d)
                    yeni_sayac += 1

                logger.info(f"   ↳ {k_id.upper()}: {len(duyurular)} duyurudan {yeni_sayac} tanesi yeni eklendi.")
            except Exception as e:
                logger.error(f"❌ Scraper hatası [{k_id}]: {e}", exc_info=False)

        logger.info(
            f"🎉 Tarama tamamlandı! Toplam {len(toplanan_duyurular)} adet yeni/işlenebilir burs duyurusu toplandı."
        )
        return toplanan_duyurular


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    yonetici = KaynakYonetici()
    sonuclar = yonetici.tara_ve_topla(filtrele_islenmis=False, limit_rss=5)
    print(f"\n{'='*60}")
    print(f"Toplam Çekilen Duyuru Sayısı: {len(sonuclar)}")
    print(f"{'='*60}")
    for idx, d in enumerate(sonuclar, 1):
        print(f"[{idx:02d}] {d.kurum_adi:<30} | {d.benzersiz_id:<18} | {d.kaynak_url}")
