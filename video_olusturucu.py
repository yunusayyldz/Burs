"""
video_olusturucu.py - Pillow ile 9:16 bilgi karti cizimi + ffmpeg video render
Cozunurluk: 1080x1920 (YouTube Shorts)
Cikti: ciktilar/videolar/{burs_id}.mp4

Render stratejisi: Pillow PNG kart -> dogrudan ffmpeg subprocess (10-20x daha hizli)
"""

import logging
import subprocess
import textwrap
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

import config
from config import VideoConfig, RenkPaleti
from ai_analiz import BursAnalizi

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Font Yönetimi
# ─────────────────────────────────────────────

def _font_yukle(boyut: int, kalin: bool = False) -> ImageFont.FreeTypeFont:
    """
    Windows sistem fontlarından Türkçe destekli font yükler.
    Bulunamazsa PIL varsayılan fontuna geri düşer.
    """
    import os
    windows_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")

    # Tercih sırası: Segoe UI (en iyi Türkçe) → Arial → varsayılan
    aday_fontlar = []
    if kalin:
        aday_fontlar = [
            os.path.join(windows_fonts, "segoeuib.ttf"),    # Segoe UI Bold
            os.path.join(windows_fonts, "arialbd.ttf"),      # Arial Bold
            os.path.join(windows_fonts, "calibrib.ttf"),     # Calibri Bold
        ]
    else:
        aday_fontlar = [
            os.path.join(windows_fonts, "segoeui.ttf"),      # Segoe UI
            os.path.join(windows_fonts, "arial.ttf"),         # Arial
            os.path.join(windows_fonts, "calibri.ttf"),       # Calibri
        ]

    for font_yolu in aday_fontlar:
        if os.path.exists(font_yolu):
            try:
                return ImageFont.truetype(font_yolu, boyut)
            except Exception:
                continue

    # Hiçbiri bulunamazsa varsayılan
    logger.warning(f"⚠️ TrueType font bulunamadı, PIL varsayılan kullanılıyor (boyut: {boyut})")
    return ImageFont.load_default(size=boyut)


# ─────────────────────────────────────────────
# Gradient Arka Plan
# ─────────────────────────────────────────────

def _gradient_arkaplan_olustur(
    genislik: int,
    yukseklik: int,
    renk1: Tuple[int, int, int],
    renk2: Tuple[int, int, int],
) -> Image.Image:
    """Dikey gradient arka plan oluşturur."""
    goruntu = Image.new("RGB", (genislik, yukseklik))
    piksel = goruntu.load()
    for y in range(yukseklik):
        oran = y / yukseklik
        r = int(renk1[0] + (renk2[0] - renk1[0]) * oran)
        g = int(renk1[1] + (renk2[1] - renk1[1]) * oran)
        b = int(renk1[2] + (renk2[2] - renk1[2]) * oran)
        for x in range(genislik):
            piksel[x, y] = (r, g, b)
    return goruntu


# ─────────────────────────────────────────────
# Yuvarlak Köşeli Dikdörtgen
# ─────────────────────────────────────────────

def _yuvarlatilmis_dikdortgen_ciz(
    draw: ImageDraw.ImageDraw,
    koordinatlar: Tuple[int, int, int, int],
    yaricap: int,
    dolgu: Tuple,
    kenar: Tuple = None,
    kenar_kalinligi: int = 0,
) -> None:
    """Yuvarlak köşeli dikdörtgen çizer."""
    x1, y1, x2, y2 = koordinatlar
    r = yaricap
    draw.rounded_rectangle(koordinatlar, radius=r, fill=dolgu, outline=kenar, width=kenar_kalinligi)


# ─────────────────────────────────────────────
# Metin Sarma
# ─────────────────────────────────────────────

def _metin_sar(metin: str, max_karakter: int = 35) -> List[str]:
    """Metni belirli genişlikte satırlara böler."""
    return textwrap.wrap(metin, width=max_karakter, break_long_words=True)


# ─────────────────────────────────────────────
# İkon Çizimi (Unicode Emoji → Geometrik Şekil)
# ─────────────────────────────────────────────

KRITER_IKONLARI = {
    "maddi_tutar":     "💰",
    "cakisma_durumu":  "🔗",
    "egitim_turu":     "🎓",
    "bolum_kriteri":   "📚",
    "basari_kriteri":  "⭐",
    "yan_haklar":      "🎁",
    "geri_odeme":      "📋",
    "basvuru":         "📅",
}


# ─────────────────────────────────────────────
# Ana Kart Çizim Fonksiyonu
# ─────────────────────────────────────────────

