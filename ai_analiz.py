"""
ai_analiz.py — Gemini 2.5 Flash ile burs duyurusu analizi
Giriş: Ham burs duyuru metni
Çıkış: 8 kriterli yapılandırılmış JSON (BursAnalizi dataclass)

Hata durumunda max 3 kez yeniden dener.
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import config

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Veri Modelleri
# ─────────────────────────────────────────────

@dataclass
class MaddiTutar:
    aylik_tl: int = 0
    odeme_ay_sayisi: int = 10   # Yılda kaç ay ödeniyor
    toplam_yil: int = 4

@dataclass
class BasariKriteri:
    taban_yks_sirasi: Optional[int] = None
    min_gno: Optional[float] = None
    altan_ders_durumu: str = "Belirtilmemiş"
    aciklama: str = ""

@dataclass
class BursAnalizi:
    """8 zorunlu kriterden oluşan tam burs analizi."""
    # Temel kimlik
    burs_id: str = ""
    burs_adi: str = ""
    kurum: str = ""

    # 8 zorunlu kriter
    maddi_tutar: MaddiTutar = field(default_factory=MaddiTutar)
    cakisma_durumu: str = ""
    egitim_turu: List[str] = field(default_factory=list)
    bolum_kriteri: str = ""
    basari_kriteri: BasariKriteri = field(default_factory=BasariKriteri)
    yan_haklar: List[str] = field(default_factory=list)
    geri_odeme: str = ""
    basvuru_son_tarih: str = ""
    basvuru_portal: str = ""

    # TTS için narrasyon metni
    narrasyon_metni: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────
# Gemini Sistem Promptu
# ─────────────────────────────────────────────

SISTEM_PROMPTU = """
Sen bir Türk yükseköğrenim bursu analiz uzmanısın.
Sana verilen ham burs duyurusu metnini analiz edip, aşağıdaki JSON şemasına tam uygun,
eksiksiz bir JSON nesnesi üreteceksin.

ZORUNLU KURALLAR:
1. Her alan doldurulmalıdır. Bilgi bulunamazsa "Belirtilmemiş" veya 0 yaz.
2. narrasyon_metni: Türkçe, doğal konuşma dili, 150-250 kelime, YouTube Shorts için optimize.
   - Heyecanlandırıcı ve bilgilendirici ol
   - Sayıları söyleme biçiminde yaz (örn. "dört bin lira" değil "4.000 TL")
   - Son cümlede izleyiciyi başvurmaya yönlendir
3. egitim_turu: SADECE geçerli olanları listele: ["orgün", "ikinci_öğretim", "uzaktan", "açık_öğretim"]
4. JSON dışında HİÇBİR ŞEY yazma. Sadece geçerli JSON döndür.

