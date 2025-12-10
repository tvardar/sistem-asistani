# sayfalar/usb_yazdir.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QComboBox, QFileDialog, QMessageBox, QProgressBar)
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import os

class UsbYazdirSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.usb_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("USB ISO Yazdırıcı", icon))

        layout.addWidget(QLabel("1. ISO Dosyası Seçin:"))
        self.btn_iso = QPushButton("Dosya Seç...")
        self.btn_iso.clicked.connect(self.iso_sec)
        layout.addWidget(self.btn_iso)
        self.lbl_iso = QLabel("Seçilmedi")
        self.lbl_iso.setStyleSheet("color:#e67e22;")
        layout.addWidget(self.lbl_iso)

        layout.addSpacing(20)
        layout.addWidget(QLabel("2. Hedef USB Bellek Seçin (DİKKAT: Veriler Silinir!):"))
        self.combo_usb = QComboBox()
        layout.addWidget(self.combo_usb)
        self.btn_refresh = QPushButton("🔄 Listeyi Yenile")
        self.btn_refresh.clicked.connect(self.diskleri_getir)
        layout.addWidget(self.btn_refresh)

        layout.addSpacing(20)
        self.btn_yaz = QPushButton("🔥 YAZDIRMAYI BAŞLAT")
        self.btn_yaz.setStyleSheet("background-color:#c0392b; color:white; font-weight:bold; font-size:12pt; padding:10px;")
        self.btn_yaz.clicked.connect(self.yazdir)
        layout.addWidget(self.btn_yaz)

        self.diskleri_getir()
        layout.addStretch()

    def iso_sec(self):
        f, _ = QFileDialog.getOpenFileName(self, "ISO Seç", "", "Disk Kalıbı (*.iso)")
        if f:
            self.lbl_iso.setText(f)

    def diskleri_getir(self):
        self.combo_usb.clear()
        try:
            out = subprocess.check_output("lsblk -d -n -o NAME,MODEL,SIZE,TYPE,TRAN", shell=True, text=True)
            for line in out.splitlines():
                if "usb" in line.lower():
                    parts = line.split()
                    dev = f"/dev/{parts[0]}"
                    model = " ".join(parts[1:-3])
                    size = parts[-3]
                    self.combo_usb.addItem(f"{model} ({size}) - {dev}", dev)
        except: pass
        if self.combo_usb.count() == 0:
            self.combo_usb.addItem("USB Bellek Bulunamadı")

    def yazdir(self):
        iso = self.lbl_iso.text()
        if not os.path.exists(iso):
            QMessageBox.warning(self, "Hata", "ISO dosyası seçilmedi.")
            return
        
        usb_dev = self.combo_usb.currentData()
        if not usb_dev:
            QMessageBox.warning(self, "Hata", "USB bellek seçilmedi.")
            return

        reply = QMessageBox.question(self, "SON UYARI", 
                                     f"Hedef: {usb_dev}\n\nBu aygıttaki TÜM VERİLER SİLİNECEK.\nDevam etmek istiyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            cmd = f"pkexec dd if='{iso}' of={usb_dev} bs=4M status=progress oflag=sync"
            subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c \"{cmd}; echo; echo 'İşlem Bitti, Pencereyi Kapatabilirsiniz.'; read\""])