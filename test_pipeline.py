"""
test_pipeline.py - Gemini API anahtari olmadan pipeline testi
Mock analiz verisi kullanarak TTS + Video uretimini test eder.

Kullanim:
    venv/Scripts/python.exe test_pipeline.py
"""

import io
import logging
import sys
from pathlib import Path

# Windows terminali icin UTF-8 zorla (CP1254 emoji sorununu onler)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

import config
config.dizinleri_olustur()

from ai_analiz import BursAnalizi, MaddiTutar, BasariKriteri
from seslendirici import seslendir
from video_olusturucu import video_olustur

# ── 3 Mock Analiz (Gemini çıktısını simüle eder)

MOCK_ANALIZLER = [
    BursAnalizi(
        burs_id="isbank_lisans_2025",
        burs_adi="Türkiye İş Bankası Lisans Bursu",
        kurum="Türkiye İş Bankası",
        maddi_tutar=MaddiTutar(aylik_tl=4000, odeme_ay_sayisi=10, toplam_yil=4),
        cakisma_durumu="KYK bursu ve kredisiyle uyumludur. Diğer özel vakıf burslarında beyan zorunludur.",
        egitim_turu=["örgün"],
        bolum_kriteri="Tüm fakülte ve bölümler başvurabilir. Hazırlık dahil tüm sınıflar.",
        basari_kriteri=BasariKriteri(
            taban_yks_sirasi=50000,
            min_gno=3.0,
            altan_ders_durumu="FF veya FD notu olanlar başvuramaz.",
            aciklama="Yeni kayıtlar için YKS sırası, ara sınıflar için GNO şartı aranır."
        ),
        yan_haklar=["Yıllık bankacılık sektörü staj imkânı", "Kariyer mentorluk programı", "Öğrenci bankacılığı paketi (komisyonsuz)"],
        geri_odeme="Tamamen karşılıksızdır. Geri ödeme veya hizmet yükümlülüğü yoktur.",
        basvuru_son_tarih="30 Ekim 2025",
        basvuru_portal="https://burs.isbank.com.tr",
        narrasyon_metni=(
            "Merhaba burs arayanlar! Türkiye İş Bankası, 2025-2026 akademik yılı için "
            "lisans bursu başvurularını açtı. Her ay dört bin lira burs alacaksınız. "
            "Üstelik bu burs yılda on ay, tam dört yıl boyunca ödeniyor. "
            "Peki kim başvurabilir? Herhangi bir bölümden örgün öğretim öğrencisi olmanız yeterli. "
            "YKS sıralamasında ilk elli bine girenler doğrudan başvurabilir. "
            "Ara sınıf öğrencileri için genel not ortalamasının en az üç sıfır sıfır olması gerekiyor. "
            "KYK bursu veya kredisiyle de birlikte alınabiliyor, bu harika bir avantaj! "
            "Ayrıca burs kazananlara İş Bankası bünyesinde staj ve kariyer mentorluğu imkânı da sunuluyor. "
            "En önemlisi bu burs tamamen karşılıksız, hiçbir geri ödeme yükümlülüğü yok. "
            "Son başvuru tarihi otuz Ekim iki bin yirmi beş. "
            "Hemen biyografideki linke tıklayın ve başvurunuzu yapın!"
        ),
    ),
    BursAnalizi(
        burs_id="tupras_ustun_basari_2025",
        burs_adi="TÜPRAŞ Üstün Başarı Bursu",
        kurum="TÜPRAŞ",
        maddi_tutar=MaddiTutar(aylik_tl=5500, odeme_ay_sayisi=12, toplam_yil=4),
        cakisma_durumu="KYK ile uyumludur. Diğer özel burslarla ÇAKIŞIR — beyan zorunludur.",
        egitim_turu=["örgün"],
        bolum_kriteri=(
            "Sadece: Kimya Müh., Petrol ve Doğalgaz Müh., Makine Müh., "
            "Elektrik-Elektronik Müh., Endüstri Müh., Kimya, Çevre Müh. "
            "1. ve 2. sınıf öğrencileri başvurabilir."
        ),
        basari_kriteri=BasariKriteri(
            taban_yks_sirasi=10000,
            min_gno=3.25,
            altan_ders_durumu="FF, FD, YZ, DZ notu olanlar kesinlikle başvuramaz.",
            aciklama="1. sınıflar YKS SAY ilk 10.000, 2. sınıflar GNO 3.25 üstü."
        ),
        yan_haklar=[
            "TÜPRAŞ rafinerilerinde zorunlu staj (İzmit, İzmir, Kırıkkale, Kırklareli)",
            "Teknik mentorluk programı",
            "Yurt içi/dışı teknik gezi",
            "TÜPRAŞ'ta işe alım önceliği",
            "Yabancı dil eğitimi (yılda 200 saate kadar)",
        ],
        geri_odeme=(
            "Vicdani hizmet yükümlülüğü vardır: Mezuniyet sonrası TÜPRAŞ'ta en az 2 yıl "
            "çalışma taahhüdü. Yerine getirilmezse alınan burs yasal faiziyle iade edilir."
        ),
        basvuru_son_tarih="15 Kasım 2025",
        basvuru_portal="https://burs.tupras.com.tr",
        narrasyon_metni=(
            "Mühendislik öğrencileri dikkat! TÜPRAŞ Üstün Başarı Bursu başvuruları başladı! "
            "Her ay beş bin beş yüz lira burs alacaksınız. Hem de yaz tatili dahil yılın on iki ayı boyunca. "
            "Dört yıl boyunca kesintisiz ödeme yapılıyor. "
            "Kimya, Makine, Elektrik, Endüstri ve Petrol Mühendisliği gibi teknik bölümlerin "
            "birinci ve ikinci sınıf öğrencileri başvurabilir. "
            "YKS SAY puan türünde ilk on bine girmiş olmanız gerekiyor. "
            "Ara sınıflar için genel not ortalaması üç virgül yirmi beş şartı aranıyor. "
            "Bursun çok cazip yan hakları var: TÜPRAŞ rafinerilerinde staj imkânı, "
            "teknik mentorluk ve mezuniyet sonrası işe alım önceliği. "
            "Dikkat! Bu burs karşılıksız değil. Mezuniyetten sonra TÜPRAŞ'ta iki yıl çalışma taahhüdü isteniyor. "
            "Son başvuru tarihi on beş Kasım iki bin yirmi beş. "
            "Biyografideki linke tıklayın ve başvurunuzu tamamlayın!"
        ),
    ),
    BursAnalizi(
        burs_id="vkv_lisans_2025",
        burs_adi="Vehbi Koç Vakfı Başarı Bursu",
        kurum="Vehbi Koç Vakfı",
        maddi_tutar=MaddiTutar(aylik_tl=3500, odeme_ay_sayisi=9, toplam_yil=4),
        cakisma_durumu="KYK ve diğer özel vakıf burslarıyla tamamen uyumludur. Birden fazla burs alınabilir.",
        egitim_turu=["örgün", "ikinci_öğretim"],
        bolum_kriteri="Tüm fakülte ve bölümler. Hazırlık dahil tüm sınıflar. İkinci öğretim de başvurabilir!",
        basari_kriteri=BasariKriteri(
            taban_yks_sirasi=30000,
            min_gno=2.80,
            altan_ders_durumu="En fazla 2 dersten CC notu kabul edilir. FF, FD, DZ olanlar başvuramaz.",
            aciklama="Gelir testi: kişi başı aylık net gelir 15.000 TL'yi aşmamalı."
        ),
        yan_haklar=[
            "Koç Topluluğu kariyer ağına erişim",
            "Online kurs ve sertifika programı (Coursera, LinkedIn Learning)",
            "Psikolojik danışmanlık ve akademik koçluk",
            "Yıllık bursiyerler buluşması",
        ],
        geri_odeme="Tamamen karşılıksızdır. Hiçbir geri ödeme veya hizmet yükümlülüğü bulunmamaktadır.",
        basvuru_son_tarih="31 Ekim 2025",
        basvuru_portal="https://burs.vehbikocvakfi.org.tr",
        narrasyon_metni=(
            "Herkese merhaba! Vehbi Koç Vakfı Başarı Bursu başvuruları açıldı! "
            "Her ay üç bin beş yüz lira burs alacaksınız. Yılda dokuz ay ödeme yapılıyor. "
            "Bu bursun en büyük avantajlarından biri: İkinci öğretim öğrencileri de başvurabilir! "
            "Herhangi bir bölümden olabilirsiniz, fakülte kısıtlaması yok. "
            "YKS'de ilk otuz bine girenler doğrudan başvurabilir. "
            "Ara sınıflar için genel not ortalaması iki virgül seksen yeterli. "
            "Ayrıca bu burs KYK dahil diğer tüm burslarla birlikte alınabiliyor, bu çok önemli! "
            "Koç Topluluğu'nun geniş kariyer ağına, online eğitim platformlarına ve "
            "akademik koçluk programına da erişim sağlıyorsunuz. "
            "Ve en güzeli: bu burs tamamen karşılıksız, hiçbir yükümlülük yok! "
            "Son başvuru tarihi otuz bir Ekim iki bin yirmi beş. "
            "Kaçırmayın, hemen biyografideki linke tıklayın!"
        ),
    ),
]


