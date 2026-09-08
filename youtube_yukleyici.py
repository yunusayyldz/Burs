"""
youtube_yukleyici.py — YouTube Data API v3 OAuth2 + Video Yükleme
Akış: OAuth2 Desktop App → token.json → resumable upload
"""

import logging
import os
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)

# YouTube API sabitleri
YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"


def _youtube_servisi_al():
    """
    YouTube API servisi oluşturur (OAuth2 doğrulamasıyla).
    İlk çalıştırmada tarayıcı açılır; sonrasında token.json kullanılır.

    Returns:
        googleapiclient.discovery.Resource — YouTube API servisi

    Raises:
        FileNotFoundError: client_secrets.json bulunamazsa
        RuntimeError: OAuth akışı başarısız olursa
    """
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not config.YOUTUBE_CLIENT_SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"YouTube client_secrets.json bulunamadı: {config.YOUTUBE_CLIENT_SECRETS_PATH}\n"
            "Google Cloud Console'dan 'Desktop App' tipi OAuth 2.0 istemcisi oluşturun."
        )

    kimlik_bilgileri = None

    # Mevcut token'ı yükle
    if config.YOUTUBE_TOKEN_PATH.exists():
        try:
            kimlik_bilgileri = Credentials.from_authorized_user_file(
                str(config.YOUTUBE_TOKEN_PATH),
                config.YOUTUBE_SCOPES,
            )
            logger.info(f"📱 Mevcut YouTube token yüklendi: {config.YOUTUBE_TOKEN_PATH.name}")
        except Exception as e:
            logger.warning(f"Token yüklenemedi, yeniden auth yapılacak: {e}")
            kimlik_bilgileri = None

    # Token geçersiz veya süresi dolmuşsa yenile
    if not kimlik_bilgileri or not kimlik_bilgileri.valid:
        if kimlik_bilgileri and kimlik_bilgileri.expired and kimlik_bilgileri.refresh_token:
            logger.info("🔄 YouTube token yenileniyor...")
            kimlik_bilgileri.refresh(Request())
        else:
            logger.info("🌐 YouTube OAuth2 akışı başlatılıyor (tarayıcı açılacak)...")
            akis = InstalledAppFlow.from_client_secrets_file(
                str(config.YOUTUBE_CLIENT_SECRETS_PATH),
                config.YOUTUBE_SCOPES,
            )
            kimlik_bilgileri = akis.run_local_server(port=0)

        # Token'ı kaydet
        with open(config.YOUTUBE_TOKEN_PATH, "w") as token_dosyasi:
            token_dosyasi.write(kimlik_bilgileri.to_json())
        logger.info(f"💾 YouTube token kaydedildi: {config.YOUTUBE_TOKEN_PATH.name}")

    return build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=kimlik_bilgileri)


def _youtube_metadata_olustur(
    burs_adi: str,
    kurum: str,
    narrasyon_metni: str,
    basvuru_portal: str,
    basvuru_son_tarih: str,
    egitim_turu: list,
) -> dict:
    """YouTube video metadata sözlüğü oluşturur."""

    # Başlık (max 100 karakter)
    baslik = f"{burs_adi} | {kurum} Burs Başvurusu 2025 #Shorts"
    if len(baslik) > 100:
        baslik = baslik[:97] + "..."

    # Açıklama
    egitim_turu_str = ", ".join(t.replace("_", " ").title() for t in egitim_turu)
    aciklama = (
        f"📢 {burs_adi}\n"
        f"🏛️ {kurum}\n\n"
        f"{narrasyon_metni[:300]}...\n\n"
        f"─────────────────────────\n"
        f"📅 Son Başvuru: {basvuru_son_tarih}\n"
        f"🎓 Öğretim Türü: {egitim_turu_str}\n"
        f"🔗 Başvuru: {basvuru_portal}\n"
        f"─────────────────────────\n\n"
        f"#Burs #YKS #Üniversite #BursStartup #ÖğrenciHakları "
        f"#{kurum.replace(' ', '')} #TürkiyeBursları #ÜcretsizEğitim\n\n"
        f"✅ Bildirimleri açın — her burs duyurusunu kaçırmayın!"
    )

    # Etiketler
    etiketler = [
        "burs", "yks", "üniversite", "öğrenci", "burs başvurusu",
        "türkiye bursu", "lisans bursu", "yüksek lisans bursu",
        kurum.lower().replace(" ", ""),
        burs_adi.lower()[:30],
        "burs haberleri", "2025 burs", "ücretsiz eğitim",
    ]

    return {
        "snippet": {
            "title": baslik,
            "description": aciklama,
            "tags": etiketler[:15],  # YouTube max 15 etiket
            "categoryId": config.YOUTUBE_KATEGORI_ID,
            "defaultLanguage": "tr",
        },
        "status": {
            "privacyStatus": config.YOUTUBE_VARSAYILAN_GIZLILIK,
            "selfDeclaredMadeForKids": False,
        },
    }


