# 📄 Belge Tarayıcı (Document Scanner)

Telefonla çekilmiş eğik, gölgeli veya dengesiz aydınlatılmış belge fotoğraflarını **düzgün taranmış, yüksek kaliteli belgelere** dönüştüren tamamen yerel (local) çalışan bir görüntü işleme aracıdır. Verileriniz hiçbir dış sunucuya gönderilmez, tüm işlemler cihazınızda gerçekleşir.


## ✨ Özellikler

*   **🔍 Çok Stratejili Otomatik Kenar Tespiti:** Canny kenar tespiti, Otsu eşikleme ve gevşek Canny yöntemlerini bir arada kullanır. Çerçeve dışına taşan belgeler için otomatik siyah kenarlık ekleme desteği barındırır.
*   **📐 Perspektif Düzeltme (Kuşbakışı Görünüm):** Tespit edilen 4 köşeyi kullanarak homografi matrisi hesaplar ve belgenin orijinal en-boy oranını (aspect ratio) koruyarak doğrusal olmayan eğiklikleri giderir.
*   **☀️ Gelişmiş Gölge ve Vinyet Giderme:** Büyük çekirdekli morfolojik kapama ve medyan filtreleme ile sayfanın aydınlatma haritasını (background illumination map) çıkarır. Görüntüyü bu haritaya bölerek tüm gölgeleri ve ışık dengesizliklerini temizler.
*   **🎨 3 Farklı İyileştirme Modu:**
    *   `color` (Renkli): Renkleri canlı tutar, gölgeleri temizler ve keskinleştirir.
    *   `gray` (Gri Tonlama): Kontrastı otomatik gerer (contrast stretching) ve pürüzsüz bir gri çıktı verir.
    *   `bw` (Siyah-Beyaz / Fotokopi): Bölgesel aydınlatmaya duyarlı adaptif eşikleme (adaptive thresholding) ile net yazılar elde eder.
*   **📄 Çok Sayfalı PDF Desteği:** Birden fazla taranan görüntüyü tek bir PDF dosyasında birleştirir.
*   **📝 Entegre OCR (Metin Tanıma):** Tesseract OCR aracılığıyla taranan belgelerdeki Türkçe ve İngilizce metinleri otomatik olarak çıkarır.
*   **🌐 Modern Web Arayüzü:** Gradio tabanlı kullanıcı dostu web arayüzü ile sürükle-bırak kullanım imkanı sunar.
*   **🛡️ Güvenli Geri Dönüş (Fallback):** Belge kenarları tespit edilemezse sistem çökmez; tüm görüntüyü otomatik olarak belge kabul edip perspektif düzeltmeyi atlayarak gölge giderme ve iyileştirme adımlarına devam eder.

---

## 🚀 Kurulum

### 1. Gereksinimler
Projenin çalışması için bilgisayarınızda **Python 3.8+** sürümünün yüklü olması gerekmektedir.

### 2. Depoyu Klonlayın ve Bağımlılıkları Kurun
```bash
git clone https://github.com/KULLANICI_ADI/belge-tarayici.git
cd belge-tarayici
pip install -r requirements.txt
```

### 3. OCR Desteği İçin Tesseract Kurulumu (İsteğe Bağlı)
Eğer belgelerden metin okumak (OCR) istiyorsanız, sisteminize Tesseract motorunu kurmalısınız:

