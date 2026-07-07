"""Belge kenarlarının (dört köşenin) tespiti.

Strateji: görüntü küçültülür ve etrafına siyah kenarlık eklenir —
böylece çerçeveye dayanan/taşan sayfaların konturu da kapanır.
Birden fazla yöntemle (Canny, Otsu, gevşek Canny) dörtgen adayları
aranır; dörtgen bulunamayan büyük konturlarda dışbükey zarftan köşe
çıkarılır. En geniş geçerli aday kazanır. Hiçbir aday yoksa görüntünün
tamamı belge kabul edilir (güvenli geri dönüş).
"""

from __future__ import annotations

import cv2
import numpy as np

# Tespit sırasında kullanılacak çalışma genişliği (piksel).
# Küçük görüntüde kontur aramak hem hızlı hem daha kararlıdır.
WORK_WIDTH = 640

# Çalışma görüntüsünün etrafına eklenen siyah kenarlık (piksel).
# Sayfa çerçeveye dayansa bile konturunun kapanmasını sağlar.
PAD = 20

# Bir dörtgenin belge sayılabilmesi için görüntü alanının
# en az bu oranını kaplaması gerekir.
MIN_AREA_RATIO = 0.15

# Bu oranın üzerindeki dörtgenler "tüm kare" sayılır ve tespit
# kabul edilmez — düz zeminlerde yanlış pozitifleri önler
# (o durumda güvenli geri dönüş zaten aynı sonucu verir).
MAX_AREA_RATIO = 0.98


def order_corners(pts: np.ndarray) -> np.ndarray:
    """Nokta kümesinden 4 köşeyi TL, TR, BR, BL sırasında çıkarır.

    4'ten fazla nokta da verilebilir (ör. dışbükey zarf); uç noktalar
    x+y ve y-x ölçütleriyle seçilir.
    """
    pts = pts.reshape(-1, 2).astype(np.float32)
    ordered = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = pts[:, 1] - pts[:, 0]
    ordered[0] = pts[np.argmin(s)]   # sol-üst: x+y en küçük
    ordered[2] = pts[np.argmax(s)]   # sağ-alt: x+y en büyük
    ordered[1] = pts[np.argmin(d)]   # sağ-üst: y-x en küçük
    ordered[3] = pts[np.argmax(d)]   # sol-alt: y-x en büyük
    return ordered


