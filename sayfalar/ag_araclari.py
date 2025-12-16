# sayfalar/ag_araclari.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QGroupBox, QLineEdit, QPushButton, QListWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QListWidgetItem, QMessageBox, QTabWidget, QApplication, QRadioButton, QButtonGroup,
                             QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFont
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import requests
import time
import threading
import shutil
import os
import urllib.request

# --- YENİ: DETAYLI PING WORKER ---
class PingWorker(QThread):
    satir_sinyali = pyqtSignal(str, str) # Mesaj, Renk Kodu
    bitti_sinyali = pyqtSignal()

    def __init__(self, hedef):
        super().__init__()
        self.hedef = hedef

    def run(self):
        try:
            # -c 4: 4 paket gönder
            # stdbuf -o0: Çıktıyı tamponlamadan anlık ver (Linux için)
            cmd = ["ping", "-c", "4", self.hedef]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Çıktıyı satır satır oku
            for line in process.stdout:
                line = line.strip()
                if not line: continue
                
                # Renklendirme mantığı
                renk = "#cccccc" # Varsayılan gri
                if "bytes from" in line: 
                    renk = "#2ecc71" # Yeşil (Başarılı yanıt)
                elif "unreachable" in line or "error" in line.lower():
                    renk = "#e74c3c" # Kırmızı (Hata)
                elif "statistics" in line:
                    renk = "#33AADD" # Mavi (Başlık)
                elif "packet loss" in line:
                    renk = "#f1c40f" # Sarı (İstatistik sonucu)

                self.satir_sinyali.emit(line, renk)
                
            process.wait()
            
            if process.returncode != 0:
                self.satir_sinyali.emit("Ping işlemi başarısız oldu veya ana makineye ulaşılamadı.", "#e74c3c")
                
        except Exception as e:
            self.satir_sinyali.emit(f"Hata oluştu: {str(e)}", "#e74c3c")
        
        self.bitti_sinyali.emit()

# --- NMAP WORKER (AYNI) ---
class NmapWorker(QThread):
    sonuc_sinyali = pyqtSignal(list)
    hata_sinyali = pyqtSignal(str)

    def run(self):
        try:
            nmap_bin = shutil.which("nmap")
            if not nmap_bin:
                if os.path.exists("/usr/bin/nmap"): nmap_bin = "/usr/bin/nmap"
                elif os.path.exists("/bin/nmap"): nmap_bin = "/bin/nmap"
                else:
                    self.hata_sinyali.emit("Nmap aracı sistemde bulunamadı.\nLütfen yükleyin: sudo apt install nmap")
                    return
            cmd = ["pkexec", nmap_bin, "-sn", "192.168.1.0/24"]
            output = subprocess.check_output(cmd, text=True)
            sonuclar = []
            for block in output.split("Nmap scan report for")[1:]:
                lines = block.split('\n'); ip = "Bilinmiyor"; host = "-"; vendor = "-"
                h = lines[0].strip()
                if "(" in h: host = h.split("(")[0].strip(); ip = h.split("(")[1].replace(")", "").strip()
                else: ip = h
                for l in lines:
                    if "MAC Address:" in l:
                        v = l.split("MAC Address:")[1].strip()
                        if "(" in v: vendor = v.split("(")[1].replace(")", "").strip()
                        else: vendor = v
                sonuclar.append((ip, host, vendor))
            self.sonuc_sinyali.emit(sonuclar)
        except subprocess.CalledProcessError as e:
            if e.returncode == 126 or e.returncode == 127: self.hata_sinyali.emit("Yetki verilmedi veya nmap çalıştırılamadı.")
            else: self.hata_sinyali.emit(f"Tarama hatası (Kod: {e.returncode})")
        except Exception as e: self.hata_sinyali.emit(str(e))

