# sayfalar/donanim.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QGroupBox, QProgressBar, QPushButton, QScrollArea,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import os
import subprocess
import shutil
import time
import socket
import getpass
import platform
import re
from datetime import datetime

class DonanimSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        icon = SvgIkonOlusturucu.hardware_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Donanım & Güç", icon))

        # --- ÜST BUTONLAR (GÜNCELLENDİ) ---
        # Butonların görünür olması için layout.addWidget ile doğrudan ekledik
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 10) # Alt boşluk
        
        self.btn_yenile = QPushButton("🔄 Yenile")
        self.btn_yenile.setMinimumHeight(40)
        self.btn_yenile.setStyleSheet("background-color: #33AADD; color: white; font-weight: bold; font-size: 10pt; padding: 5px 15px;")
        self.btn_yenile.clicked.connect(self.manuel_yenile)
        
        self.btn_rapor = QPushButton("📄 Sistem Raporu TXT Kaydet")
        self.btn_rapor.setMinimumHeight(40)
        self.btn_rapor.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; font-size: 10pt; padding: 5px 15px;")
        self.btn_rapor.clicked.connect(self.txt_kaydet)
        
        btn_layout.addStretch() # Sola yasla
        btn_layout.addWidget(self.btn_yenile)
        btn_layout.addWidget(self.btn_rapor)
        layout.addLayout(btn_layout)

        # SCROLL ALANI
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.icerik_widget = QWidget()
        self.icerik_layout = QVBoxLayout(self.icerik_widget)
        self.icerik_layout.setSpacing(20)

        # 1. GÜÇ
        self.grp_guc = QGroupBox("Güç & Batarya")
        l_guc = QVBoxLayout(self.grp_guc)
        self.lbl_durum = QLabel("Durum: Yükleniyor...")
        self.lbl_kalan = QLabel("Kalan: -")
        self.lbl_sure = QLabel("Tahmini Süre: -")
        l_guc.addWidget(self.lbl_durum); l_guc.addWidget(self.lbl_kalan); l_guc.addWidget(self.lbl_sure)
        self.icerik_layout.addWidget(self.grp_guc)

        # 2. SİSTEM
        self.grp_sis = QGroupBox("Sistem & Çekirdek")
        l_sis = QVBoxLayout(self.grp_sis)
        self.lbl_model = QLabel("Model: -") 
        self.lbl_gpu = QLabel("GPU: -")
        self.lbl_cpu = QLabel("CPU: -")
        self.lbl_ram = QLabel("RAM: -")
        self.lbl_distro = QLabel("Dağıtım: -")
        self.lbl_kernel = QLabel("Kernel: -")
        l_sis.addWidget(self.lbl_model); l_sis.addWidget(self.lbl_gpu); l_sis.addWidget(self.lbl_cpu); l_sis.addWidget(self.lbl_ram); l_sis.addWidget(self.lbl_distro); l_sis.addWidget(self.lbl_kernel)
        self.icerik_layout.addWidget(self.grp_sis)

        # 3. ÇEVRE BİRİMLERİ (DETAYLI)
        self.grp_detay = QGroupBox("Bağlı Donanımlar & Çevre Birimleri")
        self.layout_detay = QVBoxLayout(self.grp_detay)
        self.icerik_layout.addWidget(self.grp_detay)

        # 4. FİZİKSEL DİSKLER
        self.grp_fiziksel = QGroupBox("Fiziksel Diskler (Donanım)")
        self.layout_fiziksel = QVBoxLayout(self.grp_fiziksel)
        self.icerik_layout.addWidget(self.grp_fiziksel)

        # 5. MANTIKSAL BÖLÜMLER
        self.grp_disk = QGroupBox("Mantıksal Bölümler (Mounts)")
        self.layout_disk = QVBoxLayout(self.grp_disk)
        self.layout_disk.setSpacing(10)
        self.icerik_layout.addWidget(self.grp_disk)
        
        self.icerik_layout.addStretch()
        scroll.setWidget(self.icerik_widget)
        layout.addWidget(scroll)
        
        self.son_veri = {}
        self.tespit_edilen_donanimlar = {}
        self.fiziksel_diskler_listesi = []
        self.mantiksal_bolumler_listesi = []
        self.pc_modeli = "Bilinmiyor"
        
        # Başlangıçta tarama yap
        QTimer.singleShot(1000, self.donanim_tara)

    def manuel_yenile(self):
        self.donanim_tara()

    def donanim_tara(self):
        # Model Bilgisi
        try:
            with open("/sys/devices/virtual/dmi/id/product_name", "r") as f: self.pc_modeli = f.read().strip()
        except: self.pc_modeli = "Bilinmiyor"
        self.lbl_model.setText(f"<b>Model:</b> {self.pc_modeli}")

        # Detay Alanını Temizle
        while self.layout_detay.count():
            item = self.layout_detay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        self.tespit_edilen_donanimlar = { "Wi-Fi Kartı 📶": "Yok", "Ethernet (LAN) 🌐": "Yok", "Ses Kartı 🔊": "Yok", "Bluetooth 🦷": "Yok", "Yazıcı 🖨️": "Yok" }

        # Ağ Arayüzlerini Bul
        wifi_ifaces = []; eth_ifaces = []
        try:
            for iface in os.listdir('/sys/class/net'):
                if iface == 'lo': continue
                if os.path.exists(f"/sys/class/net/{iface}/wireless") or iface.startswith('wl'): wifi_ifaces.append(iface)
                elif iface.startswith('en') or iface.startswith('eth'): eth_ifaces.append(iface)
        except: pass

        # Donanım Taraması (lspci)
        try:
            out = subprocess.check_output("lspci -mm", shell=True, text=True)
            for line in out.splitlines():
                parts = line.split('"')
                if len(parts) >= 6:
                    class_name, vendor, device = parts[1], parts[3], parts[5]
                    full = f"{vendor} - {device}"
                    
                    if "Network" in class_name:
                        if wifi_ifaces: full += f" (Arayüz: {', '.join(wifi_ifaces)})"
                        self.tespit_edilen_donanimlar["Wi-Fi Kartı 📶"] = full
                    elif "Ethernet" in class_name:
                        if eth_ifaces: full += f" (Arayüz: {', '.join(eth_ifaces)})"
                        self.tespit_edilen_donanimlar["Ethernet (LAN) 🌐"] = full
                    elif "Audio" in class_name: 
                        if self.tespit_edilen_donanimlar["Ses Kartı 🔊"] == "Yok": self.tespit_edilen_donanimlar["Ses Kartı 🔊"] = full
                        else: self.tespit_edilen_donanimlar["Ses Kartı 🔊"] += f"\n{full}"
        except: pass
        
        # Bluetooth Kontrolü
        if shutil.which("hciconfig"):
            try:
                out = subprocess.check_output("hciconfig -a", shell=True, text=True)
                if "UP RUNNING" in out: self.tespit_edilen_donanimlar["Bluetooth 🦷"] = "Aktif"
                elif "DOWN" in out: self.tespit_edilen_donanimlar["Bluetooth 🦷"] = "Kapalı (Donanım Var)"
            except: pass
        else:
             try:
                 lsusb_out = subprocess.check_output("lsusb", shell=True, text=True)
                 if "Bluetooth" in lsusb_out: self.tespit_edilen_donanimlar["Bluetooth 🦷"] = "USB Adaptör"
             except: pass

        # Yazıcı Kontrolü
        if shutil.which("lpstat"):
            try:
                out = subprocess.check_output(["lpstat", "-p"], text=True, stderr=subprocess.DEVNULL)
                if out.strip():
                     printers = [l.split()[1] for l in out.splitlines() if "printer" in l]
                     self.tespit_edilen_donanimlar["Yazıcı 🖨️"] = ", ".join(printers)
                else: self.tespit_edilen_donanimlar["Yazıcı 🖨️"] = "Sistemde kurulu yazıcı yok"
            except: pass
        else: self.tespit_edilen_donanimlar["Yazıcı 🖨️"] = "CUPS Servisi Yok"

        # Arayüze Ekle
        for k, v in self.tespit_edilen_donanimlar.items(): self.donanim_bilgisi_satiri(k, v)

        # Fiziksel Diskleri Temizle ve Yenile
        while self.layout_fiziksel.count():
            item = self.layout_fiziksel.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        self.fiziksel_diskler_listesi = []
        try:
            out = subprocess.check_output("lsblk -d -n -o NAME,MODEL,SIZE,TYPE,TRAN -e 7,11", shell=True, text=True)
            for line in out.splitlines():
                cols = line.split()
                if len(cols) >= 3:
                    name = cols[0]
                    size = cols[-3] if len(cols) >= 3 else "?"
                    # Model bazen boşluklu olabilir
                    if len(cols) > 4:
                         model = " ".join(cols[1:-3])
                         tran = cols[-1].upper()
                    else:
                         model = cols[1]
                         tran = "?"

                    self.fiziksel_diskler_listesi.append(f"{name}: {model} ({size}) [{tran}]")
                    
                    w = QWidget(); hl = QHBoxLayout(w); hl.setContentsMargins(0,0,0,0)
                    icon = QLabel("💽"); icon.setFixedWidth(30)
                    
                    lbl_info = QLabel(f"{model}")
                    lbl_info.setStyleSheet("font-weight:bold;") # Renk yok, temadan alacak
                    
                    lbl_det = QLabel(f"{size} • {tran}")
                    lbl_det.setStyleSheet("color: #33AADD;")
                    
                    hl.addWidget(icon); hl.addWidget(lbl_info); hl.addStretch(); hl.addWidget(lbl_det)
                    self.layout_fiziksel.addWidget(w)
        except Exception as e: pass

        self.diskleri_yenile_df()

    def diskleri_yenile_df(self):
        while self.layout_disk.count():
            item = self.layout_disk.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        self.mantiksal_bolumler_listesi = []
        try:
            cmd = ["df", "-hT", "--exclude-type=tmpfs", "--exclude-type=devtmpfs", "--exclude-type=squashfs"]
            out = subprocess.check_output(cmd, text=True)
            lines = out.splitlines()[1:]
            for line in lines:
                cols = line.split()
                if len(cols) >= 7:
                    fs_dev = cols[0]; fstype = cols[1]; size = cols[2]; used = cols[3]; avail = cols[4]; use_pct = cols[5]; mount = cols[6]
                    rapor_satiri = f"{fs_dev} ({fstype.upper()}) - {mount} - {used}/{size}"
                    self.mantiksal_bolumler_listesi.append(rapor_satiri)
                    row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 2, 0, 2)
                    
                    etiket = f"📂 {mount} <span style='color:#7f8c8d'>({fs_dev})</span> <span style='color:#e67e22'>[{fstype.upper()}]</span>"
                    
                    lbl = QLabel(etiket); lbl.setFixedWidth(320)
                    lbl.setStyleSheet("font-weight:bold; font-size:9pt;")
                    lbl.setTextFormat(Qt.TextFormat.RichText)
                    
                    try: pct_val = int(use_pct.replace('%', ''))
                    except: pct_val = 0
                    bar = QProgressBar(); bar.setValue(pct_val); bar.setFormat(f"%p% | Dolu: {used} / Top: {size}"); bar.setTextVisible(True); bar.setAlignment(Qt.AlignmentFlag.AlignCenter); bar.setFixedHeight(18)
                    h.addWidget(lbl); h.addWidget(bar); self.layout_disk.addWidget(row)
        except Exception as e: lbl = QLabel(f"Disk bilgisi alınamadı: {e}"); self.layout_disk.addWidget(lbl)

    def donanim_bilgisi_satiri(self, baslik, deger):
        w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(0, 0, 0, 0)
        lbl_b = QLabel(f"<b>{baslik}:</b>"); lbl_b.setFixedWidth(140); lbl_b.setStyleSheet("color: #7f8c8d;")
        lbl_v = QLabel(deger); lbl_v.setWordWrap(True)
        if "Yok" in deger or "yüklü değil" in deger: lbl_v.setStyleSheet("color: #95a5a6; font-style: italic;")
        else: lbl_v.setStyleSheet("font-size: 10pt;") # Renk belirtmedik
        l.addWidget(lbl_b); l.addWidget(lbl_v); self.layout_detay.addWidget(w)

    def format_sure_str(self, raw_str):
        try:
            if not raw_str: return "Bilinmiyor"
            s = raw_str.replace("Startup finished in", "Toplam:")
            s = s.replace("kernel", "Çekirdek")
            s = s.replace("userspace", "Kullanıcı A.")
            s = s.replace("firmware", "Donanım")
            s = s.replace("loader", "Önyükleyici")
            s = re.sub(r'(\d+\.?\d*)s', r'\1 sn', s)
            s = s.replace("min", " dk")
            return s
        except: return raw_str

    def txt_kaydet(self):
        if not self.son_veri: QMessageBox.warning(self, "Uyarı", "Veriler henüz yüklenmedi, lütfen bekleyin."); return
        
        tarih_dosya_adi = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        varsayilan_isim = f"sistem_asistan_{tarih_dosya_adi}.txt"
        
        path, _ = QFileDialog.getSaveFileName(self, "Sistem Raporu TXT Kaydet", varsayilan_isim, "Text Files (*.txt)")
        if path:
            try:
                hostname = socket.gethostname(); yerel_ip = socket.gethostbyname(hostname); kullanici = getpass.getuser()
                startups = []
                p_auto = os.path.expanduser("~/.config/autostart")
                if os.path.exists(p_auto):
                    for f in os.listdir(p_auto):
                        if f.endswith(".desktop"): startups.append(f)
                services = []
                try:
                    s_out = subprocess.check_output("systemctl list-units --type=service --state=running --no-pager --no-legend", shell=True, text=True)
                    for l in s_out.splitlines(): services.append(l.split()[0])
                except: pass
                
                boot_raw = "Bilinmiyor"
                try: boot_raw = subprocess.check_output(["systemd-analyze", "time"], text=True).strip()
                except: pass
                boot_fmt = self.format_sure_str(boot_raw)

                dns_str = "Bilinmiyor"
                try:
                    dnsler = []
                    with open("/etc/resolv.conf", "r") as f:
                        for line in f:
                            if line.startswith("nameserver"): dnsler.append(line.split()[1])
                    if dnsler: dns_str = ", ".join(dnsler)
                except: pass

                # UFW Durumu
                ufw_durum = "Bilinmiyor"
                try:
                    p = subprocess.run(["pkexec", "ufw", "status"], capture_output=True, text=True)
                    out = p.stdout.lower()
                    if "status: active" in out: ufw_durum = "Aktif (Açık)"
                    elif "status: inactive" in out: ufw_durum = "Pasif (Kapalı)"
                    else: ufw_durum = "Durum Belirsiz"
                except: ufw_durum = "Erişim Hatası"

                # Rapor Yazma
                lines = [f"--- SİSTEM ASİSTANI - DETAYLI RAPOR ---", f"Tarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}", "-" * 50]
                lines.append(f"\n[SİSTEM KİMLİĞİ]")
                lines.append(f"Kullanıcı: {kullanici} @ {hostname}")
                lines.append(f"Model: {self.pc_modeli}")
                lines.append(f"Dağıtım: {self.son_veri.get('dagitim_detay', 'Bilinmiyor')}")
                lines.append(f"Kernel: {platform.release()}")
                lines.append(f"Son Açılış Süresi: {boot_fmt}")
                
                lines.append(f"\n[DONANIM ÖZETİ]")
                lines.append(f"CPU Modeli: {self.son_veri.get('islemci_model', 'Bilinmiyor')}")
                lines.append(f"CPU Kullanımı: %{self.son_veri.get('toplam_cpu_yuzde', 0):.1f}")
                lines.append(f"CPU Sıcaklığı: {self.son_veri.get('cpu_sicaklik', 0):.1f}°C")
                lines.append(f"Çalışma Süresi (Uptime): {self.son_veri.get('uptime', 'Bilinmiyor')}")
                lines.append(f"GPU Modeli: {self.son_veri.get('ekran_karti_model', 'Bilinmiyor')}")
                lines.append(f"RAM: {self.son_veri.get('ram_toplam', '0 GB')} (Kullanım: %{self.son_veri.get('ram_yuzde', 0)})")
                
                lines.append(f"\n[AĞ VE GÜVENLİK]")
                lines.append(f"Yerel IP: {yerel_ip}")
                lines.append(f"Ağ Adı (SSID): {self.son_veri.get('ag_ssid', 'Bilinmiyor')}")
                lines.append(f"Aktif Arayüz: {self.son_veri.get('ag_arayuz', 'Bilinmiyor')}")
                lines.append(f"Servis Sağlayıcı: {self.son_veri.get('konum_bilgisi', {}).get('org', 'Bilinmiyor')}")
                lines.append(f"DNS Sunucuları: {dns_str}")
                lines.append(f"Güvenlik Duvarı (UFW): {ufw_durum}")
                
                lines.append(f"\n[GÜÇ & BATARYA]")
                bat = self.son_veri.get('batarya', {})
                if bat.get("status_yok"): lines.append("Durum: AC / Masaüstü")
                else: lines.append(f"Durum: {'Şarjda' if bat.get('plugged') else 'Pilde'} (%{bat.get('percent', 0)})")
                
                lines.append(f"\n[BAĞLI DONANIMLAR]")
                for k,v in self.tespit_edilen_donanimlar.items(): lines.append(f"{k.replace('📶','').replace('🌐','').replace('🔊','').replace('🦷','').replace('🖨️','').strip()}: {v.replace(chr(10), ', ')}")
                
                lines.append(f"\n[DEPOLAMA - FİZİKSEL]")
                for d in self.fiziksel_diskler_listesi: lines.append(d)
                
                lines.append(f"\n[DEPOLAMA - MANTIKSAL]")
                for sat in self.mantiksal_bolumler_listesi: lines.append(sat)
                
                lines.append(f"\n[YAZILIM & BAŞLANGIÇ]")
                lines.append(f"Başlangıçtaki Uygulamalar ({len(startups)}):")
                if startups:
                    for app in startups: lines.append(f"    - {app}")
                else: lines.append(f"    - Yok")
                
                lines.append(f"")
                lines.append(f"Çalışan Servisler ({len(services)}):")
                if services:
                    for srv in services: lines.append(f"    - {srv}")
                else: lines.append(f"    - Servis bilgisi alınamadı")
                
                with open(path, "w", encoding="utf-8") as f: f.write("\n".join(lines))
                QMessageBox.information(self, "Başarılı", "Kapsamlı sistem raporu başarıyla kaydedildi.")
            except Exception as e: QMessageBox.warning(self, "Hata", f"Rapor kaydedilemedi: {e}")

    def guncelle(self, veri=None):
        if not veri: return
        self.son_veri = veri
        bat = veri.get('batarya', {})
        if bat.get("status_yok"): self.lbl_durum.setText("Masaüstü (Fişte)"); self.lbl_kalan.setText("-"); self.lbl_sure.setText("-")
        else: self.lbl_durum.setText(f"%{bat.get('percent')}"); self.lbl_kalan.setText(f"{'Şarjda' if bat.get('plugged') else 'Pilde'}")
        self.lbl_gpu.setText(f"<b>GPU:</b> {veri.get('ekran_karti_model', '-')}")
        self.lbl_cpu.setText(f"<b>CPU:</b> {veri.get('islemci_model', '-')}")
        self.lbl_ram.setText(f"<b>RAM:</b> {veri.get('ram_toplam', '-')}")
        self.lbl_distro.setText(f"<b>Dağıtım:</b> {veri.get('dagitim_detay', '-')}")
        self.lbl_kernel.setText(f"<b>Kernel:</b> {platform.release()}")