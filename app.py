#!/usr/bin/env python3
"""Belge Tarayıcı — Gradio web arayüzü.

Çalıştırma:
    python app.py
Ardından tarayıcıda http://127.0.0.1:7860 adresini açın.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import gradio as gr
import numpy as np

from belge_tarayici import scan_document
from belge_tarayici.detector import draw_corners
from belge_tarayici.ocr import ocr_available
from belge_tarayici.pdf import save_pdf

MODE_LABELS = {"Renkli": "color", "Gri tonlama": "gray", "Siyah-Beyaz": "bw"}


def process(image: np.ndarray, mode_label: str, do_ocr: bool):
    """Gradio geri çağrısı: RGB görüntü alır, sonuçları döndürür."""
    if image is None:
        raise gr.Error("Lütfen önce bir belge fotoğrafı yükleyin.")

    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    result = scan_document(bgr, mode=MODE_LABELS[mode_label], do_ocr=do_ocr)

    corners_vis = cv2.cvtColor(draw_corners(bgr, result.corners), cv2.COLOR_BGR2RGB)
    scanned = result.scanned
    scanned_rgb = (cv2.cvtColor(scanned, cv2.COLOR_BGR2RGB)
                   if scanned.ndim == 3 else scanned)

    pdf_path = Path(tempfile.mkdtemp()) / "tarama.pdf"
    save_pdf([scanned], pdf_path)

    status = ("✅ Belge kenarları tespit edildi." if result.detected
              else "⚠️ Kenarlar bulunamadı; görüntünün tamamı kullanıldı.")
    text = result.text if do_ocr else "(OCR kapalı)"

    return corners_vis, scanned_rgb, str(pdf_path), status, text


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Belge Tarayıcı") as demo:
        gr.Markdown(
            "# 📄 Belge Tarayıcı\n"
            "Telefonla çektiğiniz belge fotoğrafını yükleyin; "
            "eğiklik, gölge ve aydınlatma sorunları otomatik giderilir."
        )
        with gr.Row():
            with gr.Column():
                inp = gr.Image(label="Belge fotoğrafı", type="numpy")
                mode = gr.Radio(list(MODE_LABELS), value="Renkli",
                                label="Çıktı modu")
                ocr_box = gr.Checkbox(
                    label="OCR ile metni çıkar",
                    value=False,
                    interactive=ocr_available(),
                    info=None if ocr_available()
                    else "Tesseract kurulu değil — OCR devre dışı.")
                btn = gr.Button("Tara 🔍", variant="primary")
            with gr.Column():
                out_corners = gr.Image(label="Tespit edilen kenarlar")
                out_scan = gr.Image(label="Taranmış belge")
                out_pdf = gr.File(label="PDF indir")
                out_status = gr.Markdown()
                out_text = gr.Textbox(label="OCR metni", lines=6)

        btn.click(process, [inp, mode, ocr_box],
                  [out_corners, out_scan, out_pdf, out_status, out_text])
    return demo


if __name__ == "__main__":
    build_app().launch()