def bilgi_karti_ciz(analiz: BursAnalizi) -> Image.Image:
    """
    Burs analizi verilerinden 1080x1920 bilgi kartı oluşturur.

    Args:
        analiz: BursAnalizi dataclass nesnesi

    Returns:
        PIL Image nesnesi (RGBA)
    """
    W, H = config.VIDEO_CONFIG.genislik, config.VIDEO_CONFIG.yukseklik
    renkler = config.RENKLER

    # ── Arka plan gradient
    goruntu = _gradient_arkaplan_olustur(W, H, renkler.arka_plan_1, renkler.arka_plan_2)
    goruntu = goruntu.convert("RGBA")
    draw = ImageDraw.Draw(goruntu, "RGBA")

    # ── Dekoratif diagonal çizgiler (arka plan dokusu)
    for i in range(0, W + H, 80):
        draw.line([(i, 0), (0, i)], fill=(255, 255, 255, 8), width=1)

    # ═══════════════════════════════════════════
    # BÖLÜM 1: Üst Logo Bandı
    # ═══════════════════════════════════════════
    bant_yukseklik = 140
    draw.rectangle([(0, 0), (W, bant_yukseklik)], fill=(255, 215, 0, 30))

    # "BURS BİLGİSİ" etiket
    font_etiket = _font_yukle(28, kalin=True)
    draw.text((40, 20), "📢 BURS BİLGİSİ", font=font_etiket, fill=renkler.vurgu_sari)

    # Kurum adı
    font_kurum = _font_yukle(42, kalin=True)
    kurum_metni = analiz.kurum.upper()
    draw.text((40, 60), kurum_metni, font=font_kurum, fill=renkler.baslik_beyaz)

    # Üst ayırıcı çizgi
    draw.line([(40, bant_yukseklik - 5), (W - 40, bant_yukseklik - 5)],
              fill=renkler.vurgu_sari, width=2)

    # ═══════════════════════════════════════════
    # BÖLÜM 2: Burs Başlığı
    # ═══════════════════════════════════════════
    baslik_y = bant_yukseklik + 20

    font_baslik = _font_yukle(52, kalin=True)
    baslik_satirlari = _metin_sar(analiz.burs_adi, max_karakter=22)
    for satir in baslik_satirlari[:3]:  # Max 3 satır
        draw.text((40, baslik_y), satir, font=font_baslik, fill=renkler.vurgu_sari)
        baslik_y += 62

    # Aylık tutar büyük gösterim
    baslik_y += 10
    font_tutar = _font_yukle(80, kalin=True)
    tutar_metni = f"₺{analiz.maddi_tutar.aylik_tl:,}/ay"
    draw.text((40, baslik_y), tutar_metni, font=font_tutar, fill=renkler.vurgu_yesil)
    baslik_y += 95

    # Süre bilgisi
    font_sure = _font_yukle(32)
    sure_metni = (
        f"• Yılda {analiz.maddi_tutar.odeme_ay_sayisi} ay  "
        f"• {analiz.maddi_tutar.toplam_yil} yıl süre"
    )
    draw.text((40, baslik_y), sure_metni, font=font_sure, fill=renkler.metin_gri)
    baslik_y += 50

    # ═══════════════════════════════════════════
    # BÖLÜM 3: 8 Kriter Kartları
    # ═══════════════════════════════════════════
    kart_y = baslik_y + 20
    kart_kenar_bosluk = 30
    kart_genislik = W - (kart_kenar_bosluk * 2)
    kart_ic_bosluk = 18
    font_kriter_baslik = _font_yukle(26, kalin=True)
    font_kriter_icerik = _font_yukle(24)

    def _kriter_karti_ciz(
        y_baslangic: int,
        baslik: str,
        icerik: str,
        ikon: str,
        vurgu_rengi: Tuple,
    ) -> int:
        """Tek bir kriter kartı çizer, yeni y pozisyonunu döndürür."""
        # Mevrum ölçümü
        satirlar = _metin_sar(icerik, max_karakter=38)
        satirlar = satirlar[:3]  # Max 3 satır
        kart_yukseklik = 50 + (len(satirlar) * 30) + (kart_ic_bosluk * 2)

        if y_baslangic + kart_yukseklik > H - 200:
            return y_baslangic  # Ekrandan taşar, çizme

        # Kart arka planı (yarı saydam)
        _yuvarlatilmis_dikdortgen_ciz(
            draw,
            (kart_kenar_bosluk, y_baslangic, kart_kenar_bosluk + kart_genislik, y_baslangic + kart_yukseklik),
            yaricap=16,
            dolgu=(30, 30, 55, 200),
            kenar=vurgu_rengi[:3] + (80,),
            kenar_kalinligi=1,
        )

        # Sol vurgu çizgisi
        draw.rectangle(
            [(kart_kenar_bosluk, y_baslangic + 8),
             (kart_kenar_bosluk + 4, y_baslangic + kart_yukseklik - 8)],
            fill=vurgu_rengi,
        )

        # Başlık (ikon + metin)
        metin_x = kart_kenar_bosluk + 20
        draw.text(
            (metin_x, y_baslangic + kart_ic_bosluk),
            f"{baslik}",
            font=font_kriter_baslik,
            fill=vurgu_rengi,
        )

        # İçerik satırları
        icerik_y = y_baslangic + kart_ic_bosluk + 32
        for satir in satirlar:
            draw.text(
                (metin_x, icerik_y),
                satir,
                font=font_kriter_icerik,
                fill=renkler.baslik_beyaz,
            )
            icerik_y += 30

        return y_baslangic + kart_yukseklik + 12

    # Vurgu renkleri döngüsü
    vurgu_renkleri = [
        renkler.vurgu_sari,
        renkler.vurgu_mavi,
        renkler.vurgu_yesil,
        (255, 100, 180),   # Pembe
        (255, 150, 50),    # Turuncu
        renkler.vurgu_mavi,
        renkler.vurgu_yesil,
        renkler.cta_renk,
    ]

    # Eğitim türü formatla
    egitim_turu_metni = ", ".join(
        t.replace("_", " ").title() for t in analiz.egitim_turu
    ) or "Belirtilmemiş"

    # Başarı kriteri formatla
    basari_parcalar = []
    if analiz.basari_kriteri.taban_yks_sirasi:
        basari_parcalar.append(f"YKS ilk {analiz.basari_kriteri.taban_yks_sirasi:,}")
    if analiz.basari_kriteri.min_gno:
        basari_parcalar.append(f"Min GNO: {analiz.basari_kriteri.min_gno:.2f}")
    basari_metni = " | ".join(basari_parcalar) or analiz.basari_kriteri.aciklama or "Belirtilmemiş"

    # 8 kriter kartı
    kriterler = [
        ("💰 Maddi Destek", f"Aylık ₺{analiz.maddi_tutar.aylik_tl:,} | {analiz.maddi_tutar.odeme_ay_sayisi} ay/yıl | {analiz.maddi_tutar.toplam_yil} yıl"),
        ("🔗 KYK & Burs Çakışması", analiz.cakisma_durumu[:120]),
        ("🎓 Eğitim Türü", egitim_turu_metni),
        ("📚 Bölüm / Sınıf Şartı", analiz.bolum_kriteri[:100]),
        ("⭐ Başarı Kriteri", basari_metni[:100]),
        ("🎁 Yan Haklar", " • ".join(analiz.yan_haklar[:3])[:100] if analiz.yan_haklar else "Belirtilmemiş"),
        ("📋 Geri Ödeme", analiz.geri_odeme[:100]),
        ("📅 Son Başvuru", f"{analiz.basvuru_son_tarih}"),
    ]

    for i, (baslik, icerik) in enumerate(kriterler):
        kart_y = _kriter_karti_ciz(
            kart_y,
            baslik,
            icerik if icerik else "Belirtilmemiş",
            list(KRITER_IKONLARI.values())[i],
            vurgu_renkleri[i % len(vurgu_renkleri)],
        )

    # ═══════════════════════════════════════════
    # BÖLÜM 4: Alt CTA Bandı
    # ═══════════════════════════════════════════
    cta_yukseklik = 100
    cta_y = H - cta_yukseklik

    draw.rectangle([(0, cta_y), (W, H)], fill=(255, 90, 90, 200))

    font_cta = _font_yukle(34, kalin=True)
    cta_metni = "🔔 Detaylar için biyografiyi ziyaret edin!"
    cta_bb = draw.textbbox((0, 0), cta_metni, font=font_cta)
    cta_genislik = cta_bb[2] - cta_bb[0]
    draw.text(
        ((W - cta_genislik) // 2, cta_y + 30),
        cta_metni,
        font=font_cta,
        fill=renkler.baslik_beyaz,
    )

    return goruntu


# ─────────────────────────────────────────────
# Kart PNG Kaydetme
# ─────────────────────────────────────────────

def karti_kaydet(goruntu: Image.Image, burs_id: str) -> Path:
    """Bilgi kartını PNG olarak kaydeder."""
    kart_yolu = config.KART_DIR / f"{burs_id}.png"
    goruntu.save(str(kart_yolu), "PNG", optimize=True)
    logger.info(f"🖼️ Kart kaydedildi: {kart_yolu.name} ({kart_yolu.stat().st_size / 1024:.0f} KB)")
    return kart_yolu


# ─────────────────────────────────────────────
# Video Render
# ─────────────────────────────────────────────

def video_olustur(
    analiz: BursAnalizi,
    ses_yolu: Path,
    ses_suresi: float,
) -> Path:
    """
    Bilgi kartı + TTS sesi ile YouTube Shorts videosu oluşturur.

    Strateji: PIL PNG kartı + MP3 ses → doğrudan ffmpeg subprocess
    Bu yaklaşım MoviePy'nin frame-by-frame işleminden 10-20x daha hızlıdır.

    Args:
        analiz: BursAnalizi nesnesi
        ses_yolu: MP3 ses dosyası yolu
        ses_suresi: Ses dosyasının süresi (saniye)

    Returns:
        Oluşturulan MP4 dosyasının yolu
    """
    import subprocess

    burs_id = analiz.burs_id
    cfg = config.VIDEO_CONFIG

    logger.info(f"🎬 Video render başlıyor: {burs_id} (ses: {ses_suresi:.1f}s)")

    # ── 1. Bilgi kartı çiz ve kaydet
    goruntu = bilgi_karti_ciz(analiz)
    kart_yolu = karti_kaydet(goruntu, burs_id)

    # ── 2. Video süresi = ses süresi + fade buffer (Shorts max 60s)
    toplam_sure = max(ses_suresi + cfg.fade_out_sure, cfg.min_video_sure)
    toplam_sure = min(toplam_sure, cfg.max_video_sure)

    # ── 3. ffmpeg ile doğrudan render (statik görüntü + ses → MP4)
    video_yolu = config.VIDEO_DIR / f"{burs_id}.mp4"

    logger.info(f"⚙️  Encoding: {cfg.video_codec}, {cfg.fps}fps, {cfg.ffmpeg_preset} preset → {video_yolu.name}")

    # ffmpeg komutu:
    # -loop 1          : PNG'yi döngüye al
    # -i kart.png      : görüntü girdisi
    # -i ses.mp3       : ses girdisi
    # -t {sure}        : çıktı süresi
    # -vf fadein/fadeout : video filtresi
    # -c:v libx264     : video codec
    # -preset veryfast : hız/kalite dengesi
    # -crf 23          : kalite faktörü
    # -c:a aac         : ses codec
    # -b:a 128k        : ses bit hızı
    # -pix_fmt yuv420p : YouTube uyumlu piksel formatı
    # -shortest        : ses bittiğinde dur
    # -y               : üzerine yaz

    fade_in = cfg.fade_in_sure
    fade_out = cfg.fade_out_sure
    vf_filtre = (
        f"fade=t=in:st=0:d={fade_in},"
        f"fade=t=out:st={toplam_sure - fade_out}:d={fade_out}"
    )

    # imageio-ffmpeg'in ffmpeg binary'sini bul
    try:
        import imageio_ffmpeg
        ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_bin = "ffmpeg"  # PATH'te olduğunu varsay

    cmd = [
        ffmpeg_bin,
        "-y",                          # Üzerine yaz
        "-loop", "1",                  # Görüntüyü döngüye al
        "-i", str(kart_yolu),          # Görüntü girdisi
        "-i", str(ses_yolu),           # Ses girdisi
        "-t", str(toplam_sure),        # Çıktı süresi
        "-vf", vf_filtre,              # Fade in/out filtresi
        "-c:v", cfg.video_codec,
        "-preset", cfg.ffmpeg_preset,
        "-crf", "23",
        "-r", str(cfg.fps),
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",         # YouTube uyumlu
        "-shortest",
        "-movflags", "+faststart",     # Web streaming için optimize
        str(video_yolu),
    ]

    try:
        baslangic = __import__("time").time()
        sonuc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 dakika timeout
        )
        gecen = __import__("time").time() - baslangic

        if sonuc.returncode != 0:
            logger.error(f"ffmpeg hatası:\n{sonuc.stderr[-500:]}")
            raise RuntimeError(f"ffmpeg başarısız (kod {sonuc.returncode})")

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffmpeg zaman aşımı (300s): {burs_id}")

    dosya_boyutu = video_yolu.stat().st_size / (1024 * 1024)
    logger.info(
        f"✅ Video tamamlandı: {video_yolu.name} | "
        f"Süre: {toplam_sure:.1f}s | "
        f"Boyut: {dosya_boyutu:.1f} MB | "
        f"Render: {gecen:.1f}s"
    )

    return video_yolu

