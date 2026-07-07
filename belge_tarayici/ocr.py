"""İsteğe bağlı OCR desteği (Tesseract).

Tesseract ayrı bir program olarak kurulmalıdır:
    https://github.com/UB-Mannheim/tesseract/wiki  (Windows)
Türkçe dil paketi için kurulumda "Turkish" seçilmelidir.

Tesseract kurulu değilse OCR sessizce atlanır ve kullanıcıya
açıklayıcı bir mesaj döndürülür — pipeline asla çökmez.
"""

from __future__ import annotations

import numpy as np

_INSTALL_MSG = (
    "OCR atlandı: Tesseract bulunamadı. Kurulum için: "
    "https://github.com/UB-Mannheim/tesseract/wiki adresinden indirin "
    "ve kurulumda Türkçe dil paketini seçin."
)


def ocr_available() -> bool:
    """Tesseract programı ve pytesseract paketi kullanılabilir mi?"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def extract_text(image: np.ndarray, lang: str = "tur+eng") -> str:
    """Görüntüden metin çıkarır; Tesseract yoksa bilgi mesajı döner."""
    try:
        import pytesseract
    except ImportError:
        return _INSTALL_MSG
    try:
        text = pytesseract.image_to_string(image, lang=lang)
    except pytesseract.TesseractNotFoundError:
        return _INSTALL_MSG
    except pytesseract.TesseractError:
        # İstenen dil paketi yoksa yalnızca İngilizce ile tekrar dene
        try:
            text = pytesseract.image_to_string(image, lang="eng")
        except Exception:
            return _INSTALL_MSG
    return text.strip()
