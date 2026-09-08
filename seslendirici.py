"""
seslendirici.py — edge-tts ile Türkçe TTS ses üretimi
Ses: tr-TR-AhmetNeural (ücretsiz, Microsoft Edge TTS)
Çıktı: ciktilar/sesler/{burs_id}.mp3
"""

import asyncio
import logging
from pathlib import Path

import edge_tts
from moviepy import AudioFileClip

import config

logger = logging.getLogger(__name__)


async def _ses_uret_async(metin: str, cikti_yolu: Path) -> None:
    """
    Asenkron TTS üretimi.

    Args:
        metin: Seslendirilecek metin
        cikti_yolu: MP3 dosyasının kaydedileceği yol
    """
    communicate = edge_tts.Communicate(
        text=metin,
        voice=config.TTS_SES,
        rate=config.TTS_RATE,
        pitch=config.TTS_PITCH,
    )
    await communicate.save(str(cikti_yolu))
    logger.debug(f"TTS async tamamlandı: {cikti_yolu}")


def seslendir(metin: str, burs_id: str) -> tuple[Path, float]:
    """
    Metni sese dönüştürür ve MP3 dosyası oluşturur.

    Args:
        metin: Seslendirilecek Türkçe metin
        burs_id: Benzersiz burs kimliği (dosya adlandırma için)

    Returns:
        tuple: (mp3_dosya_yolu, ses_suresi_saniye)

    Raises:
        RuntimeError: TTS üretimi başarısız olursa
    """
    cikti_yolu = config.SES_DIR / f"{burs_id}.mp3"

    logger.info(f"🎙️ TTS başlıyor: {burs_id} ({len(metin.split())} kelime)")

    try:
        # Windows'ta event loop uyumluluk sorunu yaşanabilir; yeni loop oluştur
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Jupyter/nest gibi ortamlarda zaten çalışan loop var
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        _ses_uret_async(metin, cikti_yolu)
                    )
                    future.result(timeout=120)
            else:
                loop.run_until_complete(_ses_uret_async(metin, cikti_yolu))
        except RuntimeError:
            # "no current event loop" hatası
            asyncio.run(_ses_uret_async(metin, cikti_yolu))

    except Exception as e:
        raise RuntimeError(f"TTS üretimi başarısız ({burs_id}): {e}") from e

    if not cikti_yolu.exists():
        raise RuntimeError(f"TTS dosyası oluşturulmadı: {cikti_yolu}")

    # Ses süresi ölç
    sure = _ses_suresi_olc(cikti_yolu)

    logger.info(
        f"✅ Ses oluşturuldu: {cikti_yolu.name} | "
        f"Süre: {sure:.1f}s | "
        f"Boyut: {cikti_yolu.stat().st_size / 1024:.1f} KB"
    )

    return cikti_yolu, sure


def _ses_suresi_olc(mp3_yolu: Path) -> float:
    """
    MoviePy kullanarak MP3 dosyasının süresini ölçer.

    Args:
        mp3_yolu: MP3 dosya yolu

    Returns:
        Ses süresi (saniye)
    """
    try:
        with AudioFileClip(str(mp3_yolu)) as ses:
            return ses.duration
    except Exception as e:
        logger.warning(f"Ses süresi ölçülemedi: {e} — varsayılan 60s kullanılıyor")
        return 60.0
