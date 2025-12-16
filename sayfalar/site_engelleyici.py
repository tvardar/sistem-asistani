# sayfalar/site_engelleyici.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QPushButton, QLineEdit, QMessageBox, QGroupBox, QTimeEdit, QTabWidget)
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import os
import subprocess

class SiteEngelleyiciSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.block_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Site Engelleyici & Erişim Kontrolü", icon))

        self.hosts_path = "/etc/hosts"
        self.temp_hosts = "/tmp/hosts_temp"

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # TAB 1: Site Engelleme
        tab_site = QWidget(); l_site = QVBoxLayout(tab_site)
        l_site.addWidget(QLabel("Bu araç, bilgisayarınızdan belirli web sitelerine erişimi tamamen engeller.\nİşlemler sistem (root) yetkisi gerektirir."))

        grp_ekle = QGroupBox("Yeni Site Engelle")
        l_ekle = QHBoxLayout(grp_ekle)
        self.txt_site = QLineEdit(); self.txt_site.setPlaceholderText("Örn: microsoft.com")
        btn_ekle = QPushButton("🚫 Engelle (Root)"); btn_ekle.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn_ekle.clicked.connect(self.site_ekle)
        l_ekle.addWidget(self.txt_site); l_ekle.addWidget(btn_ekle); l_site.addWidget(grp_ekle)

        l_site.addWidget(QLabel("<b>Şu An Engelli Olan Siteler:</b>"))
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("font-family: Monospace; font-size: 11pt;") 
        l_site.addWidget(self.list_widget)

        h_btn = QHBoxLayout()
        btn_yenile = QPushButton("🔄 Listeyi Yenile"); btn_yenile.clicked.connect(self.listeyi_yukle); h_btn.addWidget(btn_yenile)
        btn_kaldir = QPushButton("✅ Seçili Engeli Kaldır (Root)"); btn_kaldir.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_kaldir.clicked.connect(self.site_kaldir); h_btn.addWidget(btn_kaldir)
        l_site.addLayout(h_btn); self.listeyi_yukle(); tabs.addTab(tab_site, "Web Sitesi Engelleme")

        # TAB 2: Zamanlayıcı
        tab_time = QWidget(); l_time = QVBoxLayout(tab_time)
        grp_zaman = QGroupBox("İnternet Erişimini Zamanla")
        lz = QVBoxLayout(grp_zaman)
        lz.addWidget(QLabel("Belirlediğiniz saatler arasında internet erişimi <b>tamamen kapatılır</b>."))
        
        h_t = QHBoxLayout()
        h_t.addWidget(QLabel("Başlangıç Saati (Kapanış):")); self.time_start = QTimeEdit(); self.time_start.setDisplayFormat("HH:mm"); h_t.addWidget(self.time_start)
        h_t.addWidget(QLabel("Bitiş Saati (Açılış):")); self.time_end = QTimeEdit(); self.time_end.setDisplayFormat("HH:mm"); h_t.addWidget(self.time_end)
        lz.addLayout(h_t)
        
        btn_zaman_kur = QPushButton("💾 Zamanlamayı Kaydet (Root)"); btn_zaman_kur.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 8px;")
        btn_zaman_kur.clicked.connect(self.zamanlama_kur); lz.addWidget(btn_zaman_kur)
        btn_zaman_sil = QPushButton("🗑️ Zamanlamayı İptal Et (Root)"); btn_zaman_sil.clicked.connect(self.zamanlama_sil); lz.addWidget(btn_zaman_sil)
        l_time.addWidget(grp_zaman)
        
        l_time.addStretch(); tabs.addTab(tab_time, "Zamanlama")

    def listeyi_yukle(self):
        self.list_widget.clear()
        try:
            with open(self.hosts_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("0.0.0.0") and " " in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            site = parts[1]
                            if site != "0.0.0.0": self.list_widget.addItem(site)
        except Exception as e: QMessageBox.warning(self, "Hata", f"Hosts dosyası okunamadı: {e}")

    def site_ekle(self):
        site = self.txt_site.text().strip()
        if not site: return
        site = site.replace("https://", "").replace("http://", "").split("/")[0]
        entry = f"\n0.0.0.0 {site}\n0.0.0.0 www.{site}"
        try:
            cmd = f"echo '{entry}' >> {self.hosts_path}"
            subprocess.run(["pkexec", "sh", "-c", cmd], check=True)
            self.txt_site.clear(); self.listeyi_yukle(); QMessageBox.information(self, "Başarılı", f"{site} engellendi.")
        except: QMessageBox.critical(self, "Hata", "Erişim engellendi.")

    def site_kaldir(self):
        item = self.list_widget.currentItem()
        if not item: QMessageBox.warning(self, "Seçim Yok", "Lütfen listeden seçim yapın."); return
        site = item.text()
        if QMessageBox.question(self, "Onay", f"'{site}' engelini kaldırmak istiyor musunuz?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return
        try:
            with open(self.hosts_path, "r") as f: lines = f.readlines()
            new_lines = []
            for line in lines:
                if site not in line: new_lines.append(line)
            with open(self.temp_hosts, "w") as f: f.writelines(new_lines)
            cmd = f"mv {self.temp_hosts} {self.hosts_path}"
            subprocess.run(["pkexec", "sh", "-c", cmd], check=True)
            self.listeyi_yukle(); QMessageBox.information(self, "Başarılı", "Engel kaldırıldı.")
        except Exception as e: QMessageBox.critical(self, "Hata", f"İşlem başarısız: {e}")

    def zamanlama_kur(self):
        start = self.time_start.time().toString("HH:mm"); end = self.time_end.time().toString("HH:mm")
        sh, sm = start.split(":"); eh, em = end.split(":")
        cmd_block = "/usr/sbin/ufw default deny outgoing"; cmd_allow = "/usr/sbin/ufw default allow outgoing"
        cron_block = f"{sm} {sh} * * * {cmd_block} #SistemAsistani_Block"
        cron_allow = f"{em} {eh} * * * {cmd_allow} #SistemAsistani_Allow"
        try:
            self.zamanlama_sil_silent()
            script = f"(crontab -l 2>/dev/null; echo \"{cron_block}\"; echo \"{cron_allow}\") | crontab -"
            subprocess.run(["pkexec", "bash", "-c", script], check=True)
            QMessageBox.information(self, "Başarılı", f"Zamanlama kuruldu:\n{start}'da internet KAPANACAK.\n{end}'da internet AÇILACAK.")
        except Exception as e: QMessageBox.critical(self, "Hata", f"Zamanlama kurulamadı: {e}")

    def zamanlama_sil(self):
        try: self.zamanlama_sil_silent(); QMessageBox.information(self, "Başarılı", "Zamanlanmış kısıtlamalar kaldırıldı.")
        except: QMessageBox.warning(self, "Hata", "Silme işlemi başarısız oldu.")
    def zamanlama_sil_silent(self):
        script = "crontab -l | grep -v '#SistemAsistani_' | crontab -"; subprocess.run(["pkexec", "bash", "-c", script], check=True)