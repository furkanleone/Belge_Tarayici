"""Belge Tarayıcı — telefon fotoğrafından taranmış belgeye.

Pipeline: kenar tespiti -> perspektif düzeltme -> gölge temizleme
-> keskinleştirme -> (isteğe bağlı) OCR -> PDF çıktı.
"""

from .pipeline import scan_document, ScanResult

__version__ = "1.0.0"
__all__ = ["scan_document", "ScanResult", "__version__"]
