# sayfalar/ayarlar.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QComboBox, QCheckBox, QPushButton, QMessageBox, QApplication)
from PyQt6.QtCore import Qt  # <--- EKSİK OLAN BU SATIR EKLENDİ
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu, AyarlarYoneticisi
import os
import sys
import requests
import webbrowser

class AyarlarSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.ayarlar = AyarlarYoneticisi()
        self.autostart_path = os.path.expanduser("~/.config/autostart/sistem-asistani.desktop")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        icon = SvgIkonOlusturucu.ayarlar_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Uygulama Ayarları", icon))

        # --- 1. GÖRÜNÜM ---
        grp_tema = QGroupBox("Görünüm ve Tema")
        l_tema = QVBoxLayout(grp_tema)
        l_tema.setSpacing(20)
        l_tema.setContentsMargins(20, 30, 20, 20)

        h_tema = QHBoxLayout()
        h_tema.addWidget(QLabel("Uygulama Teması:"))
        self.combo_tema = QComboBox()
        self.combo_tema.setFixedWidth(200)
        self.combo_tema.addItems(["Otomatik", "Koyu", "Açık"])
        self.combo_tema.setCurrentText(self.ayarlar.ayarlar.get("tema", "Otomatik"))
        self.combo_tema.currentTextChanged.connect(self.tema_degistir)
        h_tema.addWidget(self.combo_tema)
        h_tema.addStretch()
        l_tema.addLayout(h_tema)
        
        h_renk = QHBoxLayout()
        h_renk.addWidget(QLabel("Vurgu Rengi:"))
        self.combo_renk = QComboBox()
        self.combo_renk.setFixedWidth(200)
        self.renkler = {"Mavi": "#33AADD", "Turuncu": "#e67e22", "Yeşil": "#2ecc71", "Mor": "#9b59b6", "Kırmızı": "#e74c3c", "Gri": "#7f8c8d"}
        for k in self.renkler: self.combo_renk.addItem(k)
        
        cur_color = self.ayarlar.ayarlar.get("renk", "#33AADD")
        secili_isim = "Mavi"
        for ad, kod in self.renkler.items():
            if kod == cur_color: secili_isim = ad; break
        self.combo_renk.setCurrentText(secili_isim)
        self.combo_renk.currentTextChanged.connect(self.tema_degistir)
        h_renk.addWidget(self.combo_renk)
        h_renk.addStretch()
        l_tema.addLayout(h_renk)
        layout.addWidget(grp_tema)

        # --- 2. GÜNCELLEME ---
        grp_update = QGroupBox("Sürüm ve Güncelleme")
        l_upd = QVBoxLayout(grp_update)
        l_upd.setContentsMargins(20, 30, 20, 20)
        
        h_upd = QHBoxLayout()
        self.lbl_surum_bilgisi = QLabel("Mevcut Sürüm: Bilinmiyor")
        if self.main_window:
            self.lbl_surum_bilgisi.setText(f"Mevcut Sürüm: {self.main_window.SURUM}")
        self.lbl_surum_bilgisi.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        
        self.btn_check_update = QPushButton("🚀 Güncellemeleri Kontrol Et")
        self.btn_check_update.setFixedWidth(220)
        self.btn_check_update.clicked.connect(self.guncelleme_kontrol)
        
        h_upd.addWidget(self.lbl_surum_bilgisi)
        h_upd.addStretch()
        h_upd.addWidget(self.btn_check_update)
        l_upd.addLayout(h_upd)
        layout.addWidget(grp_update)

        # --- 3. SİSTEM DAVRANIŞI ---
        grp_davranis = QGroupBox("Sistem Davranışı")
        l_dav = QVBoxLayout(grp_davranis)
        l_dav.setContentsMargins(20, 30, 20, 20)

        self.chk_autostart = QCheckBox("Uygulamayı sistem açılışında otomatik başlat")
        # Qt.CursorShape kullanımı için yukarıdaki import Qt gereklidir
        self.chk_autostart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_autostart.setChecked(os.path.exists(self.autostart_path))
        self.chk_autostart.toggled.connect(self.toggle_autostart)
        l_dav.addWidget(self.chk_autostart)
        
        lbl_info = QLabel("<i>ℹ️ Etkinleştirildiğinde: Sistem açıldığında Asistan arka planda (sağ alt tepside) sessizce çalışmaya başlar.</i>")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: palette(mid); margin-left: 32px; margin-top: 5px;")
        l_dav.addWidget(lbl_info)

        layout.addWidget(grp_davranis)
        layout.addStretch()

    def tema_degistir(self):
        secim_tema = self.combo_tema.currentText()
        secim_renk_ad = self.combo_renk.currentText()
        secim_renk_kod = self.renkler[secim_renk_ad]
        self.ayarlar.kaydet("tema", secim_tema)
        self.ayarlar.kaydet("renk", secim_renk_kod)
        if self.main_window: self.main_window.tema_uygula()

    def toggle_autostart(self, checked):
        if checked:
            try:
                os.makedirs(os.path.dirname(self.autostart_path), exist_ok=True)
                if getattr(sys, 'frozen', False): exec_cmd = sys.executable
                else: exec_cmd = f"{sys.executable} {os.path.abspath('sistem_asistani.py')}"
                content = f"[Desktop Entry]\nType=Application\nName=Sistem Asistanı\nComment=Sistem Bakım\nExec={exec_cmd}\nX-GNOME-Autostart-enabled=true\nIcon=sistem-asistani\n"
                with open(self.autostart_path, "w") as f: f.write(content)
            except: self.chk_autostart.setChecked(False)
        else:
            if os.path.exists(self.autostart_path):
                try: os.remove(self.autostart_path)
                except: pass

    def guncelleme_kontrol(self):
        self.btn_check_update.setText("Kontrol Ediliyor...")
        self.btn_check_update.setEnabled(False)
        QApplication.processEvents()
        
        # GitHub Repo Bilgileri
        repo_owner = "tvardar"
        repo_name = "sistem-asistani"
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        mevcut_surum = self.main_window.SURUM if self.main_window else "v1.0"
        
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_tag = data.get("tag_name", "v1.0")
                html_url = data.get("html_url", "")
                
                # --- SÜRÜM KARŞILAŞTIRMA MANTIĞI ---
                def surum_to_int(v):
                    # Sadece sayısal kısımları al (v1.0 -> 10, v1.1 -> 11)
                    return int(''.join(filter(str.isdigit, v)))

                try:
                    v_remote = surum_to_int(latest_tag)
                    v_local = surum_to_int(mevcut_surum)
                except:
                    v_remote = 0
                    v_local = 0

                if v_remote > v_local:
                    msg = QMessageBox(self)
                    msg.setWindowTitle("Güncelleme Mevcut")
                    msg.setText(f"<b>Yeni Sürüm Bulundu: {latest_tag}</b>")
                    msg.setInformativeText("Yeni sürümü GitHub üzerinden indirip kurmak ister misiniz?")
                    msg.setIcon(QMessageBox.Icon.Information)
                    btn_git = msg.addButton("İndir (GitHub)", QMessageBox.ButtonRole.AcceptRole)
                    msg.addButton("İptal", QMessageBox.ButtonRole.RejectRole)
                    msg.exec()
                    
                    if msg.clickedButton() == btn_git:
                        webbrowser.open(html_url)
                
                elif v_remote == v_local:
                    QMessageBox.information(self, "Güncel", f"Sisteminiz zaten en güncel sürümde ({mevcut_surum}).")
                
                else:
                    QMessageBox.information(self, "Geliştirici Sürümü", f"Yerel sürümünüz ({mevcut_surum}), sunucudan ({latest_tag}) daha yeni.")

            else:
                QMessageBox.warning(self, "Hata", "GitHub sunucusundan bilgi alınamadı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Bağlantı hatası: {str(e)}")
        
        self.btn_check_update.setText("🚀 Güncellemeleri Kontrol Et")
        self.btn_check_update.setEnabled(True)