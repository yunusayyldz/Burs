"""
scraper/mock_scraper.py — Pipeline testi için gerçekçi mock burs verileri
Faz 2'de bu dosya gerçek web scraper'larla değiştirilecek.

Mock veriler 8 zorunlu kriteri kapsayan, gerçekçi Türkçe duyuru metinleridir.
Her burs BAĞIMSIZ bir HamDuyuru nesnesidir (birleştirme YASAK).
"""

import logging
from typing import List
from .base_scraper import BaseScraper, HamDuyuru

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Mock Burs Duyuruları (Gerçekçi Veriler)
# ─────────────────────────────────────────────

MOCK_DUYURULAR = [
    {
        "kaynak_url": "https://www.isbank.com.tr/burs/lisans-bursu",
        "kurum_adi": "Türkiye İş Bankası",
        "kaynak_adi": "mock_isbank",
        "benzersiz_id": "isbank_lisans_2025",
        "ham_metin": """
TÜRKİYE İŞ BANKASI LİSANS BURS PROGRAMI 2025-2026

Türkiye İş Bankası, Türkiye'nin önde gelen üniversitelerinde lisans eğitimi gören 
başarılı öğrencilere yönelik burs programı kapsamında 2025-2026 akademik yılı için 
başvuruları açmıştır.

MADDİ DESTEK:
Seçilen öğrencilere aylık 4.000 TL (Dört Bin Türk Lirası) burs ödemesi yapılmaktadır.
Burs, öğrencinin 4 yıllık lisans süresince (yılda 10 ay, Ekim-Temmuz arası) devam eder.
Toplam destek süresi: 4 yıl.

EĞİTİM TÜRÜ KAPSAMI:
Yalnızca örgün öğretim öğrencileri başvurabilir. İkinci öğretim, uzaktan eğitim ve 
açık öğretim öğrencileri bu burs kapsamı dışındadır.

BÖLÜM / FAKÜLTE ŞARTI:
Başvurular tüm fakülte ve bölümlere açıktır. Hazırlık sınıfı öğrencileri başvurabilir.
Ara sınıf öğrencileri (2., 3. ve 4. sınıf) de başvurabilir.

BAŞARI KRİTERLERİ:
- Yeni kayıt öğrenciler için: YKS (SAY/SÖZ/EA) puan sıralamasında ilk 50.000'e girmiş olmak
- Ara sınıf öğrencileri için: Genel Not Ortalaması (GNO) en az 3.00/4.00 olmalıdır
- Başvuru tarihinde herhangi bir dersten FF, FD notu olmamalıdır (alttan ders kabul edilmez)

ÇAKIŞMA DURUMU:
KYK (Kredi ve Yurtlar Kurumu) bursu veya kredisi ile birlikte alınabilir.
Diğer özel vakıf burslarıyla çakışma durumu için ilgili vakfın şartları incelenmelidir.
Birden fazla özel burs alındığında İş Bankası bursu iptal edilebilir — başvuru sırasında beyan zorunludur.

YAN HAKLAR:
- Yıllık bankacılık sektörü staj imkânı (İş Bankası bünyesinde)
- Kariyer mentorluk programına katılım hakkı
- İş Bankası gençlik etkinliklerine davet
- Öğrenci bankacılığı paketi (komisyonsuz hesap)

GERİ ÖDEME / HİZMET YÜKÜMLÜLÜĞÜ:
Bu burs tamamen karşılıksızdır. Herhangi bir geri ödeme veya hizmet yükümlülüğü yoktur.

BAŞVURU TAKVİMİ VE YÖNTEMİ:
- Son başvuru tarihi: 30 Ekim 2025
- Başvuru yöntemi: Yalnızca online — https://burs.isbank.com.tr
- Gerekli belgeler: Transkript, öğrenci belgesi, gelir durumu belgesi, YKS sonuç belgesi
- Mülakatlar: Kasım 2025 (online video mülakat)
- Sonuç açıklaması: Aralık 2025
"""
    },
    {
        "kaynak_url": "https://www.tupras.com.tr/sosyal-sorumluluk/burs",
        "kurum_adi": "TÜPRAŞ",
        "kaynak_adi": "mock_tupras",
        "benzersiz_id": "tupras_ustun_basari_2025",
        "ham_metin": """
TÜPRAŞ ÜSTÜN BAŞARI BURS PROGRAMI 2025-2026

Türkiye Petrol Rafinerileri A.Ş. (TÜPRAŞ), ülkemizin gelecekteki mühendis ve 
bilim insanlarını yetiştirme amacıyla Üstün Başarı Burs Programı'nı hayata geçirmiştir.

MADDİ DESTEK:
Lisans öğrencilerine aylık 5.500 TL burs verilmektedir.
Yüksek lisans öğrencilerine aylık 8.000 TL burs verilmektedir.
Burs ödemeleri yılda 12 ay (kesintisiz, yaz dahil) yapılmaktadır.
Lisans bursu maksimum 4 yıl, yüksek lisans bursu maksimum 2 yıl sürer.

NOT: Lisans ve yüksek lisans bursları TAMAMEN AYRI programlardır, ayrı başvuru gerektirir.

EĞİTİM TÜRÜ KAPSAMI:
Yalnızca örgün öğretim (birinci öğretim) öğrencileri başvurabilir.
İkinci öğretim, uzaktan eğitim ve açık öğretim programları kapsam dışıdır.

BÖLÜM / FAKÜLTE / SINIF ŞARTI:
Sadece aşağıdaki bölümlerin öğrencileri başvurabilir:
- Kimya Mühendisliği
- Petrol ve Doğalgaz Mühendisliği
- Makine Mühendisliği
- Elektrik-Elektronik Mühendisliği
- Endüstri Mühendisliği
- Kimya (Fen Fakültesi)
- Çevre Mühendisliği

Sadece 1. ve 2. sınıf öğrencileri başvurabilir (3. ve 4. sınıflar başvuramaz).
Hazırlık sınıfı öğrencileri başvurabilir (başarı kriteri YKS sırası olarak değerlendirilir).

BAŞARI KRİTERLERİ:
- Birinci sınıflar: YKS SAY puan türünde ilk 10.000'e girmiş olmak ZORUNLUDUR
- İkinci sınıflar: GNO en az 3.25/4.00 (veya 82.5/100) olmalıdır
- Hiçbir dersten başarısız (FF, FD, YZ, DZ) not olmamalıdır
- Alttan ders durumunda başvuru kesinlikle kabul edilmez

ÇAKIŞMA DURUMU:
KYK bursu veya kredisi ile birlikte alınabilir — uyumludur.
Diğer özel vakıf/şirket burslarıyla ÇAKIŞIR; TÜPRAŞ bursu alınırken başka özel kurumdan 
burs alınamaz. Yanlış beyanda cezai şart uygulanır.

YAN HAKLAR:
- Zorunlu staj TÜPRAŞ rafinerilerinde yapılabilir (İzmit, İzmir, Kırıkkale, Kırklareli)
- Teknik mentorluk programı (TÜPRAŞ mühendisleriyle birebir)
- Yurt içi ve yurt dışı teknik gezi imkânı
- TÜPRAŞ'ta işe alım önceliği (mezuniyet sonrası)
- Yabancı dil eğitimi desteği (İngilizce — yılda 200 saate kadar)

GERİ ÖDEME / HİZMET YÜKÜMLÜLÜĞÜ:
Burs karşılıksız değildir. Vicdani hizmet yükümlülüğü vardır:
Bursu alan öğrenci, mezun olduğunda TÜPRAŞ'ta en az 2 yıl çalışmayı taahhüt eder.
Bu taahhüt yerine getirilmezse, alınan toplam burs miktarı yasal faiziyle iade edilir.

BAŞVURU TAKVİMİ VE YÖNTEMİ:
- Son başvuru tarihi: 15 Kasım 2025 (saat 23:59)
- Başvuru portalı: https://burs.tupras.com.tr
- Başvuru tamamen online, posta/elden başvuru kabul edilmez
- Gerekli belgeler: Transkript (onaylı), öğrenci belgesi, nüfus cüzdanı fotokopisi,
  gelir durumu belgesi (aile beyan formu), YKS sonuç belgesi, motivasyon mektubu (Türkçe, 500 kelime)
- Mülakat: Aralık 2025 (yüz yüze, TÜPRAŞ ofislerinde)
- Kesin sonuç: Ocak 2026
"""
    },
    {
        "kaynak_url": "https://www.vehbikocsvakfi.org.tr/burs/lisans",
        "kurum_adi": "Vehbi Koç Vakfı",
        "kaynak_adi": "mock_vkv",
        "benzersiz_id": "vkv_lisans_2025",
        "ham_metin": """
VEHBİ KOÇ VAKFI BAŞARI BURSU 2025-2026

Vehbi Koç Vakfı, Türkiye'nin önde gelen vakıflarından biri olarak, akademik başarısı 
yüksek ve ekonomik desteğe ihtiyacı olan lisans öğrencilerine yönelik Başarı Burs 
Programı'nı sürdürmektedir.

MADDİ DESTEK:
Seçilen öğrencilere aylık 3.500 TL burs ödemesi yapılmaktadır.
Burs yılda 9 ay (Ekim-Haziran arası, yaz tatilinde ödeme yapılmaz) ödenir.
Başarı şartı sağlandığı sürece lisans eğitimi boyunca devam eder (maksimum 4+1=5 yıl).

EĞİTİM TÜRÜ KAPSAMI:
Örgün öğretim (birinci öğretim) öğrencileri başvurabilir.
İkinci öğretim öğrencileri de başvurabilir — bu, Vehbi Koç Vakfı'nı diğer vakıflardan ayıran
önemli bir özelliktir.
Uzaktan eğitim ve açık öğretim öğrencileri kapsam dışıdır.

BÖLÜM / FAKÜLTE ŞARTI:
Tüm fakülte ve bölümler başvurabilir — bölüm kısıtlaması yoktur.
Hazırlık sınıfı öğrencileri başvurabilir.
Tüm sınıf öğrencileri (1-4) başvurabilir.

BAŞARI KRİTERLERİ:
- 1. sınıf yeni kayıt: YKS herhangi bir puan türünde ilk 30.000'e girmiş olmak
- Ara sınıflar: GNO en az 2.80/4.00
- En fazla 2 dersten CC notu kabul edilir; FF, FD, DZ notu olanlar başvuramaz
- Aile geliri: Kişi başı aylık net gelir 15.000 TL'yi aşmamalıdır (gelir testi uygulanır)

ÇAKIŞMA DURUMU:
KYK bursu ve kredisiyle uyumludur — birlikte alınabilir.
Diğer özel vakıf burslarıyla uyumludur — birden fazla özel burs alınabilir.
(Bu konu başvuru formunda beyan edilmelidir)

YAN HAKLAR:
- Koç Topluluğu kariyer ağına erişim
- Yıllık bursiyerler buluşmasına davet
- Online kurs ve sertifika programı erişimi (Coursera, LinkedIn Learning)
- Psikolojik danışmanlık ve akademik koçluk desteği

GERİ ÖDEME / HİZMET YÜKÜMLÜLÜĞÜ:
Burs tamamen karşılıksızdır. Herhangi bir geri ödeme veya hizmet yükümlülüğü bulunmamaktadır.

BAŞVURU TAKVİMİ VE YÖNTEMİ:
- Son başvuru tarihi: 31 Ekim 2025
- Başvuru portalı: https://burs.vehbikoçvakfi.org.tr
- Online başvuru zorunludur; belgelerin asılları mülakat aşamasında istenir
- Gerekli belgeler: Transkript, öğrenci belgesi, gelir belgesi (SGK dökümü + vergi beyannamesi),
  YKS sonuç belgesi, öz geçmiş, referans mektubu (isteğe bağlı)
- Mülakatlar: Kasım-Aralık 2025 (karma — önce online sonra yüz yüze)
- Sonuçlar: Ocak 2026 başı
"""
    },
]


