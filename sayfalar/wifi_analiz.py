# sayfalar/wifi_analiz.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QPushButton, QProgressBar, QCheckBox, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor # <--- EKLENDİ
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import re

class WifiScanner(QThread):
    # (SSID, Sinyal, Kanal, Güvenlik, Frekans, BSSID, Aktif_Mi)
    sonuc_sinyali = pyqtSignal(list) 
    hata_sinyali = pyqtSignal(str)

    def run(self):
        try:
            # -f IN-USE ekleyerek aktif ağı tespit ediyoruz (* işareti gelir)
            cmd = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,CHAN,SECURITY,FREQ,BSSID", "dev", "wifi"]
            
            # Arka planda taramayı tetikle (Sessizce)
            subprocess.run(["nmcli", "dev", "wifi", "rescan"], stderr=subprocess.DEVNULL)
            
            try:
                out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                out = ""
            
            networks = []
            
            for line in out.splitlines():
                if not line.strip(): continue
                
                # Kaçış karakterlerini düzelt
                parts = line.replace("\\:", "|COLON|").split(":")
                
                if len(parts) >= 7:
                    in_use = parts[0].strip() == "*"
                    ssid = parts[1].replace("|COLON|", ":").strip()
                    if not ssid: ssid = "<Gizli Ağ>"
                    
                    try: signal = int(parts[2])
                    except: signal = 0
                    
                    chan = parts[3]
                    sec = parts[4]
                    freq = parts[5]
                    bssid = parts[6].replace("|COLON|", ":")
                    
                    # Frekans Ayrımı
                    band = "2.4 GHz"
                    try:
                        f_val = int(freq.split()[0])
                        if f_val > 5000: band = "5 GHz"
                    except: pass

                    networks.append((ssid, signal, chan, sec, band, bssid, in_use))
            
            # Sıralama: Önce Aktif Ağ, Sonra Sinyal Gücü
            networks.sort(key=lambda x: (not x[6], -x[1]))
            
            self.sonuc_sinyali.emit(networks)

        except Exception as e:
            self.hata_sinyali.emit(str(e))

class WifiAnalizSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.network_ikonu("#e67e22", 32)
        layout.addWidget(SayfaBasligi("Gelişmiş Wi-Fi Analizörü", icon))

        # --- ÜST PANEL ---
        self.suggestion_box = QFrame()
        self.suggestion_box.setStyleSheet("""
            QFrame {
                background-color: rgba(51, 170, 221, 0.08); 
                border: 1px solid rgba(51, 170, 221, 0.3); 
                border-radius: 6px;
            }
        """)
        l_sugg = QVBoxLayout(self.suggestion_box)
        l_sugg.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_oneri = QLabel("Analiz Bekleniyor...")
        self.lbl_oneri.setStyleSheet("font-size: 10pt; color: #33AADD; border: none; background: transparent;")
        self.lbl_oneri.setWordWrap(True)
        self.lbl_oneri.setTextFormat(Qt.TextFormat.RichText)
        l_sugg.addWidget(self.lbl_oneri)
        layout.addWidget(self.suggestion_box)

        # --- KONTROLLER ---
        h_top = QHBoxLayout()
        self.chk_auto = QCheckBox("Otomatik Yenile (5sn)")
        self.chk_auto.stateChanged.connect(self.oto_yenileme_degisti)
        
        self.btn_tara = QPushButton("📡 Şimdi Tara")
        self.btn_tara.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 6px 15px;")
        self.btn_tara.clicked.connect(self.tara)
        
        h_top.addWidget(self.chk_auto)
        h_top.addStretch()
        h_top.addWidget(self.btn_tara)
        layout.addLayout(h_top)

        # --- TABLO ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Ağ Adı (SSID)", "Sinyal", "Kanal", "Bant", "Güvenlik", "MAC Adresi"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        # Sütun Genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(1, 120)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(2, 60)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(3, 80)
        
        layout.addWidget(self.table)

        # --- BİLGİ ---
        lbl_legend = QLabel("■ Yeşil: Mükemmel (>70%)  ■ Sarı: İyi (>40%)  ■ Kırmızı: Zayıf")
        lbl_legend.setStyleSheet("color: palette(mid); font-size: 9pt; margin-top: 5px;")
        lbl_legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_legend)

        self.timer = QTimer()
        self.timer.timeout.connect(self.tara)
        self.tara()

    def oto_yenileme_degisti(self, state):
        if state == 2:
            self.tara()
            self.timer.start(5000)
            self.btn_tara.setEnabled(False)
        else:
            self.timer.stop()
            self.btn_tara.setEnabled(True)

    def tara(self):
        if not self.chk_auto.isChecked():
            self.btn_tara.setEnabled(False)
            self.btn_tara.setText("Taranıyor...")
        
        self.worker = WifiScanner()
        self.worker.sonuc_sinyali.connect(self.sonuc_goster)
        self.worker.hata_sinyali.connect(self.hata_goster)
        self.worker.start()

    def kanal_analizi_yap(self, networks):
        kanallar = {1: 0, 2:0, 3:0, 4:0, 5:0, 6: 0, 7:0, 8:0, 9:0, 10:0, 11: 0, 12:0, 13:0}
        total_24 = 0
        
        for item in networks:
            if item[4] == "2.4 GHz":
                try:
                    ch = int(item[2])
                    if ch in kanallar: 
                        kanallar[ch] += 1
                        total_24 += 1
                except: pass
        
        if total_24 == 0:
            self.lbl_oneri.setText("Çevrede 2.4 GHz ağ bulunamadı veya Wi-Fi kapalı.")
            return

        ana_kanallar = {1: kanallar.get(1,0), 6: kanallar.get(6,0), 11: kanallar.get(11,0)}
        en_iyi_kanal = min(ana_kanallar, key=ana_kanallar.get)
        yogunluk = ana_kanallar[en_iyi_kanal]
        
        msg = f"<span style='color:#e67e22; font-weight:bold;'>ANALİZ SONUCU:</span> Çevrede {total_24} adet 2.4GHz ağ tespit edildi.<br>"
        
        if yogunluk == 0:
            msg += f"✅ <b>TAVSİYE:</b> Kanal <b style='font-size:12pt; color:#2ecc71;'>{en_iyi_kanal}</b> tamamen boş! Modeminizi bu kanala sabitleyiniz."
        else:
            msg += f"ℹ️ <b>TAVSİYE:</b> Kanal <b style='font-size:12pt; color:#f1c40f;'>{en_iyi_kanal}</b> en az yoğunluğa sahip. ({yogunluk} ağ var)"
            
        self.lbl_oneri.setText(msg)

    def sonuc_goster(self, networks):
        if not self.chk_auto.isChecked():
            self.btn_tara.setEnabled(True)
            self.btn_tara.setText("📡 Şimdi Tara")
        
        self.table.setRowCount(0)
        self.kanal_analizi_yap(networks)
        
        for ssid, signal, chan, sec, band, bssid, in_use in networks:
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            ssid_item = QTableWidgetItem(ssid)
            if in_use:
                ssid_item.setForeground(QColor("#2ecc71"))
                font = ssid_item.font()
                font.setBold(True)
                ssid_item.setFont(font)
                ssid_item.setText(f"{ssid} (Bağlı)")
            self.table.setItem(r, 0, ssid_item)
            
            w_bar = QWidget()
            l_bar = QHBoxLayout(w_bar)
            l_bar.setContentsMargins(5, 5, 5, 5)
            l_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            pbar = QProgressBar()
            pbar.setValue(signal)
            pbar.setTextVisible(True)
            pbar.setFormat(f"%{signal}")
            pbar.setFixedHeight(16)
            
            if signal > 70: col = "#2ecc71"
            elif signal > 40: col = "#f1c40f"
            else: col = "#e74c3c"
            
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #444;
                    border: 1px solid #666;
                    border-radius: 3px;
                    color: white;
                    text-align: center;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: {col};
                    border-radius: 3px;
                }}
            """)
            
            l_bar.addWidget(pbar)
            self.table.setCellWidget(r, 1, w_bar)
            
            c_item = QTableWidgetItem(chan); c_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.table.setItem(r, 2, c_item)
            b_item = QTableWidgetItem(band); b_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.table.setItem(r, 3, b_item)
            
            sec_short = sec.replace("WPA1", "").replace("WPA2", "WPA2").strip()
            self.table.setItem(r, 4, QTableWidgetItem(sec_short[:15]))
            self.table.setItem(r, 5, QTableWidgetItem(bssid))

        if not networks:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("Ağ bulunamadı."))

    def hata_goster(self, msg):
        if not self.chk_auto.isChecked():
            self.btn_tara.setEnabled(True)
            self.btn_tara.setText("📡 Şimdi Tara")
        self.lbl_oneri.setText(f"<b style='color:red'>Hata:</b> {msg}")