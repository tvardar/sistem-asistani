# sayfalar/hakkinda.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QCursor
from gorsel_araclar import AyarlarYoneticisi 
import os

class HakkindaSayfasi(QWidget):
    def __init__(self, surum_gelen, icon_path, parent=None):
        super().__init__(parent)
        
        self.GUNCEL_SURUM = "v.1.0"
        self.icon_path = icon_path
        self.ayarlar_yoneticisi = AyarlarYoneticisi()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- ARAYÜZ ELEMANLARI OLUŞTURULUYOR ---
        # (Renk atamalarını burada yapmıyoruz, tema_guncelle fonksiyonunda yapacağız)

        # 1. Ana Kart
        self.card = QFrame()
        self.card.setFixedWidth(650)
        
        cl = QVBoxLayout(self.card)
        cl.setSpacing(8)
        cl.setContentsMargins(50, 40, 50, 40)
        
        # 2. Logo
        if os.path.exists(self.icon_path):
            img = QLabel()
            pix = QPixmap(self.icon_path).scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img.setPixmap(pix)
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img.setStyleSheet("background:transparent; margin-bottom:10px; border: none;")
            cl.addWidget(img)
            
        # 3. Başlık
        self.lbl_baslik = QLabel("SİSTEM ASİSTANI")
        self.lbl_baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_baslik.setStyleSheet("font-size: 26pt; font-weight: 900; letter-spacing: 2px; border: none; color: #33AADD;")
        cl.addWidget(self.lbl_baslik)
        
        # 4. Sürüm
        self.lbl_surum = QLabel()
        self.lbl_surum.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.lbl_surum)
        
        # 5. Açıklama
        self.desc = QLabel("Linux (Pardus/Debian) sistemler için geliştirilmiş;\nperformans izleme, bakım, donanım analizi ve yönetim aracı.")
        self.desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc.setWordWrap(True)
        cl.addWidget(self.desc)
        
        # 6. Uyarı Metni
        self.lbl_warning = QLabel("Bu program <b>kesinlikle hiçbir garanti vermez</b>.<br>Kullanımdan doğabilecek riskler kullanıcıya aittir.")
        self.lbl_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_warning.setStyleSheet("color: #e74c3c; font-size: 10pt; font-style: italic; margin: 10px 0; border: none;")
        cl.addWidget(self.lbl_warning)
        
        cl.addSpacing(10)
        
        # 7. Geliştirici Bilgisi
        self.lbl_dev = QLabel()
        self.lbl_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.lbl_dev)
        
        # 8. Linkler
        self.lbl_mail = QLabel()
        self.lbl_mail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mail.setOpenExternalLinks(True)
        self.lbl_mail.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cl.addWidget(self.lbl_mail)

        self.lbl_web = QLabel()
        self.lbl_web.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_web.setOpenExternalLinks(True)
        self.lbl_web.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cl.addWidget(self.lbl_web)

        self.lbl_github = QLabel()
        self.lbl_github.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_github.setOpenExternalLinks(True)
        self.lbl_github.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cl.addWidget(self.lbl_github)
        
        cl.addSpacing(20)

        # 9. Lisans Kutusu
        self.license_frame = QFrame()
        l_lic = QVBoxLayout(self.license_frame)
        l_lic.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_lic_title = QLabel("GNU Genel Kamu Lisansı v3.0 (GPLv3)")
        self.lbl_lic_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_lic_text = QLabel("Bu yazılım özgürdür; Özgür Yazılım Vakfı tarafından yayınlanan\nGNU Genel Kamu Lisansı koşulları altında değiştirebilir ve/veya dağıtabilirsiniz.")
        self.lbl_lic_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l_lic.addWidget(self.lbl_lic_title)
        l_lic.addWidget(self.lbl_lic_text)
        cl.addWidget(self.license_frame)

        # 10. Copyright
        self.lbl_copy = QLabel("© 2025 - Tüm Hakları Saklıdır")
        self.lbl_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.lbl_copy)

        layout.addWidget(self.card)
        
        # Başlangıçta temayı uygula
        self.tema_guncelle()

    def showEvent(self, event):
        """Bu sayfa her görüntülendiğinde temayı kontrol et ve güncelle."""
        self.tema_guncelle()
        super().showEvent(event)

    def tema_guncelle(self):
        """Temaya göre renkleri dinamik olarak ayarlar."""
        # Ayarları diskten tazeleyerek oku
        self.ayarlar_yoneticisi.ayarlar = self.ayarlar_yoneticisi.yukle()
        tema = self.ayarlar_yoneticisi.ayarlar.get("tema", "Otomatik")
        
        if tema == "Otomatik":
            tema = AyarlarYoneticisi.sistem_temasini_algila()

        if tema == "Açık":
            # AÇIK TEMA RENKLERİ
            c_text_main = "#000000"
            c_text_mid = "#333333"
            c_link = "#0066CC"
            c_border = "#BBBBBB"
            c_lic_bg = "rgba(0, 0, 0, 0.08)"
        else:
            # KOYU TEMA RENKLERİ (Parlak Beyaz)
            c_text_main = "#FFFFFF"
            c_text_mid = "#DDDDDD"
            c_link = "#33AADD"
            c_border = "#555555"
            c_lic_bg = "rgba(255, 255, 255, 0.1)"

        # STİLLERİ GÜNCELLE
        self.card.setStyleSheet(f"QFrame {{ border-radius: 20px; border: 1px solid {c_border}; background-color: transparent; }}")
        
        self.lbl_surum.setText(f"Sürüm {self.GUNCEL_SURUM} (Stable)")
        self.lbl_surum.setStyleSheet(f"font-size: 12pt; font-weight: bold; color: {c_text_mid}; border: none; margin-bottom: 10px;")
        
        self.desc.setStyleSheet(f"font-size: 12pt; margin: 5px 0; border: none; color: {c_text_main};")
        
        self.lbl_dev.setText(f"Geliştirici: <b style='color:{c_text_main}'>Tarık Vardar</b>")
        self.lbl_dev.setStyleSheet(f"font-size: 12pt; border: none; color: {c_text_mid}; margin-bottom: 5px;")
        
        link_style = f"""
            QLabel {{ font-size: 11pt; border: none; color: {c_text_mid}; margin-bottom: 2px; }} 
            a {{ color: {c_link}; text-decoration: none; font-weight: bold; }} 
            a:hover {{ color: #2980b9; text-decoration: underline; }}
        """
        self.lbl_mail.setText(f'<span style="font-size:12pt">📧</span> <a href="mailto:tarikvardar@gmail.com">tarikvardar@gmail.com</a>')
        self.lbl_mail.setStyleSheet(link_style)
        
        self.lbl_web.setText(f'<span style="font-size:12pt">🌐</span> <a href="https://www.tarikvardar.com.tr">www.tarikvardar.com.tr</a>')
        self.lbl_web.setStyleSheet(link_style)
        
        self.lbl_github.setText(f'<span style="font-size:12pt">💻</span> <a href="https://github.com/tvardar">github.com/tvardar</a>')
        self.lbl_github.setStyleSheet(link_style)

        self.license_frame.setStyleSheet(f"background-color: {c_lic_bg}; border-radius: 8px; border: none;")
        self.lbl_lic_title.setStyleSheet(f"font-weight: bold; font-size: 10pt; color: {c_text_main}; border: none; background: transparent;")
        self.lbl_lic_text.setStyleSheet(f"font-size: 9pt; color: {c_text_main}; border: none; background: transparent;")
        
        self.lbl_copy.setStyleSheet(f"color: {c_text_mid}; font-size: 9pt; margin-top: 5px; border: none;")