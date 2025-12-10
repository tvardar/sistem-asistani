# sayfalar/acilis_analizi.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                             QLabel, QPushButton, QProgressBar, QHBoxLayout, QMessageBox)
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtCore import Qt
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess

class AcilisAnaliziSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.boot_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Sistem Açılış Analizi", icon))
        
        info = QLabel("Sistem açılışını en çok yavaşlatan servisleri aşağıda görebilirsiniz.")
        info.setStyleSheet("color: palette(mid); margin-bottom: 5px;")
        layout.addWidget(info)
        
        # Üst Panel
        h_top = QHBoxLayout()
        self.lbl_toplam = QLabel("Analiz Bekleniyor...")
        self.lbl_toplam.setStyleSheet("font-size: 11pt; font-weight: bold; color: #33AADD;")
        h_top.addWidget(self.lbl_toplam)
        h_top.addStretch()
        
        self.btn_analiz = QPushButton("🚀 Analiz Et")
        self.btn_analiz.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px 15px;")
        self.btn_analiz.clicked.connect(self.analiz_et)
        h_top.addWidget(self.btn_analiz)
        layout.addLayout(h_top)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Süre (Grafik)", "Süre (Metin)", "Servis Adı"])
        
        # Sütun Ayarları
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(0, 150) # Grafik
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(1, 100) # Metin
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Servis
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.secim_kontrol)
        
        layout.addWidget(self.table)

        # Alt Buton
        self.btn_disable = QPushButton("⛔ Seçili Servisi Devre Dışı Bırak")
        self.btn_disable.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px;")
        self.btn_disable.clicked.connect(self.servisi_kapat)
        self.btn_disable.setEnabled(False)
        layout.addWidget(self.btn_disable)

    def secim_kontrol(self):
        self.btn_disable.setEnabled(len(self.table.selectedItems()) > 0)

    def analiz_et(self):
        self.table.setRowCount(0)
        self.lbl_toplam.setText("Analiz ediliyor...")
        self.btn_analiz.setEnabled(False)
        self.btn_disable.setEnabled(False)
        
        try:
            # 1. Toplam Süre
            total_time_out = subprocess.check_output(["systemd-analyze", "time"], text=True)
            t_str = total_time_out.split(' = ')[-1].strip()
            self.lbl_toplam.setText(f"Toplam Açılış Süresi: {t_str}")

            # 2. Servisler
            out = subprocess.check_output(["systemd-analyze", "blame"], text=True)
            lines = out.splitlines()[:40] # İlk 40 servis
            
            parsed_data = []
            max_ms = 0
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    time_str = parts[0]
                    service = " ".join(parts[1:])
                    
                    # Milisaniyeye çevir (Grafik için)
                    ms = 0
                    if "min" in time_str:
                        m = float(time_str.split("min")[0])
                        ms += m * 60000
                        time_str = time_str.split("min")[1]
                    
                    if "ms" in time_str: 
                        ms += float(time_str.replace("ms", ""))
                    elif "s" in time_str: 
                        ms += float(time_str.replace("s", "")) * 1000
                        
                    if ms > max_ms: max_ms = ms
                    parsed_data.append((ms, parts[0], service)) # parts[0] orijinal süre metni

            # Tabloya Ekle
            for ms, t_str, srv in parsed_data:
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # 1. Grafik Bar
                w_bar = QWidget()
                l_bar = QHBoxLayout(w_bar); l_bar.setContentsMargins(5, 5, 5, 5)
                pbar = QProgressBar()
                pbar.setRange(0, int(max_ms))
                pbar.setValue(int(ms))
                pbar.setTextVisible(False)
                
                # Renklendirme
                if ms > 5000: col = "#e74c3c" # 5sn üstü kırmızı
                elif ms > 1000: col = "#f1c40f" # 1sn üstü sarı
                else: col = "#2ecc71" # Yeşil
                
                pbar.setStyleSheet(f"QProgressBar {{ background: #444; border-radius: 2px; }} QProgressBar::chunk {{ background: {col}; border-radius: 2px; }}")
                l_bar.addWidget(pbar)
                self.table.setCellWidget(r, 0, w_bar)
                
                # 2. Metin Süre
                it_time = QTableWidgetItem(t_str)
                it_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, 1, it_time)
                
                # 3. Servis Adı
                self.table.setItem(r, 2, QTableWidgetItem(srv))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Analiz yapılamadı: {e}")
            self.lbl_toplam.setText("Analiz Hatası")
        
        self.btn_analiz.setEnabled(True)

    def servisi_kapat(self):
        row = self.table.currentRow()
        if row < 0: return
        
        service_name = self.table.item(row, 2).text()
        
        reply = QMessageBox.question(self, "Onay", 
                                     f"'{service_name}' servisini devre dışı bırakmak istiyor musunuz?\n\nBu işlem, servisin sistem açılışında otomatik başlamasını engeller.", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try: 
                subprocess.run(["pkexec", "systemctl", "disable", service_name], check=True)
                QMessageBox.information(self, "Başarılı", f"{service_name} devre dışı bırakıldı.")
                self.analiz_et() # Listeyi yenile
            except Exception as e: 
                QMessageBox.critical(self, "Hata", f"İşlem başarısız: {e}")