class MockScraper(BaseScraper):
    """
    Pipeline testi için gerçekçi mock burs verisi döndürür.
    Faz 2'de bu sınıf gerçek URL scraper'larıyla değiştirilecek.
    
    3 bağımsız burs programı içerir:
    1. Türkiye İş Bankası Lisans Bursu
    2. TÜPRAŞ Üstün Başarı Bursu (Lisans) — NOT: Lisans ve YL ayrı programlardır
    3. Vehbi Koç Vakfı Başarı Bursu
    """

    kaynak_adi = "mock"
    kaynak_url = "local://mock"

    def fetch_duyurular(self) -> List[HamDuyuru]:
        """
        Mock burs duyurularını döndürür.
        Her eleman BAĞIMSIZ bir burs programıdır.
        """
        duyurular = []
        for veri in MOCK_DUYURULAR:
            duyuru = HamDuyuru(
                kaynak_url=veri["kaynak_url"],
                kurum_adi=veri["kurum_adi"],
                ham_metin=veri["ham_metin"].strip(),
                kaynak_adi=veri["kaynak_adi"],
                benzersiz_id=veri["benzersiz_id"],
            )
            duyurular.append(duyuru)
            logger.debug(f"Mock duyuru yüklendi: {veri['kurum_adi']} ({veri['benzersiz_id']})")

        logger.info(f"✅ {len(duyurular)} mock burs duyurusu hazır.")
        return duyurular
