# sayfalar/ozel_komutlar.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QLineEdit, QInputDialog, QMessageBox, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu, AyarlarYoneticisi
import subprocess
import json
import os

class OzelKomutlarSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ayarlar_yoneticisi = AyarlarYoneticisi() # Tema ayarları için
        
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.script_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Özel Komutlar", icon))

        self.json_file = os.path.expanduser("~/.config/sistem-asistani/scripts.json")
        self.komutlar = self.yukle()

        # Ekleme Butonu
        btn_ekle = QPushButton("➕ Yeni Komut Butonu Ekle")
        btn_ekle.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_ekle.clicked.connect(self.komut_ekle)
        layout.addWidget(btn_ekle)

        # Izgara Alanı
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("background:transparent; border:none;")
        self.content = QWidget(); self.grid = QGridLayout(self.content); self.grid.setSpacing(15)
        scroll.setWidget(self.content)
        layout.addWidget(scroll)

        # --- BİLGİLENDİRME ALANI ---
        self.info_frame = QFrame()
        self.l_info = QVBoxLayout(self.info_frame)
        
        lbl_baslik = QLabel("ℹ️ Nasıl Kullanılır?")
        lbl_baslik.setStyleSheet("color: #33AADD; font-weight: bold; font-size: 11pt;")
        self.l_info.addWidget(lbl_baslik)
        
        self.lbl_aciklama = QLabel(
            "Bu ekran, sık kullandığınız uzun terminal komutlarını tek tıkla çalışan butonlara dönüştürmenizi sağlar.\n"
            "Örnekler:\n"
            "• <b>Sistemi Güncelle:</b> <code>sudo apt update && sudo apt upgrade -y</code>\n"
            "• <b>Docker Temizle:</b> <code>docker system prune -a</code>\n"
            "• <b>Dosya Ara:</b> <code>find /home -name '*.mp4'</code>"
        )
        self.lbl_aciklama.setWordWrap(True)
        self.lbl_aciklama.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.l_info.addWidget(self.lbl_aciklama)
        
        layout.addWidget(self.info_frame)

        self.arayuz_tazele()

    def yukle(self):
        if os.path.exists(self.json_file):
            try: return json.load(open(self.json_file))
            except: return []
        return []

    def kaydet(self):
        os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
        json.dump(self.komutlar, open(self.json_file, "w"))

    def arayuz_tazele(self):
        # Önce mevcut butonları temizle
        for i in range(self.grid.count()): 
            self.grid.itemAt(i).widget().deleteLater()
        
        # Temayı algıla
        tema = self.ayarlar_yoneticisi.ayarlar.get("tema", "Otomatik")
        if tema == "Otomatik":
            tema = AyarlarYoneticisi.sistem_temasini_algila()

        # Tema bazlı renk tanımları
        if tema == "Açık":
            btn_style = """
                QPushButton { background-color: #f5f6fa; color: #2c3e50; border: 1px solid #dcdde1; border-radius: 8px; font-weight: bold; } 
                QPushButton:hover { border-color: #33AADD; background-color: #e5e6ea; }
            """
            info_bg = "#ffffff"
            info_border = "#dcdde1"
            info_text = "#7f8c8d"
        else: # Koyu Tema
            btn_style = """
                QPushButton { background-color: #2D2D30; color: #ecf0f1; border: 1px solid #444; border-radius: 8px; font-weight: bold; } 
                QPushButton:hover { border-color: #33AADD; }
            """
            info_bg = "#252526"
            info_border = "#444"
            info_text = "#cccccc"

        # Bilgi kutusunu güncelle
        self.info_frame.setStyleSheet(f"background-color: {info_bg}; border-radius: 8px; border: 1px solid {info_border}; margin-top: 10px;")
        self.lbl_aciklama.setStyleSheet(f"color: {info_text}; font-size: 10pt; margin-top: 5px;")

        # Butonları oluştur
        row, col = 0, 0
        for idx, item in enumerate(self.komutlar):
            # Ana buton
            btn = QPushButton(f"{item['ad']}\n(Komut: {item['cmd'][:20]}...)")
            btn.setMinimumHeight(80)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, x=item: self.calistir(x))
            
            # Kapsayıcı (Sil butonu ile birleştirmek için)
            frame = QFrame()
            l = QVBoxLayout(frame); l.setContentsMargins(0,0,0,0); l.setSpacing(2)
            l.addWidget(btn)
            
            # Sil butonu
            btn_sil = QPushButton("Sil")
            btn_sil.setStyleSheet("QPushButton { background-color: #c0392b; color: white; border-radius: 4px; height: 20px; font-size: 8pt; border: none; } QPushButton:hover { background-color: #e74c3c; }")
            btn_sil.clicked.connect(lambda _, i=idx: self.sil(i))
            l.addWidget(btn_sil)
            
            self.grid.addWidget(frame, row, col)
            col += 1
            if col > 2: col = 0; row += 1

    def komut_ekle(self):
        ad, ok1 = QInputDialog.getText(self, "Yeni Komut", "Buton Adı (Örn: Yedek Al):")
        if not ok1 or not ad: return
        cmd, ok2 = QInputDialog.getText(self, "Yeni Komut", "Terminal Komutu (Örn: tar -czf...):")
        if not ok2 or not cmd: return
        
        self.komutlar.append({"ad": ad, "cmd": cmd})
        self.kaydet()
        self.arayuz_tazele()

    def sil(self, idx):
        if QMessageBox.question(self, "Sil", "Bu butonu silmek istiyor musunuz?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.komutlar.pop(idx)
            self.kaydet()
            self.arayuz_tazele()

    def calistir(self, item):
        try:
            # Komutu yeni bir terminal penceresinde açıp, bitince bekletir.
            subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c \"{item['cmd']}; echo; echo '--------------------------------'; echo 'İşlem Tamamlandı (Pencereyi kapatabilirsiniz)'; read\""])
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Komut çalıştırılamadı: {e}")