# --- NETWORK TASK (VERİ TAŞIYICI) ---
class NetworkTask(threading.Thread):
    def __init__(self, url, mode='dl', data=None):
        super().__init__()
        self.url = url
        self.mode = mode
        self.data = data
        self.running = True
        self.bytes_transferred = 0 
        self.daemon = True

    def run(self):
        session = requests.Session()
        while self.running:
            try:
                if self.mode == 'dl':
                    with session.get(self.url, stream=True, timeout=5) as r:
                        for chunk in r.iter_content(chunk_size=1048576):
                            if not self.running: break
                            if chunk:
                                self.bytes_transferred += len(chunk)
                else:
                    session.post(self.url, data=self.data, timeout=5)
                    self.bytes_transferred += len(self.data)
            except:
                time.sleep(0.1)
        session.close()

    def stop(self):
        self.running = False

# --- HIZ TESTİ YÖNETİCİSİ ---
class HizTestiWorker(QThread):
    sonuc_sinyali = pyqtSignal(str, str)
    anlik_sinyal = pyqtSignal(int, float)
    
    def __init__(self): 
        super().__init__()
        self.running = True
        self.thread_count = 4
        self.test_duration = 10 

    def run(self):
        try:
            # 1. PING
            self.sonuc_sinyali.emit("Durum", "Gecikme (Google) Ölçülüyor...")
            self.anlik_sinyal.emit(0, 0.0)
            try:
                out = subprocess.check_output(["ping", "-c", "3", "-W", "1", "8.8.8.8"], text=True)
                val = out.split("min/avg/max")[1].split("=")[1].split("/")[1].strip()
                self.sonuc_sinyali.emit("Gecikme", f"{val} ms")
            except: self.sonuc_sinyali.emit("Gecikme", "Hata")

            if not self.running: return

            # 2. İNDİRME TESTİ
            self.sonuc_sinyali.emit("Durum", "İndirme Kapasitesi Ölçülüyor...")
            url = "http://speed.cloudflare.com/__down?bytes=50000000"
            workers = []
            for _ in range(self.thread_count):
                task = NetworkTask(url, mode='dl')
                task.start()
                workers.append(task)

            start_time = time.time()
            last_bytes = 0
            last_check = start_time
            speed_samples = []

            while time.time() - start_time < self.test_duration and self.running:
                time.sleep(0.5)
                now = time.time()
                current_total_bytes = sum(w.bytes_transferred for w in workers)
                bytes_delta = current_total_bytes - last_bytes
                time_delta = now - last_check
                
                if time_delta > 0:
                    instant_speed = (bytes_delta * 8) / (time_delta * 1000000)
                    if (now - start_time) > 2: speed_samples.append(instant_speed)
                    progress = int(((now - start_time) / self.test_duration) * 100)
                    self.sonuc_sinyali.emit("İndirme", f"{instant_speed:.1f} Mbps")
                    self.anlik_sinyal.emit(progress, instant_speed)
                    last_bytes = current_total_bytes
                    last_check = now

            for w in workers: w.stop(); w.join(timeout=1)

            final_dl_speed = 0.0
            if speed_samples:
                speed_samples.sort()
                top_samples = speed_samples[int(len(speed_samples)*0.5):]
                if top_samples: final_dl_speed = sum(top_samples) / len(top_samples)
                else: final_dl_speed = max(speed_samples)

            self.sonuc_sinyali.emit("İndirme", f"{final_dl_speed:.2f} Mbps")
            self.anlik_sinyal.emit(100, final_dl_speed)

            if not self.running: return
            time.sleep(1)

            # 3. YÜKLEME TESTİ
            self.sonuc_sinyali.emit("Durum", "Yükleme Kapasitesi Ölçülüyor...")
            workers = []; data = b'0' * 524288
            for _ in range(self.thread_count):
                task = NetworkTask("http://speed.cloudflare.com/__up", mode='ul', data=data)
                task.start()
                workers.append(task)

            start_time = time.time()
            last_bytes = 0
            last_check = start_time
            speed_samples = []

            while time.time() - start_time < self.test_duration and self.running:
                time.sleep(0.5)
                now = time.time()
                current_total_bytes = sum(w.bytes_transferred for w in workers)
                bytes_delta = current_total_bytes - last_bytes
                time_delta = now - last_check
                
                if time_delta > 0:
                    instant_speed = (bytes_delta * 8) / (time_delta * 1000000)
                    if (now - start_time) > 2: speed_samples.append(instant_speed)
                    progress = int(((now - start_time) / self.test_duration) * 100)
                    self.sonuc_sinyali.emit("Yükleme", f"{instant_speed:.1f} Mbps")
                    self.anlik_sinyal.emit(progress, instant_speed)
                    last_bytes = current_total_bytes
                    last_check = now

            for w in workers: w.stop(); w.join(timeout=1)

            final_ul_speed = 0.0
            if speed_samples:
                speed_samples.sort()
                top_samples = speed_samples[int(len(speed_samples)*0.5):]
                if top_samples: final_ul_speed = sum(top_samples) / len(top_samples)
                else: final_ul_speed = max(speed_samples)

            self.sonuc_sinyali.emit("Yükleme", f"{final_ul_speed:.2f} Mbps")
            self.anlik_sinyal.emit(100, final_ul_speed)
            self.sonuc_sinyali.emit("Durum", "Test Tamamlandı")
            self.sonuc_sinyali.emit("Bitti", "Bitti")

        except Exception as e: self.sonuc_sinyali.emit("Hata", str(e))
    
    def stop(self): self.running = False