def test_calistir(burs_id: str = None):
    """Pipeline testini çalıştırır."""
    print("\n" + "═" * 55)
    print("  🧪 PIPELINE TESTİ (Gemini olmadan mock analiz)")
    print("═" * 55)

    analizler = MOCK_ANALIZLER
    if burs_id:
        analizler = [a for a in MOCK_ANALIZLER if a.burs_id == burs_id]
        if not analizler:
            print(f"❌ ID bulunamadı: {burs_id}")
            sys.exit(1)

    basarili = 0
    hatali = 0

    for analiz in analizler:
        print(f"\n{'─' * 50}")
        print(f"📋 {analiz.burs_adi} [{analiz.burs_id}]")

        try:
            # TTS
            print(f"  🎙️ TTS üretiliyor...")
            ses_yolu, ses_suresi = seslendir(analiz.narrasyon_metni, analiz.burs_id)
            print(f"     ✅ {ses_yolu.name} ({ses_suresi:.1f}s, {ses_yolu.stat().st_size/1024:.0f} KB)")

            # Video
            print(f"  🎬 Video render ediliyor...")
            video_yolu = video_olustur(analiz, ses_yolu, ses_suresi)
            boyut = video_yolu.stat().st_size / (1024 * 1024)
            print(f"     ✅ {video_yolu.name} ({boyut:.2f} MB)")

            basarili += 1

        except Exception as e:
            print(f"     ❌ HATA: {e}")
            logger.error(f"Test hatası — {analiz.burs_id}: {e}", exc_info=True)
            hatali += 1

    print(f"\n{'═' * 55}")
    print(f"📊 SONUÇ: ✅ {basarili} başarılı  ❌ {hatali} hatalı")

    # Üretilen dosyaları listele
    print(f"\n📁 Üretilen dosyalar:")
    for f in sorted(config.SES_DIR.glob("*.mp3")):
        if f.stem != "test_tts":  # Test dosyasını atla
            print(f"   🎵 {f.name} ({f.stat().st_size/1024:.0f} KB)")
    for f in sorted(config.KART_DIR.glob("*.png")):
        if f.stem != "test_video":
            print(f"   🖼️ {f.name} ({f.stat().st_size/1024:.0f} KB)")
    for f in sorted(config.VIDEO_DIR.glob("*.mp4")):
        if f.stem != "test_video":
            print(f"   🎬 {f.name} ({f.stat().st_size/(1024*1024):.2f} MB)")
    print(f"{'═' * 55}\n")


if __name__ == "__main__":
    burs_id_filtre = sys.argv[1] if len(sys.argv) > 1 else None
    test_calistir(burs_id_filtre)
