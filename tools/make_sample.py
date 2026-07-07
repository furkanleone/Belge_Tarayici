#!/usr/bin/env python3
"""Sentetik test görüntüsü üretir: ahşap zemin üzerinde eğik çekilmiş,
gölgeli bir belge fotoğrafı taklidi. Gerçek fotoğraf olmadan pipeline'ı
test etmek ve README görselleri üretmek için kullanılır.

Kullanım:
    python tools/make_sample.py [cikti.jpg]
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np


def make_document(w: int = 800, h: int = 1100) -> np.ndarray:
    """Metin satırları ve başlık içeren beyaz bir 'belge' üretir."""
    doc = np.full((h, w, 3), 250, dtype=np.uint8)

    cv2.putText(doc, "BELGE TARAYICI", (60, 90),
                cv2.FONT_HERSHEY_DUPLEX, 1.6, (30, 30, 30), 3)
    cv2.putText(doc, "Ornek Test Belgesi", (60, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 80, 80), 2)
    cv2.line(doc, (60, 180), (w - 60, 180), (150, 150, 150), 2)

    # Sahte paragraf satırları (değişken uzunlukta gri çubuklar)
    rng = np.random.default_rng(42)
    y = 240
    while y < h - 120:
        line_w = int(rng.uniform(0.55, 0.92) * (w - 120))
        cv2.rectangle(doc, (60, y), (60 + line_w, y + 14), (90, 90, 90), -1)
        y += 38
        if rng.random() < 0.15:  # paragraf boşluğu
            y += 30

    cv2.putText(doc, "Sayfa 1 / 1", (w - 220, h - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 120, 120), 2)
    return doc


def make_background(w: int = 1600, h: int = 1200) -> np.ndarray:
    """Ahşap masa görünümlü koyu, dokulu zemin üretir."""
    rng = np.random.default_rng(7)
    base = np.full((h, w, 3), (40, 60, 95), dtype=np.float32)  # BGR kahve
    # Ahşap damarı: yatay sinüs dalgaları + gürültü
    yy = np.arange(h).reshape(-1, 1)
    grain = 12 * np.sin(yy / 23.0) + rng.normal(0, 6, (h, w))
    base += grain[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def compose_photo(doc: np.ndarray, bg: np.ndarray,
                  corners: np.ndarray) -> np.ndarray:
    """Belgeyi zemine perspektifli yerleştirir, gölge ve gürültü ekler."""
    h, w = bg.shape[:2]
    dh, dw = doc.shape[:2]
    src = np.array([[0, 0], [dw - 1, 0], [dw - 1, dh - 1], [0, dh - 1]],
                   dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src, corners.astype(np.float32))

    warped = cv2.warpPerspective(doc, matrix, (w, h))
    mask = cv2.warpPerspective(np.full((dh, dw), 255, np.uint8), matrix, (w, h))
    photo = bg.copy()
    photo[mask > 0] = warped[mask > 0]

    # Köşegen gölge: sol üstten sağ alta doğru kararan aydınlatma
    xx, yy = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    shade = 1.0 - 0.45 * ((xx + yy) / 2.0) ** 1.5
    photo = (photo.astype(np.float32) * shade[..., None]).astype(np.uint8)

    # Hafif sensör gürültüsü ve bulanıklık (telefon kamerası taklidi)
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 4, photo.shape).astype(np.float32)
    photo = np.clip(photo.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    photo = cv2.GaussianBlur(photo, (3, 3), 0)
    return photo


DEFAULT_CORNERS = np.array([[380, 150], [1280, 230], [1180, 1080], [280, 990]],
                           dtype=np.float32)


def make_sample(corners: np.ndarray | None = None) -> np.ndarray:
    """Tam sentetik test fotoğrafı döndürür (BGR)."""
    corners = DEFAULT_CORNERS if corners is None else corners
    return compose_photo(make_document(), make_background(), corners)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("examples/ornek_foto.jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    photo = make_sample()
    ok, buf = cv2.imencode(".jpg", photo, [cv2.IMWRITE_JPEG_QUALITY, 92])
    buf.tofile(str(out))
    print(f"Örnek fotoğraf üretildi: {out} ({photo.shape[1]}x{photo.shape[0]})")
