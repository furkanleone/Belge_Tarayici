"""Perspektif düzeltme: eğik çekilmiş belgeyi kuşbakışı hale getirir."""

from __future__ import annotations

import cv2
import numpy as np


def four_point_transform(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Sıralı 4 köşeden perspektif düzeltilmiş görüntü üretir.

    Çıktı boyutu, dörtgenin kenar uzunluklarından hesaplanır; böylece
    belgenin en-boy oranı korunur.
    """
    tl, tr, br, bl = corners.astype(np.float32)

    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)

    out_w = max(int(round(max(width_top, width_bottom))), 1)
    out_h = max(int(round(max(height_left, height_right))), 1)

    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]],
                   dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
    return cv2.warpPerspective(image, matrix, (out_w, out_h),
                               flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)
