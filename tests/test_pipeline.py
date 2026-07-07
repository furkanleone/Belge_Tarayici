"""Uçtan uca ve birim testler.

Çalıştırma (proje kökünden):
    python -m pytest tests/ -v
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from belge_tarayici import scan_document
from belge_tarayici.detector import detect_document, order_corners
from belge_tarayici.enhance import enhance, remove_shadows
from belge_tarayici.pdf import save_pdf
from belge_tarayici.transform import four_point_transform
from tools.make_sample import make_sample, DEFAULT_CORNERS


@pytest.fixture(scope="module")
def sample_photo():
    return make_sample()


def test_order_corners():
    """Karışık verilen köşeler TL, TR, BR, BL sırasına dizilmeli."""
    pts = np.array([[100, 100], [10, 100], [10, 10], [100, 10]], dtype=np.float32)
    ordered = order_corners(pts)
    assert np.allclose(ordered[0], [10, 10])     # sol-üst
    assert np.allclose(ordered[1], [100, 10])    # sağ-üst
    assert np.allclose(ordered[2], [100, 100])   # sağ-alt
    assert np.allclose(ordered[3], [10, 100])    # sol-alt


def test_detection_finds_document(sample_photo):
    """Sentetik fotoğrafta köşeler gerçek konumlara yakın bulunmalı."""
    corners, detected = detect_document(sample_photo)
    assert detected, "Belge tespit edilemedi"
    # Her köşe gerçek konumundan en fazla 30 px sapabilir
    err = np.linalg.norm(corners - DEFAULT_CORNERS, axis=1)
    assert err.max() < 30, f"Köşe hatası çok büyük: {err}"


def test_detection_fallback_on_blank():
    """Belge içermeyen düz görüntüde güvenli geri dönüş çalışmalı."""
    blank = np.full((400, 600, 3), 128, dtype=np.uint8)
    corners, detected = detect_document(blank)
    assert not detected
    assert np.allclose(corners[0], [0, 0])
    assert np.allclose(corners[2], [599, 399])


def test_perspective_transform_shape():
    """Dönüşüm çıktısı dörtgenin kenar uzunluklarına uymalı."""
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    corners = np.array([[50, 50], [449, 50], [449, 349], [50, 349]],
                       dtype=np.float32)
    warped = four_point_transform(img, corners)
    # Kenar uzunlukları: 449-50 = 399 ve 349-50 = 299 piksel
    assert warped.shape[:2] == (299, 399)


def test_shadow_removal_brightens_dark_corner(sample_photo):
    """Gölge kaldırma, karanlık köşedeki sayfa parlaklığını artırmalı."""
    result = scan_document(sample_photo, mode="color")
    warped, cleaned = result.warped, result.scanned
    # Sayfanın sağ alt bölgesi (gölgeli taraf) temizlikten sonra daha parlak olmalı
    h, w = warped.shape[:2]
    region = np.s_[int(h * 0.75):int(h * 0.95), int(w * 0.75):int(w * 0.95)]
    assert cleaned[region].mean() > warped[region].mean() + 20


def test_all_modes_run(sample_photo):
    """Üç çıktı modu da hatasız çalışmalı ve doğru tipte çıktı vermeli."""
    for mode in ("color", "gray", "bw"):
        result = scan_document(sample_photo, mode=mode)
        assert result.scanned.dtype == np.uint8
        if mode == "color":
            assert result.scanned.ndim == 3
        else:
            assert result.scanned.ndim == 2
    with pytest.raises(ValueError):
        enhance(sample_photo, mode="yanlis")


def test_bw_mode_is_binary(sample_photo):
    """Siyah-beyaz mod yalnızca 0 ve 255 değerleri içermeli."""
    result = scan_document(sample_photo, mode="bw")
    assert set(np.unique(result.scanned)) <= {0, 255}


def test_pdf_output(tmp_path, sample_photo):
    """PDF çıktısı geçerli bir dosya üretmeli."""
    result = scan_document(sample_photo)
    pdf = save_pdf([result.scanned, result.scanned], tmp_path / "out.pdf")
    assert pdf.exists() and pdf.stat().st_size > 1000
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_debug_outputs(sample_photo):
    """keep_debug=True üç ara adım görüntüsü döndürmeli."""
    result = scan_document(sample_photo, keep_debug=True)
    assert set(result.debug) == {"1_koseler", "2_duzeltilmis", "3_sonuc"}
