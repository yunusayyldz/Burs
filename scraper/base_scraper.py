"""
scraper/base_scraper.py — Soyut temel scraper sınıfı
Faz 2'de gerçek scraper implementasyonları buradan türeyecek.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class HamDuyuru:
    """
    Bir burs kaynağından çekilen ham duyuru verisi.
    8 kriterli analiz için ai_analiz.py'ye gönderilir.
    """
    kaynak_url: str                        # Duyurunun orijinal URL'i
    kurum_adi: str                         # Burs veren kurum adı
    ham_metin: str                         # Parse edilmemiş duyuru metni
    cekilis_zamani: datetime = field(default_factory=datetime.now)
    benzersiz_id: str = ""                 # URL hash veya özel ID
    kaynak_adi: str = ""                   # Hangi scraper çekti (ör. "tbb_rss")

    def __post_init__(self):
        if not self.benzersiz_id:
            import hashlib
            self.benzersiz_id = hashlib.md5(
                (self.kaynak_url + self.ham_metin[:100]).encode()
            ).hexdigest()[:12]


class BaseScraper(ABC):
    """
    Tüm burs scraper'larının implement etmesi gereken arayüz.
    
    Kullanım:
        class TBBScraper(BaseScraper):
            def fetch_duyurular(self) -> List[HamDuyuru]:
                ...
    """

    # Alt sınıflar bu listeyi override etmelidir
    kaynak_adi: str = "base"
    kaynak_url: str = ""

    @abstractmethod
    def fetch_duyurular(self) -> List[HamDuyuru]:
        """
        Burs duyurularını kaynaktan çeker.
        
        Returns:
            HamDuyuru nesnelerinin listesi.
            Her nesne bağımsız bir burs programına karşılık gelir.
            Aynı kurumun birden fazla bursu varsa, her biri ayrı HamDuyuru nesnesi olmalıdır!
        """
        raise NotImplementedError

    def kaynagi_kontrol_et(self) -> bool:
        """
        Kaynağın erişilebilir olup olmadığını test eder.
        Varsayılan implementasyon basit bir HTTP GET dener.
        """
        import requests
        try:
            r = requests.get(self.kaynak_url, timeout=10)
            return r.status_code == 200
        except Exception:
            return False