JSON ŞEMASI:
{
  "burs_adi": "string — bursun tam resmi adı",
  "kurum": "string — burs veren kurum/vakıf adı",
  "maddi_tutar": {
    "aylik_tl": integer — aylık TL miktarı (sadece rakam),
    "odeme_ay_sayisi": integer — yılda kaç ay ödeniyor,
    "toplam_yil": integer — kaç yıl süreceği
  },
  "cakisma_durumu": "string — KYK bursu/kredisi ve diğer özel vakıf burslarıyla uyumluluk durumu",
  "egitim_turu": ["array — hangi öğretim türlerinin başvurabileceği"],
  "bolum_kriteri": "string — bölüm, fakülte, sınıf kısıtlamaları",
  "basari_kriteri": {
    "taban_yks_sirasi": integer veya null — YKS başarı sırası (null=belirtilmemiş),
    "min_gno": float veya null — minimum GNO (null=belirtilmemiş),
    "altan_ders_durumu": "string — alttan ders ve başarısız not durumu",
    "aciklama": "string — ek başarı şartları"
  },
  "yan_haklar": ["array — staj, mentorluk, dil eğitimi, donanım desteği vb."],
  "geri_odeme": "string — karşılıksız mı, hizmet/geri ödeme yükümlülüğü var mı",
  "basvuru_son_tarih": "string — son başvuru tarihi (örn. '30 Ekim 2025')",
  "basvuru_portal": "string — başvuru URL'i",
  "narrasyon_metni": "string — TTS için Türkçe narrasyon metni"
}
"""


# ─────────────────────────────────────────────
# JSON Temizleme Yardımcısı
# ─────────────────────────────────────────────

def json_temizle(ham_metin: str) -> str:
    """Gemini'nin yanıtından saf JSON'u çıkarır."""
    # Markdown code block varsa temizle
    temiz = re.sub(r"```(?:json)?\s*", "", ham_metin)
    temiz = re.sub(r"```\s*$", "", temiz, flags=re.MULTILINE)
    temiz = temiz.strip()
    # İlk { ile son } arasını al
    baslangic = temiz.find("{")
    bitis = temiz.rfind("}") + 1
    if baslangic != -1 and bitis > baslangic:
        return temiz[baslangic:bitis]
    return temiz


# ─────────────────────────────────────────────
# Ana Analiz Fonksiyonu
# ─────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(config.GEMINI_MAX_DENEME),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((json.JSONDecodeError, ValueError, KeyError)),
    before_sleep=lambda rs: logger.warning(
        f"⚠️ JSON parse hatası, yeniden deneniyor ({rs.attempt_number}/{config.GEMINI_MAX_DENEME})..."
    )
)
def _gemini_cagir(client: genai.Client, ham_metin: str) -> Dict[str, Any]:
    """
    Gemini API'yi çağırır ve JSON yanıtı parse eder.
    Hata durumunda otomatik yeniden dener.
    """
    kullanici_mesaji = f"""
Aşağıdaki burs duyurusunu analiz et ve JSON üret:

