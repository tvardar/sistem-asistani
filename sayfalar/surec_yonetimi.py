# sayfalar/surec_yonetimi.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QHeaderView, QCheckBox, QPushButton, QMessageBox, QTableWidgetItem)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QTimer
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import psutil
import subprocess

class SurecYonetimiSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.process_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Görev Yöneticisi", icon))

        header = QHBoxLayout()
        self.lbl_count = QLabel("Toplam İşlem: 0")
        self.chk_auto = QCheckBox("Otomatik Yenile"); self.chk_auto.setChecked(True)
        header.addWidget(self.lbl_count); header.addStretch(); header.addWidget(self.chk_auto)
        layout.addLayout(header)

        self.tablo = QTableWidget(); self.tablo.setColumnCount(4)
        self.tablo.setHorizontalHeaderLabels(["PID", "Uygulama Adı", "CPU %", "RAM %"])
        self.tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tablo.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tablo.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # STİL SATIRI SİLİNDİ (Global stilden alacak)
        layout.addWidget(self.tablo)

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Şimdi Yenile"); btn_refresh.clicked.connect(self.verileri_cek)
        btn_kill = QPushButton("⛔ Seçili Süreci Sonlandır")
        btn_kill.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn_kill.clicked.connect(self.oldur)
        btn_layout.addWidget(btn_refresh); btn_layout.addStretch(); btn_layout.addWidget(btn_kill)
        layout.addLayout(btn_layout)

        self.timer = QTimer(self); self.timer.timeout.connect(self.otomatik_yenile); self.timer.start(3000)
        self.verileri_cek()

    def otomatik_yenile(self):
        if self.chk_auto.isChecked(): self.verileri_cek()
    def verileri_cek(self):
        # (Eski kodun aynısı)
        procs = []
        try:
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try: procs.append(p.info)
                except: pass
        except: pass
        procs.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        self.tablo.setRowCount(len(procs))
        self.lbl_count.setText(f"Toplam İşlem: {len(procs)}")
        for row, p in enumerate(procs):
            pid = str(p['pid']); name = p['name']; cpu = f"{p['cpu_percent']:.1f}"; ram = f"{p['memory_percent']:.1f}"
            self.tablo.setItem(row, 0, QTableWidgetItem(pid)); self.tablo.setItem(row, 1, QTableWidgetItem(name))
            self.tablo.setItem(row, 2, QTableWidgetItem(cpu)); self.tablo.setItem(row, 3, QTableWidgetItem(ram))
            if (p['cpu_percent'] or 0) > 50:
                for col in range(4): self.tablo.item(row, col).setForeground(QColor("#e74c3c"))
    def oldur(self):
        # (Eski kodun aynısı)
        current_row = self.tablo.currentRow()
        if current_row < 0: QMessageBox.warning(self, "Seçim Yok", "İşlem seçin."); return
        pid = self.tablo.item(current_row, 0).text()
        name = self.tablo.item(current_row, 1).text()
        if QMessageBox.question(self, "Onay", f"'{name}' (PID: {pid}) sonlandırılsın mı?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try: psutil.Process(int(pid)).terminate(); self.verileri_cek()
            except:
                try: subprocess.run(["pkexec", "kill", "-9", pid], check=True); self.verileri_cek()
                except: QMessageBox.critical(self, "Hata", "İşlem sonlandırılamadı.")