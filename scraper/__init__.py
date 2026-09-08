"""
scraper/ — Burs duyurusu çekme modülleri

Faz 1: MockScraper (pipeline testi için)
Faz 2: Gerçek web scraper'lar (TBB, YÖK, vakıf siteleri vb.)
"""

from .base_scraper import BaseScraper, HamDuyuru
from .mock_scraper import MockScraper

__all__ = ["BaseScraper", "HamDuyuru", "MockScraper"]