---
{ham_metin}
---
"""
    yanit = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=kullanici_mesaji,
        config=types.GenerateContentConfig(
            system_instruction=SISTEM_PROMPTU,
            temperature=0.2,  # Tutarlı, tahmin edilebilir JSON çıktısı için düşük
            response_mime_type="application/json",
        ),
    )

    ham_json = yanit.text
    logger.debug(f"Gemini ham yanıt ({len(ham_json)} karakter):\n{ham_json[:200]}...")

    temiz_json = json_temizle(ham_json)
    veri = json.loads(temiz_json)

    # Zorunlu alanları kontrol et
    zorunlu_alanlar = [
        "burs_adi", "kurum", "maddi_tutar", "cakisma_durumu",
        "egitim_turu", "bolum_kriteri", "basari_kriteri",
        "yan_haklar", "geri_odeme", "basvuru_son_tarih",
        "basvuru_portal", "narrasyon_metni"
    ]
    eksik = [alan for alan in zorunlu_alanlar if alan not in veri]
    if eksik:
        raise KeyError(f"Eksik alanlar: {eksik}")

    return veri


def mock_analiz_uret(ham_metin: str, burs_id: str) -> BursAnalizi:
    """Offline testler için ham metinden temel bilgiler çıkaran mock analiz üretici."""
    # Başlık ve kurum kestirimi
    satirlar = [s.strip() for s in ham_metin.split("\n") if s.strip()]
    baslik = satirlar[0] if satirlar else "Örnek Burs Programı"
    for s in satirlar[:5]:
        if "burs" in s.lower() or "program" in s.lower():
            baslik = s.replace("Başlık:", "").replace("Burs Adı:", "").replace("Burs Programı:", "").strip()
            break

    kurum = "Eğitim Vakfı"
    for s in satirlar[:5]:
        if "kurum:" in s.lower():
            kurum = s.split(":", 1)[1].strip()
            break

    narrasyon = (
        f"Merhaba öğrenciler! {kurum} tarafından sağlanan {baslik} başvuruları devam ediyor. "
        f"Aylık beş bin Türk Lirası karşılıksız burs desteği, üniversite lisans ve yüksek lisans öğrencilerine sunuluyor. "
        f"KYK bursuyla da uyumlu olan bu programa katılmak ve tüm ayrıntıları öğrenmek için "
        f"biyografideki bağlantıya tıklayabilirsiniz. Başarılar dileriz!"
    )

    return BursAnalizi(
        burs_id=burs_id,
        burs_adi=baslik[:45],
        kurum=kurum[:35],
        maddi_tutar=MaddiTutar(aylik_tl=5000, odeme_ay_sayisi=10, toplam_yil=4),
        cakisma_durumu="KYK bursu ile uyumludur.",
        egitim_turu=["örgün"],
        bolum_kriteri="Tüm üniversite ve bölümler başvurabilir.",
        basari_kriteri=BasariKriteri(
            taban_yks_sirasi=100000,
            min_gno=2.5,
            altan_ders_durumu="Alttan en fazla 2 ders kabul edilir.",
            aciklama="Genel akademik başarı aranmaktadır."
        ),
        yan_haklar=["Mentorluk desteği", "Staj imkanı"],
        geri_odeme="Tamamen karşılıksızdır.",
        basvuru_son_tarih="15 Kasım 2026",
        basvuru_portal="https://burs.gov.tr",
        narrasyon_metni=narrasyon
    )


def burs_analiz_et(ham_metin: str, burs_id: str, mock_ai: bool = False) -> BursAnalizi:
    """
    Ham burs duyurusu metnini Gemini ile analiz eder.

    Args:
        ham_metin: Ham burs duyurusu metni
        burs_id: Benzersiz burs kimliği (dosya adlandırma için kullanılır)
        mock_ai: True ise veya API anahtarı geçersizse offline mock analiz kullanılır

    Returns:
        BursAnalizi dataclass nesnesi
    """
    if mock_ai:
        logger.info(f"🧪 Mock AI modu aktif: {burs_id}")
        return mock_analiz_uret(ham_metin, burs_id)

    if not config.GEMINI_API_KEY or "YOUR_GEMINI" in config.GEMINI_API_KEY:
        logger.warning(f"⚠️ Geçerli GEMINI_API_KEY bulunamadı, {burs_id} için mock analiz kullanılıyor.")
        return mock_analiz_uret(ham_metin, burs_id)

    logger.info(f"🤖 Gemini analizi başlıyor: {burs_id}")

    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        veri = _gemini_cagir(client, ham_metin)
    except Exception as e:
        logger.warning(f"⚠️ Gemini API hatası ({e}), mock analize geçiliyor...")
        return mock_analiz_uret(ham_metin, burs_id)

    # Dataclass'a dönüştür
    maddi = veri.get("maddi_tutar", {})
    basari = veri.get("basari_kriteri", {})

    analiz = BursAnalizi(
        burs_id=burs_id,
        burs_adi=veri.get("burs_adi", "Bilinmeyen Burs"),
        kurum=veri.get("kurum", "Bilinmeyen Kurum"),
        maddi_tutar=MaddiTutar(
            aylik_tl=int(maddi.get("aylik_tl", 0)),
            odeme_ay_sayisi=int(maddi.get("odeme_ay_sayisi", 10)),
            toplam_yil=int(maddi.get("toplam_yil", 4)),
        ),
        cakisma_durumu=veri.get("cakisma_durumu", "Belirtilmemiş"),
        egitim_turu=veri.get("egitim_turu", []),
        bolum_kriteri=veri.get("bolum_kriteri", "Belirtilmemiş"),
        basari_kriteri=BasariKriteri(
            taban_yks_sirasi=basari.get("taban_yks_sirasi"),
            min_gno=basari.get("min_gno"),
            altan_ders_durumu=basari.get("altan_ders_durumu", "Belirtilmemiş"),
            aciklama=basari.get("aciklama", ""),
        ),
        yan_haklar=veri.get("yan_haklar", []),
        geri_odeme=veri.get("geri_odeme", "Belirtilmemiş"),
        basvuru_son_tarih=veri.get("basvuru_son_tarih", "Belirtilmemiş"),
        basvuru_portal=veri.get("basvuru_portal", "Belirtilmemiş"),
        narrasyon_metni=veri.get("narrasyon_metni", ""),
    )

    logger.info(
        f"✅ Analiz tamamlandı: {analiz.burs_adi} | "
        f"Aylık: {analiz.maddi_tutar.aylik_tl:,} TL | "
        f"Narrasyon: {len(analiz.narrasyon_metni.split())} kelime"
    )

    return analiz
