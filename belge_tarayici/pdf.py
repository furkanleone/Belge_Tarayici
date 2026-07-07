"""Taranan sayfaları tek PDF dosyasında birleştirme."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def _to_pil(image: np.ndarray) -> Image.Image:
    """OpenCV (BGR) görüntüsünü PIL (RGB) görüntüsüne çevirir."""
    if image.ndim == 2:
        return Image.fromarray(image).convert("RGB")
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def save_pdf(pages: list[np.ndarray], output_path: str | Path,
             dpi: int = 200) -> Path:
    """Sayfa görüntülerini tek PDF olarak kaydeder."""
    if not pages:
        raise ValueError("PDF için en az bir sayfa gerekli.")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pil_pages = [_to_pil(p) for p in pages]
    pil_pages[0].save(
        output_path, "PDF",
        resolution=dpi,
        save_all=len(pil_pages) > 1,
        append_images=pil_pages[1:],
    )
    return output_path
