# sayfalar/yonetim.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QListWidget, QMessageBox, QGroupBox, 
                             QTabWidget, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu, AyarlarYoneticisi
import subprocess
import os
import shutil
import sys

class YonetimSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.ayarlar = AyarlarYoneticisi()
        
        if os.path.exists("/usr/sbin/ufw"): self.ufw_bin = "/usr/sbin/ufw"
        elif os.path.exists("/sbin/ufw"): self.ufw_bin = "/sbin/ufw"
        else: self.ufw_bin = "/usr/sbin/ufw"

        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.ayarlar_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Sistem Yönetimi", icon))

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.tab_degisti)
        layout.addWidget(self.tabs)

        # TAB 1: BAŞLANGIÇ YÖNETİMİ (Sadeleştirildi)
        tab_start = QWidget(); l_start = QVBoxLayout(tab_start); l_start.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        grp_apps = QGroupBox("Diğer Başlangıç Uygulamaları")
        l_apps = QVBoxLayout(grp_apps)
        l_apps.addWidget(QLabel("Sistem açılışında çalışan diğer uygulamaları yönetin:"))
        
        self.list_start = QListWidget()
        l_apps.addWidget(self.list_start)
        
        btn_del = QPushButton("🗑️ Seçili Uygulamayı Kaldır")
        btn_del.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px;")
        btn_del.clicked.connect(self.del_autostart)
        l_apps.addWidget(btn_del)
        
        l_start.addWidget(grp_apps)
        
        self.tabs.addTab(tab_start, QIcon(SvgIkonOlusturucu.script_ikonu("#33AADD")), "Başlangıç")
        
        # TAB 2: UFW
        tab_sec = QWidget(); l_sec = QVBoxLayout(tab_sec)
        self.header_ufw = QHBoxLayout()
        self.lbl_ufw = QLabel("Durum: Kontrol Ediliyor..."); self.lbl_ufw.setStyleSheet("font-size: 14pt; font-weight: bold; color: #888;")
        self.header_ufw.addWidget(self.lbl_ufw)
        self.btn_install_ufw = QPushButton("📥 UFW Kur"); self.btn_install_ufw.setStyleSheet("background-color: #33AADD; color: white; font-weight: bold;")
        self.btn_install_ufw.clicked.connect(self.install_ufw); self.btn_install_ufw.hide()
        self.header_ufw.addWidget(self.btn_install_ufw); l_sec.addLayout(self.header_ufw)
        h_btn = QHBoxLayout()
        btn_on = QPushButton("✅ AÇ"); btn_on.setMinimumHeight(40); btn_on.setStyleSheet("font-weight:bold; font-size:11pt;")
        btn_on.clicked.connect(lambda: self.ufw_cmd("enable"))
        btn_off = QPushButton("⛔ KAPAT"); btn_off.setMinimumHeight(40); btn_off.setStyleSheet("font-weight:bold; font-size:11pt;")
        btn_off.clicked.connect(lambda: self.ufw_cmd("disable"))
        h_btn.addWidget(btn_on); h_btn.addWidget(btn_off); l_sec.addLayout(h_btn)
        l_sec.addWidget(QLabel("Mevcut Kurallar:"))
        self.list_rules = QListWidget(); self.list_rules.setStyleSheet("font-family: Monospace; font-size: 10pt;")
        l_sec.addWidget(self.list_rules)
        self.tabs.addTab(tab_sec, QIcon(SvgIkonOlusturucu.anahtar_ikonu("#e67e22")), "Güvenlik Duvarı")
        
        # TAB 3: SERVICES
        tab_serv = QWidget(); l_serv = QVBoxLayout(tab_serv)
        l_serv.addWidget(QLabel("Çalışan Kritik Servisler"))
        self.list_serv = QListWidget(); l_serv.addWidget(self.list_serv)
        btn_stop = QPushButton("⛔ Seçili Servisi Durdur"); btn_stop.clicked.connect(self.stop_service)
        l_serv.addWidget(btn_stop)
        self.tabs.addTab(tab_serv, QIcon(SvgIkonOlusturucu.process_ikonu("#9b59b6")), "Servisler")

        self.load_autostart(); self.load_services()

    def tab_degisti(self, index):
        if index == 1: 
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.check_ufw(sessiz=False))

    def check_ufw(self, sessiz=False):
        if not os.path.exists(self.ufw_bin):
            self.lbl_ufw.setText("Durum: UFW Dosyası Yok"); self.lbl_ufw.setStyleSheet("color: #e74c3c; font-weight:bold;"); self.btn_install_ufw.show(); return
        self.btn_install_ufw.hide()
        try:
            cmd = ["pkexec", self.ufw_bin, "status"]
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                self.list_rules.clear(); self.parse_ufw_output(process.stdout)
            else:
                if not sessiz: self.lbl_ufw.setText("Durum: Erişim Reddedildi")
        except Exception as e:
            if not sessiz: self.lbl_ufw.setText(f"Hata: {str(e)}")

    def ufw_cmd(self, action):
        if not os.path.exists(self.ufw_bin): QMessageBox.warning(self, "Hata", f"UFW bulunamadı."); return
        try: 
            full_cmd = f"{self.ufw_bin} {action} && {self.ufw_bin} status"
            cmd = ["pkexec", "sh", "-c", full_cmd]
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0: self.list_rules.clear(); self.parse_ufw_output(process.stdout)
            else: err = process.stderr if process.stderr else "Yetki verilmedi."; QMessageBox.warning(self, "İşlem Tamamlanamadı", f"Hata: {err}")
        except Exception as e: QMessageBox.critical(self, "Hata", f"İşlem başarısız: {e}")

    def parse_ufw_output(self, out):
        out_lower = out.lower()
        if "inactive" in out_lower: self.lbl_ufw.setText("Durum: KAPALI 🔴"); self.lbl_ufw.setStyleSheet("color: #e74c3c; font-weight:bold; font-size: 14pt;")
        elif "active" in out_lower:
            self.lbl_ufw.setText("Durum: AÇIK 🟢"); self.lbl_ufw.setStyleSheet("color: #2ecc71; font-weight:bold; font-size: 14pt;")
            lines = out.split('\n'); capture = False
            for l in lines:
                if "To" in l and "Action" in l: capture = True; continue
                if capture and l.strip(): self.list_rules.addItem(l.strip())
        else: 
            if "active" in out_lower: self.lbl_ufw.setText("Durum: AÇIK 🟢"); self.lbl_ufw.setStyleSheet("color: #2ecc71; font-weight:bold; font-size: 14pt;")
            else: self.lbl_ufw.setText("Durum: Bilinmiyor ⚪")

    def install_ufw(self):
        QMessageBox.information(self, "Kurulum", "UFW kurulumu başlatılacak.\nLütfen açılan pencerede root şifrenizi giriniz.")
        cmd = "export DEBIAN_FRONTEND=noninteractive; apt-get update && apt-get install ufw -y"
        try:
            process = subprocess.run(["pkexec", "sh", "-c", cmd], capture_output=True, text=True)
            if process.returncode == 0:
                if os.path.exists(self.ufw_bin): QMessageBox.information(self, "Başarılı", "UFW kuruldu."); self.check_ufw()
                else: QMessageBox.warning(self, "Uyarı", f"Kurulum bitti ama '{self.ufw_bin}' dosyası hala yok.")
            else: err_msg = process.stderr if process.stderr else "Yetki verilmedi."; QMessageBox.critical(self, "Hata", f"Kurulum başarısız:\n{err_msg}")
        except Exception as e: QMessageBox.critical(self, "Kritik Hata", f"İşlem yürütülemedi: {str(e)}")
    
    def load_autostart(self):
        self.list_start.clear(); p = os.path.expanduser("~/.config/autostart")
        if os.path.exists(p):
            for f in os.listdir(p):
                if f.endswith(".desktop"): self.list_start.addItem(f)
    def del_autostart(self):
        i = self.list_start.currentItem()
        if i:
            try: os.remove(os.path.expanduser(f"~/.config/autostart/{i.text()}")); self.load_autostart()
            except: pass
    def load_services(self):
        self.list_serv.clear()
        try:
            o = subprocess.check_output("systemctl list-units --type=service --state=running --no-pager", shell=True, text=True)
            for l in o.split('\n')[1:-7]:
                if l.split(): self.list_serv.addItem(l.split()[0])
        except: pass
    def stop_service(self):
        i = self.list_serv.currentItem()
        if i: subprocess.run(["pkexec", "systemctl", "stop", i.text()]); self.load_services()