#!/usr/bin/env python3
"""Belge Tarayıcı — komut satırı arayüzü.

Örnekler:
    python scan.py foto.jpg
    python scan.py foto.jpg -m bw -o cikti.png
    python scan.py klasor/ --pdf tarama.pdf
    python scan.py foto.jpg --ocr --debug
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from belge_tarayici import scan_document, __version__
from belge_tarayici.enhance import MODES
from belge_tarayici.pdf import save_pdf
from belge_tarayici.pipeline import save_image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def collect_inputs(target: Path) -> list[Path]:
    """Dosya ya da klasörden işlenecek görüntü listesini çıkarır."""
    if target.is_file():
        return [target]
    if target.is_dir():
        files = sorted(p for p in target.iterdir()
                       if p.suffix.lower() in IMAGE_EXTS)
        if not files:
            sys.exit(f"Hata: {target} klasöründe görüntü dosyası yok.")
        return files
    sys.exit(f"Hata: {target} bulunamadı.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Telefon fotoğrafını taranmış belgeye çevirir.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", type=Path,
                        help="Görüntü dosyası ya da görüntü klasörü")
    parser.add_argument("-m", "--mode", choices=MODES, default="color",
                        help="Çıktı modu")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Çıktı dosyası/klasörü (varsayılan: yanına _taranmis eki ile)")
    parser.add_argument("--pdf", type=Path, default=None, metavar="DOSYA.pdf",
                        help="Tüm sayfaları tek PDF'te birleştir")
    parser.add_argument("--ocr", action="store_true",
                        help="OCR ile metni çıkar ve .txt olarak kaydet")
    parser.add_argument("--debug", action="store_true",
                        help="Ara adım görüntülerini de kaydet")
    parser.add_argument("-V", "--version", action="version",
                        version=f"Belge Tarayıcı {__version__}")
    args = parser.parse_args()

    inputs = collect_inputs(args.input)
    pages = []

    for i, path in enumerate(inputs, 1):
        print(f"[{i}/{len(inputs)}] {path.name} işleniyor...", flush=True)
        result = scan_document(path, mode=args.mode, do_ocr=args.ocr,
                               keep_debug=args.debug)
        if not result.detected:
            print(f"  ! Uyarı: belge kenarları bulunamadı, "
                  f"görüntünün tamamı kullanıldı.")

        # Çıktı yolunu belirle
        if args.output is None:
            out_path = path.with_name(f"{path.stem}_taranmis.png")
        elif len(inputs) > 1 or args.output.is_dir():
            args.output.mkdir(parents=True, exist_ok=True)
            out_path = args.output / f"{path.stem}_taranmis.png"
        else:
            out_path = args.output

        save_image(result.scanned, out_path)
        print(f"  -> {out_path}")

        if args.ocr and result.text:
            txt_path = out_path.with_suffix(".txt")
            txt_path.write_text(result.text, encoding="utf-8")
            print(f"  -> {txt_path} ({len(result.text)} karakter)")

        if args.debug:
            for name, img in result.debug.items():
                dbg_path = out_path.with_name(f"{out_path.stem}_{name}.png")
                save_image(img, dbg_path)
                print(f"  -> {dbg_path}")

        pages.append(result.scanned)

    if args.pdf:
        pdf_path = save_pdf(pages, args.pdf)
        print(f"\nPDF oluşturuldu: {pdf_path} ({len(pages)} sayfa)")

    print("\nTamamlandı.")


if __name__ == "__main__":
    main()
