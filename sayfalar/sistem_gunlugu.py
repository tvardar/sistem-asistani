# sayfalar/sistem_gunlugu.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHeaderView, QComboBox, QHBoxLayout, QMessageBox, QLabel)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess

class SistemGunluguSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.log_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Sistem Günlükleri (Logs)", icon))

        h_ctrl = QHBoxLayout()
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["Tümü", "Hatalar (Error)", "Uyarılar (Warning)"])
        h_ctrl.addWidget(QLabel("Filtre:"))
        h_ctrl.addWidget(self.combo_filter)
        
        btn_refresh = QPushButton("🔄 Günlükleri Getir")
        btn_refresh.clicked.connect(self.loglari_getir)
        h_ctrl.addWidget(btn_refresh)
        h_ctrl.addStretch()
        layout.addLayout(h_ctrl)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Zaman", "Kaynak", "Mesaj"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Stil temizlendi, global stilden alacak
        layout.addWidget(self.table)

    def loglari_getir(self):
        self.table.setRowCount(0)
        filtre = self.combo_filter.currentText()
        
        # Journalctl komutu (Son 200 satır)
        cmd = ["pkexec", "journalctl", "-n", "200", "--no-pager"]
        
        if "Hatalar" in filtre: cmd.extend(["-p", "err"])
        elif "Uyarılar" in filtre: cmd.extend(["-p", "warning"])
        
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            lines = out.splitlines()
            
            self.table.setRowCount(len(lines))
            for i, line in enumerate(lines):
                parts = line.split(maxsplit=5)
                if len(parts) < 5: continue
                
                zaman = f"{parts[0]} {parts[1]} {parts[2]}"
                kaynak = parts[4].replace(":", "")
                mesaj = parts[5] if len(parts) > 5 else ""
                
                self.table.setItem(i, 0, QTableWidgetItem(zaman))
                self.table.setItem(i, 1, QTableWidgetItem(kaynak))
                self.table.setItem(i, 2, QTableWidgetItem(mesaj))
                
                # Sadece yazı rengini (foreground) değiştiriyoruz, arka plan temadan gelecek
                if "error" in line.lower() or "fail" in line.lower():
                    self.table.item(i, 2).setForeground(QColor("#e74c3c"))
                elif "warn" in line.lower():
                    self.table.item(i, 2).setForeground(QColor("#f1c40f"))

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Loglar okunamadı: {e}")