*   **Windows:** [UB-Mannheim Tesseract Yükleyicisi](https://github.com/UB-Mannheim/tesseract/wiki) sayfasından en son `.exe` dosyasını indirin. Kurulum adımlarında ek diller kısmından **Turkish** dil paketini seçmeyi unutmayın.
*   **Ubuntu/Debian:**
    ```bash
    sudo apt update
    sudo apt install tesseract-ocr tesseract-ocr-tur
    ```
*   **macOS:**
    ```bash
    brew install tesseract tesseract-lang
    ```

---

## 📖 Kullanım Kılavuzu

### 1. Komut Satırı Arayüzü (CLI)

[scan.py](file:///c:/Users/Emir%20Furkan%20ASLAN/Desktop/Belge_Tarayici/scan.py) dosyası üzerinden terminal aracılığıyla hızlıca tarama yapabilirsiniz:

```bash
# Tek bir fotoğrafı işle (Sonucu yanına '_taranmis.png' olarak kaydeder)
python scan.py foto.jpg

# Çıktıyı siyah-beyaz (fotokopi) modunda belirli bir dosyaya kaydet
python scan.py foto.jpg -m bw -o cikti.png

# Klasördeki tüm fotoğrafları tara ve tek bir PDF belgesinde birleştir
python scan.py belgeler/ --pdf tarama.pdf

# OCR ile metin çıkar, .txt olarak kaydet ve ara adımları (debug görüntüleri) görselleştir
python scan.py foto.jpg --ocr --debug
```

#### CLI Parametreleri
| Parametre | Kısa Yol | Açıklama | Varsayılan |
| :--- | :--- | :--- | :--- |
| `input` | | Girdi görüntü dosyası veya klasör yolu. | *Zorunlu* |
| `--mode` | `-m` | Çıktı modu seçeneği: `color`, `gray`, `bw` | `color` |
| `--output` | `-o` | Çıktı dosya/klasör yolu. | Yanına `_taranmis` ekler |
| `--pdf` | | Tüm sayfaları birleştireceği çıktı PDF dosya adı. | Kapalı |
| `--ocr` | | Aktifleştirildiğinde Tesseract ile metin okuyup `.txt` yazar. | Kapalı |
| `--debug` | | Ara işleme adımlarını (kenar tespiti vb.) diske kaydeder. | Kapalı |

---

### 2. Web Arayüzü

Gradio tabanlı grafiksel arayüzü başlatmak için:

```bash
python app.py
```
Arayüz başladıktan sonra tarayıcınızda otomatik olarak **`http://127.0.0.1:7860`** adresi açılacaktır. Bu arayüz üzerinden dosyalarınızı sürükleyip bırakabilir, mod seçebilir ve anlık olarak sonuçları görebilirsiniz.

---

### 3. Python API Kullanımı

Kendi Python projelerinizde entegre olarak kullanmak için `belge_tarayici` paketini içe aktarabilirsiniz:

```python
from pathlib import Path
from belge_tarayici import scan_document

# Görüntü dosyası yolu veya doğrudan numpy dizisi (BGR formatında) verilebilir
result = scan_document("foto.jpg", mode="bw", do_ocr=True)

# Sonuçları inceleme
if result.detected:
    print("Belge kenarları başarıyla tespit edildi.")
else:
    print("Uyarı: Kenarlar bulunamadı, tüm görüntü kullanıldı.")

print(f"Tespit Edilen Köşeler:\n{result.corners}")
print(f"Çıkarılan Metin (OCR):\n{result.text}")

# İşlenmiş görüntüyü (numpy dizisi) OpenCV ile kaydetme veya gösterme
import cv2
cv2.imwrite("taranmis.png", result.scanned)
```

#### API Ayrıntıları: `ScanResult` Veri Yapısı
`scan_document` fonksiyonu geriye bir `ScanResult` nesnesi döndürür. Bu nesnenin içeriği şöyledir:
*   `scanned` (`np.ndarray`): İyileştirme işlemleri uygulanmış nihai taranmış görüntü.
*   `corners` (`np.ndarray`): Orijinal çözünürlükteki 4 köşe noktası koordinatı.
*   `detected` (`bool`): Kenar tespitinin başarılı olup olmadığı bilgisi.
*   `warped` (`np.ndarray`): Perspektif düzeltilmiş ancak gölge temizleme yapılmamış ham kesilmiş görüntü.
*   `text` (`str`): OCR yapıldıysa elde edilen metin içeriği.
*   `debug` (`dict`): `keep_debug=True` ise ara adımların görüntü haritası (`1_koseler`, `2_duzeltilmis`, `3_sonuc`).

---

## 🔬 Çalışma Mantığı ve Algoritma Detayları

```
Girdi Fotoğrafı ──► Kenar Tespiti ──► Perspektif Düzeltme ──► Gölge Kaldırma ──► İyileştirme ──► PNG / PDF Çıktı
                     (Multi-Scale       (Homografi &          (Morfolojik       (Moda göre
                      & Çoklu Metot)     Aspect Ratio)         Filtreleme)       Eşikleme / Keskinlik)
```

### 1. Kenar Tespiti (`detector.py`)
Görüntü işlemenin en kritik adımıdir:
*   **Çözünürlük Standartlaştırma:** Görüntü, gürültüleri azaltmak ve işlem hızını optimize etmek amacıyla `640` piksel genişliğe (`WORK_WIDTH`) ölçeklendirilir.
*   **Kenarlık Desteği (`PAD`):** Görüntünün etrafına siyah bir çerçeve eklenir. Bu sayede belgenin kenarları fotoğraf karesinin sınırına dayanmış veya taşmış olsa bile OpenCV konturlarının kapalı bir alan oluşturması sağlanır.
*   **Çoklu Aday Filtreleme:** Canny (klasik), Otsu Eşikleme ve Gevşek Canny yöntemleriyle 3 ayrı kenar haritası çıkarılır.
*   **Uç Nokta Belirleme:** Konturların dışbükey zarfı (Convex Hull) alınarak `approxPolyDP` ile 4 köşeli en geniş dışbükey çokgen aranır. Adaylar alan büyüklüğü ve parlaklık oranlarına göre puanlanarak en başarılı dörtgen seçilir.

### 2. Perspektif Düzeltme (`transform.py`)
*   Seçilen 4 köşe noktası; sol-üst, sağ-üst, sağ-alt ve sol-alt (`TL, TR, BR, BL`) olacak şekilde sıralanır.
*   Köşeler arası Öklid mesafeleri hesaplanarak belgenin olabilecek en doğru en-boy oranı (`out_w`, `out_h`) belirlenir.
*   `cv2.getPerspectiveTransform` ve `cv2.warpPerspective` fonksiyonları (kübik interpolasyon ile) kullanılarak eğik duran belge düzleştirilir.

### 3. Gölge ve Işık Düzensizliklerini Kaldırma (`enhance.py`)
*   Düzleştirilen görüntünün kanallarında büyük bir eliptik yapı elemanı (`31x31`) kullanılarak morfolojik kapama (closing) işlemi uygulanır.
*   Elde edilen görüntü medyan filtresiyle yumuşatılarak belgenin yalnızca ışık/gölge dağılımını içeren bir **aydınlatma haritası** oluşturulur.
*   Orijinal kanal görüntüsü bu aydınlatma haritasına bölünerek (`cv2.divide`), gölgeler beyaza çekilir ve homojen bir arka plan elde edilir.

### 4. İyileştirme (`enhance.py`)
*   **Renkli:** Unsharp mask yöntemiyle görüntü keskinleştirilir.
*   **Gri Tonlama:** Görüntünün kontrastını artırmak için en alttaki %1 ve en üstteki %99'luk piksel değerleri kırpılarak kontrast yayılımı uygulanır.
*   **Siyah-Beyaz:** Gauss dağılımlı adaptif eşikleme yöntemi kullanılarak yerel piksellere göre eşik değeri dinamik olarak belirlenir ve ardından tuz-biber gürültülerini engellemek için medyan filtresi uygulanır.

---

## 🧪 Testler ve Doğrulama

Projeyi test etmek için bir test paketi mevcuttur. Testler, gerçek bir kameraya veya görüntü veritabanına ihtiyaç duymadan çalışabilmek adına sentetik bir görüntü oluşturucu kullanır:

1.  [tools/make_sample.py](file:///c:/Users/Emir%20Furkan%20ASLAN/Desktop/Belge_Tarayici/tools/make_sample.py) betiği çalıştırılarak yapay bir ahşap masa üzerine yerleştirilmiş, perspektifi bozuk, gölgeli ve gürültülü yapay bir belge fotoğrafı üretilir.
2.  `pytest` aracı ile uçtan uca tüm testler koşturulur:

```bash
# Testleri çalıştırmak için
python -m pytest tests/ -v
```

Bu testler; köşe bulma algoritmasının hassasiyetini, gölge temizleme performansını, PDF çıktısının doğruluğunu ve tüm iyileştirme modlarını doğrular.

---

## 📁 Proje Yapısı

```text
Belge_Tarayici/
├── belge_tarayici/           # Çekirdek Python paketi
│   ├── __init__.py           # Paket tanımlayıcısı ve dışa açılan API'ler
│   ├── detector.py           # Kenar ve 4 köşe tespit algoritmaları
│   ├── transform.py          # Perspektif düzeltme (homografi) işlemleri
│   ├── enhance.py            # Gölge temizleme, keskinleştirme ve mod filtreleri
│   ├── ocr.py                # Tesseract OCR entegrasyonu ve hata yönetimi
│   ├── pdf.py                # PIL tabanlı PDF dönüştürücü
│   └── pipeline.py           # Uçtan uca iş akışı (pipeline) yönetimi
├── tests/                    # Otomatik testler
│   └── test_pipeline.py      # pytest test senaryoları
├── tools/                    # Yardımcı araçlar
│   └── make_sample.py        # Sentetik belge/arka plan oluşturucu
├── examples/                 # Örnek görsel çıktıları barındıran klasör
├── app.py                    # Gradio Web Arayüzü uygulaması
├── scan.py                   # Komut Satırı (CLI) uygulaması
├── requirements.txt          # Gerekli kütüphane listesi
└── README.md                 # Proje dokümantasyonu (Bu dosya)
```

---

## 📜 Lisans

Bu proje **MIT Lisansı** altında sunulmaktadır. Ticari ve kişisel projelerinizde dilediğiniz gibi kullanabilir, değiştirebilir ve dağıtabilirsiniz.