def _candidate_edges(gray: np.ndarray) -> list[np.ndarray]:
    """Farklı ön işlemlerle kenar haritası adayları üretir."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    close_k = np.ones((5, 5), np.uint8)
    candidates = []

    # 1) Klasik Canny + kapama (kopuk kenarları birleştirir)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, close_k, iterations=2)
    candidates.append(edges)

    # 2) Otsu eşikleme — belge/zemin kontrastı yüksekse çok kararlı
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    candidates.append(cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_k))

    # 3) Daha gevşek Canny — düşük kontrastlı sahneler için
    edges2 = cv2.Canny(blurred, 30, 90)
    edges2 = cv2.morphologyEx(edges2, cv2.MORPH_CLOSE, close_k, iterations=3)
    candidates.append(edges2)

    return candidates


def _quad_from_contour(contour: np.ndarray) -> np.ndarray | None:
    """Tek konturdan dörtgen çıkarmayı dener.

    Önce klasik approxPolyDP; kontur gürültülü/kesikse dışbükey zarf
    üzerinde tekrar denenir; o da olmazsa zarfın uç noktalarından
    köşe türetilir (sayfa içi çizgilerin konturu bölmesine dayanıklı).
    """
    peri = cv2.arcLength(contour, True)
    for eps in (0.02, 0.03, 0.05):
        approx = cv2.approxPolyDP(contour, eps * peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            return approx.reshape(4, 2).astype(np.float32)

    hull = cv2.convexHull(contour)
    hull_peri = cv2.arcLength(hull, True)
    for eps in (0.02, 0.05, 0.08):
        approx = cv2.approxPolyDP(hull, eps * hull_peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            return approx.reshape(4, 2).astype(np.float32)

    # Son çare: zarfın uç noktaları. Zarf alanının büyük kısmını
    # kapsıyorsa güvenilir bir köşe kümesidir.
    corners = order_corners(hull)
    quad_area = cv2.contourArea(corners)
    hull_area = cv2.contourArea(hull)
    if hull_area > 0 and quad_area / hull_area > 0.8:
        return corners
    return None


def _find_quads(edge_map: np.ndarray, min_area: float) -> list[np.ndarray]:
    """Kenar haritasındaki büyük konturlardan dörtgen adayları toplar."""
    contours, _ = cv2.findContours(edge_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    quads = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
        if cv2.contourArea(contour) < min_area:
            break
        quad = _quad_from_contour(contour)
        if quad is not None:
            quads.append(quad)
    return quads


def detect_document(image: np.ndarray) -> tuple[np.ndarray, bool]:
    """Belgenin 4 köşesini orijinal görüntü koordinatlarında döndürür.

    Returns:
        (köşeler [4x2 float32, sıralı], tespit başarılı mı)
        Başarısızsa köşeler görüntünün tamamıdır.
    """
    h, w = image.shape[:2]
    scale = WORK_WIDTH / w
    small = cv2.resize(image, (WORK_WIDTH, int(h * scale)))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    # Siyah kenarlık: çerçeveye dayanan sayfanın konturunu kapatır
    padded = cv2.copyMakeBorder(gray, PAD, PAD, PAD, PAD,
                                cv2.BORDER_CONSTANT, value=0)

    sh, sw = small.shape[:2]
    frame_area = sh * sw
    min_area = MIN_AREA_RATIO * frame_area
    max_area = MAX_AREA_RATIO * frame_area

    # "Parlak sayfa" maskesi: adaylar yalnızca alana göre değil, içlerinin
    # ne kadar sayfa pikseliyle dolu olduğuna göre puanlanır. Böylece koyu
    # zemini de kapsayan gevşek dörtgenler, sayfaya tam oturan dörtgene
    # karşı kaybeder.
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bright_mask = cv2.threshold(blurred, 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    def score(q: np.ndarray, area: float) -> float:
        region = np.zeros((sh, sw), np.uint8)
        cv2.fillConvexPoly(region, q.astype(np.int32), 1)
        inside = bright_mask[region == 1]
        if inside.size == 0:
            return 0.0
        page_ratio = float(inside.mean()) / 255.0
        return area * page_ratio ** 2

    best_quad = None
    best_score = 0.0
    for edge_map in _candidate_edges(padded):
        for quad in _find_quads(edge_map, min_area):
            # Kenarlık ofsetini geri al, çalışma çerçevesine kırp
            q = quad - PAD
            q[:, 0] = np.clip(q[:, 0], 0, sw - 1)
            q[:, 1] = np.clip(q[:, 1], 0, sh - 1)
            area = cv2.contourArea(q)
            if not (min_area <= area <= max_area):
                continue
            s = score(q, area)
            if s > best_score:
                best_quad = q
                best_score = s

    if best_quad is None:
        # Güvenli geri dönüş: görüntünün tamamı
        corners = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]],
                           dtype=np.float32)
        return corners, False

    corners = order_corners(best_quad) / scale
    corners[:, 0] = np.clip(corners[:, 0], 0, w - 1)
    corners[:, 1] = np.clip(corners[:, 1], 0, h - 1)
    return corners, True


def draw_corners(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Hata ayıklama için köşeleri ve çerçeveyi görüntüye çizer."""
    vis = image.copy()
    pts = corners.astype(int)
    cv2.polylines(vis, [pts.reshape(-1, 1, 2)], True, (0, 200, 0), 3)
    for x, y in pts:
        cv2.circle(vis, (int(x), int(y)), 10, (0, 0, 255), -1)
    return vis
