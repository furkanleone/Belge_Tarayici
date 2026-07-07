"""Görüntü iyileştirme: gölge kaldırma, keskinleştirme, tarayıcı görünümü.

Gölge kaldırma yaklaşımı: büyük çekirdekli morfolojik kapama +
medyan bulanıklaştırma ile sayfanın "aydınlatma haritası" kestirilir;
görüntü bu haritaya bölünerek homojen aydınlatma elde edilir.
Metin gibi ince detaylar haritada kaybolduğu için bölme işlemi
yalnızca gölgeleri/vinyetlemeyi giderir, içeriğe dokunmaz.
"""

from __future__ import annotations

import cv2
import numpy as np

MODES = ("color", "gray", "bw")


def _illumination_map(channel: np.ndarray, kernel: int = 31) -> np.ndarray:
    """Tek kanalın arka plan (aydınlatma) kestirimini üretir."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel))
    background = cv2.morphologyEx(channel, cv2.MORPH_CLOSE, k)
    background = cv2.medianBlur(background, kernel if kernel % 2 == 1 else kernel + 1)
    return background


def remove_shadows(image: np.ndarray) -> np.ndarray:
    """Gölgeleri ve dengesiz aydınlatmayı her kanalda ayrı giderir."""
    channels = cv2.split(image) if image.ndim == 3 else [image]
    cleaned = []
    for ch in channels:
        bg = _illumination_map(ch)
        # Kanalı aydınlatma haritasına böl: gölgeler beyaza normalize olur
        norm = cv2.divide(ch, bg, scale=255)
        cleaned.append(norm)
    result = cv2.merge(cleaned) if len(cleaned) > 1 else cleaned[0]
    return result


def sharpen(image: np.ndarray, amount: float = 0.7) -> np.ndarray:
    """Unsharp mask ile hafif keskinleştirme."""
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=2.0)
    return cv2.addWeighted(image, 1 + amount, blurred, -amount, 0)


def enhance(image: np.ndarray, mode: str = "color") -> np.ndarray:
    """Düzleştirilmiş belgeyi seçilen modda iyileştirir.

    Modlar:
        color — gölgesiz, keskin renkli çıktı
        gray  — gölgesiz gri tonlama
        bw    — yüksek kontrastlı siyah-beyaz (fotokopi görünümü)
    """
    if mode not in MODES:
        raise ValueError(f"Geçersiz mod: {mode!r}. Seçenekler: {MODES}")

    cleaned = remove_shadows(image)

    if mode == "color":
        return sharpen(cleaned)

    gray = cv2.cvtColor(cleaned, cv2.COLOR_BGR2GRAY) if cleaned.ndim == 3 else cleaned

    if mode == "gray":
        # Kontrastı nazikçe ger: %1'lik uç değerleri kırparak normalize et
        lo, hi = np.percentile(gray, (1, 99))
        if hi > lo:
            gray = np.clip((gray.astype(np.float32) - lo) * 255.0 / (hi - lo), 0, 255)
            gray = gray.astype(np.uint8)
        return sharpen(gray)

    # bw: adaptif eşikleme — bölgesel aydınlatma farklarına dayanıklı
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, blockSize=25, C=15)
    # Tuz-biber gürültüsünü temizle
    bw = cv2.medianBlur(bw, 3)
    return bw
