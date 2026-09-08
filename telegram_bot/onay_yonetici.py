"""
telegram_bot/onay_yonetici.py — Telegram Onay Durum Yöneticisi
Onay bekleyen, onaylanan veya reddedilen burs duyurularını
veriler/onay_bekleyenler.json dosyasında güvenli biçimde takip eder.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import config

logger = logging.getLogger(__name__)


class OnayYonetici:
    """Burs duyurularının onay süreçlerini persist eden yönetici sınıf."""

    def __init__(self, dosya_yolu: Path = config.ONAY_BEKLEYENLER_DOSYA):
        self.dosya_yolu = dosya_yolu
        self._dosya_hazirla()

    def _dosya_hazirla(self) -> None:
        """Gerekiyorsa veriler dizinini ve json dosyasını oluşturur."""
        self.dosya_yolu.parent.mkdir(parents=True, exist_ok=True)
        if not self.dosya_yolu.exists():
            self._kaydet({})

    def _yukle(self) -> Dict[str, dict]:
        """Kayıtlı durumu okur."""
        try:
            if self.dosya_yolu.exists():
                with open(self.dosya_yolu, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Onay kayıtları yüklenirken hata: {e}")
        return {}

    def _kaydet(self, veriler: Dict[str, dict]) -> None:
        """Kayıtları dosyaya yazar."""
        try:
            with open(self.dosya_yolu, "w", encoding="utf-8") as f:
                json.dump(veriler, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Onay kayıtları kaydedilirken hata: {e}")

    def bekleyen_ekle(
        self,
        burs_id: str,
        kurum_adi: str,
        kaynak_url: str,
        ozet: str = "",
        kaynak_adi: str = ""
    ) -> None:
        """Onay kuyruğuna yeni bir burs ekler."""
        veriler = self._yukle()
        if burs_id not in veriler:
            veriler[burs_id] = {
                "burs_id": burs_id,
                "kurum_adi": kurum_adi,
                "kaynak_url": kaynak_url,
                "kaynak_adi": kaynak_adi,
                "ozet": ozet[:300],
                "durum": "bekliyor",  # bekliyor / onaylandi / reddedildi
                "eklenme_zamani": datetime.now().isoformat(),
                "guncelleme_zamani": None
            }
            self._kaydet(veriler)
            logger.info(f"📥 Onay kuyruğuna eklendi: {burs_id} ({kurum_adi})")

    def bekleyenleri_getir(self) -> List[dict]:
        """Yalnızca 'bekliyor' durumundaki bursları listeler."""
        veriler = self._yukle()
        return [v for v in veriler.values() if v.get("durum") == "bekliyor"]

    def durum_guncelle(self, burs_id: str, yeni_durum: str) -> bool:
        """Belirtilen bursun durumunu ('onaylandi' / 'reddedildi') günceller."""
        veriler = self._yukle()
        if burs_id in veriler:
            veriler[burs_id]["durum"] = yeni_durum
            veriler[burs_id]["guncelleme_zamani"] = datetime.now().isoformat()
            self._kaydet(veriler)
            logger.info(f"🔄 Burs onay durumu güncellendi: {burs_id} -> {yeni_durum}")
            return True
        return False

    def toplu_onayla(self) -> int:
        """Bekleyen tüm bursları tek seferde 'onaylandi' yapar."""
        veriler = self._yukle()
        sayac = 0
        zaman = datetime.now().isoformat()
        for b in veriler.values():
            if b.get("durum") == "bekliyor":
                b["durum"] = "onaylandi"
                b["guncelleme_zamani"] = zaman
                sayac += 1
        self._kaydet(veriler)
        logger.info(f"✅ {sayac} adet burs toplu olarak onaylandı.")
        return sayac

    def toplu_reddet(self) -> int:
        """Bekleyen tüm bursları tek seferde 'reddedildi' yapar."""
        veriler = self._yukle()
        sayac = 0
        zaman = datetime.now().isoformat()
        for b in veriler.values():
            if b.get("durum") == "bekliyor":
                b["durum"] = "reddedildi"
                b["guncelleme_zamani"] = zaman
                sayac += 1
        self._kaydet(veriler)
        logger.info(f"❌ {sayac} adet burs toplu olarak reddedildi.")
        return sayac

    def onayli_burs_idleri(self) -> List[str]:
        """Onaylanmış bursların ID listesi."""
        veriler = self._yukle()
        return [b_id for b_id, v in veriler.items() if v.get("durum") == "onaylandi"]
