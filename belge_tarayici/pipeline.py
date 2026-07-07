"""Uçtan uca tarama hattı: yükle -> tespit -> düzelt -> iyileştir -> OCR."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .detector import detect_document, draw_corners
from .enhance import enhance
from .ocr import extract_text
from .transform import four_point_transform


@dataclass
class ScanResult:
    """Bir belgenin tarama sonucu ve ara adımları."""
    scanned: np.ndarray                 # nihai iyileştirilmiş çıktı
    corners: np.ndarray                 # tespit edilen 4 köşe (orijinalde)
    detected: bool                      # köşe tespiti başarılı mıydı
    warped: np.ndarray                  # perspektif düzeltilmiş ham görüntü
    text: str = ""                      # OCR metni (istenirse)
    debug: dict[str, np.ndarray] = field(default_factory=dict)


def load_image(path: str | Path) -> np.ndarray:
    """Görüntüyü diskten okur (Unicode/Türkçe karakterli yollarla uyumlu)."""
    data = np.fromfile(str(path), dtype=np.uint8)  # cv2.imread Türkçe yolda başarısız olur
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Görüntü okunamadı: {path}")
    return image


def save_image(image: np.ndarray, path: str | Path) -> None:
    """Görüntüyü diske yazar (Unicode/Türkçe karakterli yollarla uyumlu)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(path.suffix or ".png", image)
    if not ok:
        raise ValueError(f"Görüntü kodlanamadı: {path}")
    buf.tofile(str(path))


def scan_document(image: np.ndarray | str | Path,
                  mode: str = "color",
                  do_ocr: bool = False,
                  keep_debug: bool = False) -> ScanResult:
    """Tek bir belge fotoğrafını uçtan uca tarar.

    Args:
        image: BGR numpy dizisi ya da dosya yolu.
        mode: "color" | "gray" | "bw" çıktı modu.
        do_ocr: True ise düzeltilmiş görüntüden metin çıkarılır.
        keep_debug: True ise ara adım görüntüleri sonuçta saklanır.
    """
    if isinstance(image, (str, Path)):
        image = load_image(image)

    corners, detected = detect_document(image)
    warped = four_point_transform(image, corners)
    scanned = enhance(warped, mode=mode)
    text = extract_text(scanned if mode != "color" else warped) if do_ocr else ""

    debug = {}
    if keep_debug:
        debug = {
            "1_koseler": draw_corners(image, corners),
            "2_duzeltilmis": warped,
            "3_sonuc": scanned,
        }

    return ScanResult(scanned=scanned, corners=corners, detected=detected,
                      warped=warped, text=text, debug=debug)