def video_yukle(
    video_yolu: Path,
    burs_adi: str,
    kurum: str,
    narrasyon_metni: str,
    basvuru_portal: str,
    basvuru_son_tarih: str,
    egitim_turu: list,
) -> Optional[str]:
    """
    YouTube'a video yükler.

    Args:
        video_yolu: Yüklenecek MP4 dosyasının yolu
        burs_adi: Burs programının adı
        kurum: Burs veren kurum adı
        narrasyon_metni: Video açıklaması için metin
        basvuru_portal: Başvuru URL'i
        basvuru_son_tarih: Son başvuru tarihi
        egitim_turu: Uygun öğretim türleri listesi

    Returns:
        YouTube video ID'si (başarılı yüklemede) veya None (hata durumunda)
    """
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError

    if not video_yolu.exists():
        logger.error(f"Video dosyası bulunamadı: {video_yolu}")
        return None

    logger.info(f"📤 YouTube yüklemesi başlıyor: {video_yolu.name}")
    dosya_boyutu = video_yolu.stat().st_size / (1024 * 1024)
    logger.info(f"   Dosya boyutu: {dosya_boyutu:.1f} MB")

    try:
        youtube = _youtube_servisi_al()
        metadata = _youtube_metadata_olustur(
            burs_adi=burs_adi,
            kurum=kurum,
            narrasyon_metni=narrasyon_metni,
            basvuru_portal=basvuru_portal,
            basvuru_son_tarih=basvuru_son_tarih,
            egitim_turu=egitim_turu,
        )

        # Resumable upload (büyük dosyalar için güvenilir)
        medya = MediaFileUpload(
            str(video_yolu),
            mimetype="video/mp4",
            resumable=True,
            chunksize=config.YOUTUBE_CHUNK_BOYUTU,
        )

        istek = youtube.videos().insert(
            part="snippet,status",
            body=metadata,
            media_body=medya,
        )

        # Yükleme döngüsü
        yanit = None
        while yanit is None:
            durum, yanit = istek.next_chunk()
            if durum:
                ilerleme = int(durum.progress() * 100)
                logger.info(f"   ⏫ Yükleniyor: %{ilerleme}")

        video_id = yanit["id"]
        video_url = f"https://www.youtube.com/shorts/{video_id}"
        logger.info(f"✅ YouTube yüklemesi tamamlandı!")
        logger.info(f"   🎬 Video ID: {video_id}")
        logger.info(f"   🔗 URL: {video_url}")

        return video_id

    except HttpError as e:
        logger.error(f"YouTube API hatası: {e.status_code} — {e.reason}")
        if e.status_code == 403:
            logger.error("   💡 Quota aşıldı! 24 saat sonra tekrar deneyin.")
        return None
    except Exception as e:
        logger.error(f"YouTube yükleme hatası: {e}")
        return None
