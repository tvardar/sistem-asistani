# logo_uret_v2.py (GÜNCELLENDİ - AÇIK TEMA DESTEKLİ)

import os
import sys
import math
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath, QRadialGradient, QTransform, QPixmap
from PyQt6.QtCore import Qt, QRectF, QPointF

def logo_ciz_profesyonel(boyut=512, dosya_adi="icons/sistem-asistani.png", tema="Koyu"):
    # QApplication örneği yoksa oluştur (PyQt çizim sınıfları için gerekli)
    if not QApplication.instance():
        app = QApplication(sys.argv)
    
    os.makedirs(os.path.dirname(dosya_adi), exist_ok=True)
    
    pixmap = QPixmap(boyut, boyut)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # --- RENK PALETİ ---
    accent_blue = QColor("#33AADD") # Pardus Mavisi (Her iki temada ortak)

    if tema == "Açık":
        # Açık Tema Renkleri
        bg_start = QColor("#F5F7FA")
        bg_end = QColor("#E0E0E0")
        check_color = QColor("#2C3E50") # Koyu Gri Tik İşareti
        gear_center_color = QColor("#F5F7FA") # Açık Renk Çark Merkezi
    else:
        # Koyu Tema Renkleri (Varsayılan)
        bg_start = QColor("#2D2D30")
        bg_end = QColor("#252526")
        check_color = QColor("#FFFFFF") # Beyaz Tik İşareti
        gear_center_color = QColor("#252526") # Koyu Renk Çark Merkezi
    
    center_pt = QPointF(boyut / 2, boyut / 2)
    center = boyut / 2

    # 1. ZEMİN (Yuvarlak Köşeli Kare)
    path_bg = QPainterPath()
    rect_bg = QRectF(boyut*0.05, boyut*0.05, boyut*0.9, boyut*0.9)
    path_bg.addRoundedRect(rect_bg, boyut*0.22, boyut*0.22)
    
    bg_grad = QLinearGradient(0, 0, boyut, boyut)
    bg_grad.setColorAt(0.0, bg_start)
    bg_grad.setColorAt(1.0, bg_end)
    
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(bg_grad))
    painter.drawPath(path_bg)

    # 2. DİŞLİ ÇARK (SİSTEM)
    gear_radius_outer = boyut * 0.38
    gear_radius_inner = boyut * 0.28
    num_teeth = 8
    
    path_gear = QPainterPath()
    path_gear.addEllipse(center_pt, gear_radius_inner, gear_radius_inner)
    
    for i in range(num_teeth):
        angle_deg = (i / num_teeth) * 360
        angle_rad = math.radians(angle_deg)
        tooth_center_x = center + math.cos(angle_rad) * gear_radius_inner
        tooth_center_y = center + math.sin(angle_rad) * gear_radius_inner
        tooth_w = boyut * 0.12; tooth_h = boyut * 0.18
        path_tooth = QPainterPath()
        rect_tooth = QRectF(-tooth_w/2, -tooth_h/2, tooth_w, tooth_h)
        path_tooth.addRoundedRect(rect_tooth, tooth_w*0.3, tooth_w*0.3)
        transform = QTransform(); transform.translate(tooth_center_x, tooth_center_y); transform.rotate(angle_deg + 90)
        path_gear.addPath(transform.map(path_tooth))

    # Çarkı Boya
    gear_grad = QRadialGradient(center_pt, gear_radius_outer)
    gear_grad.setColorAt(0.0, accent_blue.lighter(110))
    gear_grad.setColorAt(1.0, accent_blue)
    
    painter.setBrush(QBrush(gear_grad))
    painter.drawPath(path_gear.simplified())

    # Çarkın ortasını del (Temaya uygun renkle)
    painter.setBrush(gear_center_color)
    painter.drawEllipse(center_pt, gear_radius_inner * 0.6, gear_radius_inner * 0.6)

    # 3. ONAY İŞARETİ (ASİSTAN) - Temaya göre renk değişir
    path_check = QPainterPath()
    start_pt = QPointF(center - boyut * 0.14, center + boyut * 0.02)
    mid_pt = QPointF(center - boyut * 0.04, center + boyut * 0.14)
    end_pt = QPointF(center + boyut * 0.16, center - boyut * 0.12)
    
    path_check.moveTo(start_pt); path_check.lineTo(mid_pt); path_check.lineTo(end_pt)
    
    pen_check = QPen(check_color, boyut * 0.07)
    pen_check.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen_check.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen_check)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(path_check)
    
    painter.end()
    pixmap.save(dosya_adi, "PNG")
    print(f"✅ Logo oluşturuldu: {dosya_adi} (Tema: {tema})")

if __name__ == "__main__":
    # 1. Varsayılan Koyu Tema Logosu (Beyaz tik)
    logo_ciz_profesyonel(512, "icons/sistem-asistani.png", tema="Koyu")
    # Uygulama ikonu yedeği
    logo_ciz_profesyonel(256, "icons/yardimci-logo.png", tema="Koyu")

    # 2. YENİ: Açık Tema Logosu (Koyu tik)
    logo_ciz_profesyonel(512, "icons/sistem-asistani-dark.png", tema="Açık")
    
    print("\n🎉 Tüm logolar başarıyla oluşturuldu!")