# --- DNS WORKER (AYNI) ---
class DNSWorker(QThread):
    durum_sinyali = pyqtSignal(str, str)
    def __init__(self, dns_ips, dns_name):
        super().__init__(); self.dns_ips = dns_ips; self.dns_name = dns_name
    def run(self):
        self.durum_sinyali.emit("Aktif bağlantı tespit ediliyor...", "orange"); time.sleep(0.5)
        try:
            con_name = subprocess.check_output("nmcli -t -f NAME connection show --active", shell=True, text=True).strip().split('\n')[0]
            if not con_name: self.durum_sinyali.emit("Hata: Aktif ağ bağlantısı bulunamadı.", "red"); return
            self.durum_sinyali.emit(f"'{con_name}' yapılandırılıyor...", "orange")
            cmds = []
            if self.dns_ips == "auto":
                cmds.append(f"nmcli con mod \"{con_name}\" ipv4.ignore-auto-dns no"); cmds.append(f"nmcli con mod \"{con_name}\" ipv4.dns \"\"")
            else:
                cmds.append(f"nmcli con mod \"{con_name}\" ipv4.ignore-auto-dns yes"); cmds.append(f"nmcli con mod \"{con_name}\" ipv4.dns \"{self.dns_ips}\"")
            cmds.append(f"nmcli con up \"{con_name}\"")
            subprocess.run(["pkexec", "sh", "-c", " && ".join(cmds)], check=True)
            self.durum_sinyali.emit(f"Başarılı: {self.dns_name} ayarlandı.", "#2ecc71")
        except: self.durum_sinyali.emit("Hata: Yetki verilmedi veya işlem başarısız.", "red")

class AgAraclariSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.network_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Ağ & Hız Testi", icon))
        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        
        # TAB 1: Tanılama (DETAYLI PING)
        tab1 = QWidget(); l1 = QVBoxLayout(tab1)
        grp_ping = QGroupBox("Ping Testi (4 Paket)"); l_ping = QVBoxLayout(grp_ping)
        h_ping = QHBoxLayout(); self.txt_hedef = QLineEdit("google.com"); self.btn_ping = QPushButton("Ping Başlat"); self.btn_ping.clicked.connect(self.ping_at)
        h_ping.addWidget(self.txt_hedef); h_ping.addWidget(self.btn_ping); l_ping.addLayout(h_ping)
        
        # Ping listesini büyüttük ve terminal görünümü verdik
        self.ping_list = QListWidget()
        self.ping_list.setMinimumHeight(150) # Biraz daha yüksek
        self.ping_list.setStyleSheet("font-family: 'Consolas', 'Monospace'; font-size: 10pt; background-color: #252526; color: #f0f0f0;")
        l_ping.addWidget(self.ping_list); l1.addWidget(grp_ping)
        
        grp_scan = QGroupBox("Ağ Tarama"); l_scan = QVBoxLayout(grp_scan)
        h_scan = QHBoxLayout(); btn_scan = QPushButton("🔍 Ağı Tara (Root)"); btn_scan.clicked.connect(self.agi_tara)
        self.lbl_durum = QLabel("Hazır"); self.lbl_durum.setStyleSheet("color: palette(mid);") 
        h_scan.addWidget(btn_scan); h_scan.addWidget(self.lbl_durum); h_scan.addStretch(); l_scan.addLayout(h_scan)
        self.table = QTableWidget(); self.table.setColumnCount(3); self.table.setHorizontalHeaderLabels(["IP", "Cihaz", "Marka"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);
        l_scan.addWidget(self.table); l1.addWidget(grp_scan); self.tabs.addTab(tab1, QIcon(SvgIkonOlusturucu.info_ikonu("#33AADD")), "Tanılama")
        
        # TAB 2: DNS
        tab_dns = QWidget(); l_dns = QVBoxLayout(tab_dns)
        grp_dns = QGroupBox("DNS Sunucusu Değiştir"); l_dns_in = QVBoxLayout(grp_dns)
        self.bg_dns = QButtonGroup()
        self.dns_options = [("Google DNS", "8.8.8.8 8.8.4.4"), ("Cloudflare DNS", "1.1.1.1 1.0.0.1"), ("OpenDNS", "208.67.222.222 208.67.220.220"), ("Sistem Varsayılanı (Otomatik)", "auto")]
        for name, val in self.dns_options:
            t = name + (f" ({val.split()[0]})" if "auto" not in val else "")
            rb = QRadioButton(t); self.bg_dns.addButton(rb); l_dns_in.addWidget(rb)
            if "auto" in val: rb.setChecked(True)
        btn_apply_dns = QPushButton("DNS Ayarlarını Uygula (Root)"); btn_apply_dns.setStyleSheet("background-color:#e67e22; color:white; font-weight:bold; padding:8px;")
        btn_apply_dns.clicked.connect(self.dns_uygula); l_dns_in.addWidget(btn_apply_dns)
        self.lbl_dns_durum = QLabel("Durum: Bekleniyor"); self.lbl_dns_durum.setAlignment(Qt.AlignmentFlag.AlignCenter); l_dns_in.addWidget(self.lbl_dns_durum)
        l_dns.addWidget(grp_dns); l_dns.addStretch(); self.tabs.addTab(tab_dns, QIcon(SvgIkonOlusturucu.network_ikonu("#e67e22")), "DNS Ayarları")

        # TAB 3: Hız Testi
        tab2 = QWidget(); l2 = QVBoxLayout(tab2); l2.setSpacing(20); l2.setContentsMargins(50, 50, 50, 50)
        l2.addWidget(QLabel("<h2 style='color:#33AADD; text-align:center'>İnternet Hız Testi</h2>"))
        self.lbl_test_durum = QLabel("Başlamaya Hazır"); self.lbl_test_durum.setAlignment(Qt.AlignmentFlag.AlignCenter); l2.addWidget(self.lbl_test_durum)
        self.pbar_hiz = QProgressBar(); self.pbar_hiz.setTextVisible(False); self.pbar_hiz.setFixedHeight(10); self.pbar_hiz.setStyleSheet("QProgressBar { border-radius: 5px; background: #e0e0e0; } QProgressBar::chunk { background-color: #33AADD; border-radius: 5px; }")
        l2.addWidget(self.pbar_hiz)
        grid_speed = QHBoxLayout()
        def create_speed_box(title):
            box = QGroupBox(title); lb = QVBoxLayout(box); lbl = QLabel("-"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lbl.setStyleSheet("font-size: 24pt; font-weight: bold;"); lb.addWidget(lbl); return box, lbl
        box_ping, self.lbl_ping = create_speed_box("Gecikme (Ping)"); box_dl, self.lbl_dl = create_speed_box("İndirme (Mbps)"); box_ul, self.lbl_ul = create_speed_box("Yükleme (Mbps)")
        grid_speed.addWidget(box_ping); grid_speed.addWidget(box_dl); grid_speed.addWidget(box_ul); l2.addLayout(grid_speed)
        self.btn_speed = QPushButton("🚀 TESTİ BAŞLAT"); self.btn_speed.setFixedSize(220, 60); self.btn_speed.setStyleSheet("background-color: #e67e22; color: white; font-size: 14pt; border-radius: 30px; font-weight:bold;")
        self.btn_speed.clicked.connect(self.hiz_testi_baslat); l2.addStretch(); l2.addWidget(self.btn_speed, alignment=Qt.AlignmentFlag.AlignCenter); l2.addStretch()
        self.tabs.addTab(tab2, QIcon(SvgIkonOlusturucu.dashboard_ikonu("#e67e22")), "Hız Testi")

    def ping_at(self):
        hedef = self.txt_hedef.text().strip()
        if not hedef: return
        self.ping_list.clear()
        self.btn_ping.setEnabled(False); self.btn_ping.setText("Ping Atılıyor...")
        self.ping_list.addItem(QListWidgetItem(f"⏳ {hedef} adresine 4 paket gönderiliyor..."))
        
        self.ping_worker = PingWorker(hedef)
        self.ping_worker.satir_sinyali.connect(self.ping_satir_ekle)
        self.ping_worker.bitti_sinyali.connect(self.ping_bitti)
        self.ping_worker.start()

    def ping_satir_ekle(self, mesaj, renk):
        item = QListWidgetItem(mesaj)
        item.setForeground(QColor(renk))
        self.ping_list.addItem(item)
        self.ping_list.scrollToBottom()

    def ping_bitti(self):
        self.btn_ping.setEnabled(True); self.btn_ping.setText("Ping Başlat")
        self.ping_list.addItem(QListWidgetItem("--- İşlem Tamamlandı ---"))
        self.ping_list.scrollToBottom()
    
    def agi_tara(self):
        self.lbl_durum.setText("Taranıyor... (Root Şifresi Girin)"); self.table.setRowCount(0)
        self.worker_scan = NmapWorker(); self.worker_scan.sonuc_sinyali.connect(self.tarama_bitti); self.worker_scan.hata_sinyali.connect(self.tarama_hata); self.worker_scan.start()

    def tarama_bitti(self, sonuclar):
        self.lbl_durum.setText(f"Tamamlandı: {len(sonuclar)} cihaz")
        for ip, host, vendor in sonuclar:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(ip)); self.table.setItem(r, 1, QTableWidgetItem(host)); self.table.setItem(r, 2, QTableWidgetItem(vendor))

    def tarama_hata(self, m): self.lbl_durum.setText("Hata"); QMessageBox.warning(self, "Hata", m)

    def hiz_testi_baslat(self):
        self.btn_speed.setText("Ölçülüyor..."); self.btn_speed.setEnabled(False); self.pbar_hiz.setValue(0)
        self.worker = HizTestiWorker(); self.worker.sonuc_sinyali.connect(self.hiz_sonuc); self.worker.anlik_sinyal.connect(self.hiz_anlik_guncelle); self.worker.start()
    
    def hiz_anlik_guncelle(self, progress, speed): self.pbar_hiz.setValue(progress)
    
    def hiz_sonuc(self, tur, deger):
        if tur == "Bitti": self.btn_speed.setText("Testi Tekrarla"); self.btn_speed.setEnabled(True); self.pbar_hiz.setValue(100)
        elif tur == "Hata": QMessageBox.critical(self, "Hata", deger); self.btn_speed.setEnabled(True)
        elif tur == "Gecikme": self.lbl_ping.setText(deger)
        elif tur == "İndirme": self.lbl_dl.setText(deger)
        elif tur == "Yükleme": self.lbl_ul.setText(deger)
        elif tur == "Durum": self.lbl_test_durum.setText(deger)
    
    def dns_uygula(self):
        sel = self.bg_dns.checkedButton(); 
        if not sel: return
        val = ""; dns_name = "Özel DNS"; selected_text = sel.text()
        for name, v in self.dns_options:
            if name in selected_text: val = v; dns_name = name; break
        self.lbl_dns_durum.setText("⏳ Uygulanıyor..."); QApplication.processEvents()
        self.dns_worker = DNSWorker(val, dns_name); self.dns_worker.durum_sinyali.connect(self.dns_sonuc); self.dns_worker.start()

    def dns_sonuc(self, m, c): self.lbl_dns_durum.setText(m); self.lbl_dns_durum.setStyleSheet(f"color: {c}; font-weight: bold;")