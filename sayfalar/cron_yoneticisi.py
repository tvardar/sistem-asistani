# sayfalar/cron_yoneticisi.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHeaderView, QMessageBox, 
                             QComboBox, QLineEdit, QGroupBox, QSpinBox, QCheckBox, 
                             QDialog, QTextEdit, QTimeEdit, QApplication)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import os

class LogPenceresi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cron İşlem Logları")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: Monospace;")
        layout.addWidget(self.text_area)
        
        btn_yenile = QPushButton("Yenile")
        btn_yenile.clicked.connect(self.loglari_oku)
        layout.addWidget(btn_yenile)
        
        self.loglari_oku()
        
    def loglari_oku(self):
        log_path = os.path.expanduser("~/sistem_asistani_cron.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                # Son 2000 karakteri oku
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(size - 2000, 0))
                content = f.read()
                self.text_area.setText(content)
                # Scroll en alta
                sb = self.text_area.verticalScrollBar()
                sb.setValue(sb.maximum())
        else:
            self.text_area.setText("Henüz bir log kaydı yok.")

class CronYoneticisiSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.cron_ikonu("#33AADD", 32)
        
        # Üst Başlık ve Sistem Saati
        header_layout = QHBoxLayout()
        header_layout.addWidget(SayfaBasligi("Görev Zamanlayıcı (Cron İşleri)", icon))
        
        self.lbl_sistem_saati = QLabel()
        self.lbl_sistem_saati.setStyleSheet("color: #e67e22; font-weight: bold; font-size: 11pt;")
        header_layout.addWidget(self.lbl_sistem_saati)
        self.layout.addLayout(header_layout)
        
        # Saat Güncelleyici
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.saati_guncelle)
        self.timer.start(1000)
        self.saati_guncelle()

        # --- GÖREV OLUŞTURUCU ---
        grp_ekle = QGroupBox("Yeni Görev Planla")
        l_form = QVBoxLayout(grp_ekle)
        l_form.setSpacing(10)
        
        # 1. Sıklık Seçimi
        h_freq = QHBoxLayout()
        h_freq.addWidget(QLabel("Tekrar Sıklığı:"))
        self.combo_freq = QComboBox()
        self.combo_freq.addItems(["Günlük", "Haftalık", "Aylık", "Yıllık", "Her Dakika (Test İçin)"])
        self.combo_freq.currentTextChanged.connect(self.arayuz_guncelle)
        h_freq.addWidget(self.combo_freq)
        h_freq.addStretch()
        l_form.addLayout(h_freq)
        
        # 2. Dinamik Zaman Seçiciler
        self.container_time = QGroupBox("Zaman Ayarları")
        self.container_time.setStyleSheet("QGroupBox { border: 1px solid #ddd; border-radius: 5px; margin-top: 5px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        l_time_inner = QHBoxLayout(self.container_time)
        
        # Ay (Sadece Yıllıkta)
        self.lbl_month = QLabel("Ay:")
        self.combo_month = QComboBox()
        self.combo_month.addItems(["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                                   "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"])
        l_time_inner.addWidget(self.lbl_month)
        l_time_inner.addWidget(self.combo_month)
        
        # Gün (Ayın Günü) - Aylık ve Yıllıkta
        self.lbl_dom = QLabel("Gün:")
        self.spin_dom = QSpinBox(); self.spin_dom.setRange(1, 31)
        l_time_inner.addWidget(self.lbl_dom)
        l_time_inner.addWidget(self.spin_dom)
        
        # Haftanın Günü (Sadece Haftalıkta)
        self.lbl_dow = QLabel("Gün:")
        self.combo_dow = QComboBox()
        self.combo_dow.addItems(["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"])
        l_time_inner.addWidget(self.lbl_dow)
        l_time_inner.addWidget(self.combo_dow)
        
        # Saat ve Dakika (Her zaman)
        l_time_inner.addWidget(QLabel("|  Saat:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        l_time_inner.addWidget(self.time_edit)
        
        l_time_inner.addStretch()
        l_form.addWidget(self.container_time)
        
        # 3. Komut ve Log
        h_cmd = QHBoxLayout()
        self.txt_komut = QLineEdit()
        self.txt_komut.setPlaceholderText("Örn: python3 /home/kullanici/script.py")
        h_cmd.addWidget(QLabel("Komut:"))
        h_cmd.addWidget(self.txt_komut)
        l_form.addLayout(h_cmd)
        
        h_opts = QHBoxLayout()
        self.chk_log = QCheckBox("Log Kaydı Tut (Sonuçları Görmek İçin)")
        self.chk_log.setChecked(True)
        self.chk_log.setToolTip("İşlemin çıktısını ~/sistem_asistani_cron.log dosyasına yazar.")
        h_opts.addWidget(self.chk_log)
        
        btn_ekle = QPushButton("✅ Planla")
        btn_ekle.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 5px 15px;")
        btn_ekle.clicked.connect(self.gorev_ekle)
        h_opts.addStretch()
        h_opts.addWidget(btn_ekle)
        l_form.addLayout(h_opts)
        
        self.layout.addWidget(grp_ekle)

        # --- LİSTE VE LOG BUTONU ---
        h_list_header = QHBoxLayout()
        h_list_header.addWidget(QLabel("<b>Aktif Görevler</b>"))
        h_list_header.addStretch()
        btn_view_logs = QPushButton("📜 Logları Göster")
        btn_view_logs.clicked.connect(self.log_penceresi_ac)
        h_list_header.addWidget(btn_view_logs)
        self.layout.addLayout(h_list_header)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Zamanlama (Cron)", "Açıklama", "Komut"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.table)

        btn_sil = QPushButton("🗑️ Seçili Görevi Sil")
        btn_sil.setStyleSheet("background-color: #c0392b; color: white; padding: 6px;")
        btn_sil.clicked.connect(self.gorev_sil)
        self.layout.addWidget(btn_sil)

        self.arayuz_guncelle("Günlük") # Varsayılan görünüm
        self.listeyi_yukle()

    def saati_guncelle(self):
        # Sistem saatini göster (Cron'un çalıştığı saat budur)
        now = QDateTime.currentDateTime()
        self.lbl_sistem_saati.setText(f"Sistem Saati: {now.toString('dd.MM.yyyy HH:mm:ss')} (Yerel)")

    def arayuz_guncelle(self, freq):
        # Hepsini gizle önce
        self.lbl_month.hide(); self.combo_month.hide()
        self.lbl_dom.hide(); self.spin_dom.hide()
        self.lbl_dow.hide(); self.combo_dow.hide()
        self.time_edit.setEnabled(True)
        
        if freq == "Günlük":
            # Sadece Saat:Dakika
            pass 
        elif freq == "Haftalık":
            self.lbl_dow.show(); self.combo_dow.show()
        elif freq == "Aylık":
            self.lbl_dom.show(); self.spin_dom.show()
        elif freq == "Yıllık":
            self.lbl_dom.show(); self.spin_dom.show()
            self.lbl_month.show(); self.combo_month.show()
        elif freq == "Her Dakika (Test İçin)":
            self.time_edit.setEnabled(False)

    def log_penceresi_ac(self):
        dlg = LogPenceresi(self)
        dlg.exec()

    def listeyi_yukle(self):
        self.table.setRowCount(0)
        try:
            out = subprocess.check_output("crontab -l", shell=True, text=True, stderr=subprocess.DEVNULL)
            lines = out.splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"): continue
                
                parts = line.split(maxsplit=5)
                if len(parts) >= 6:
                    zaman_kod = " ".join(parts[:5])
                    komut = parts[5]
                    
                    # Log eklentisini temizle (görünüm için)
                    display_komut = komut.split(" >>")[0]
                    
                    aciklama = self.cron_cozumle(zaman_kod)
                    
                    r = self.table.rowCount()
                    self.table.insertRow(r)
                    self.table.setItem(r, 0, QTableWidgetItem(zaman_kod))
                    self.table.setItem(r, 1, QTableWidgetItem(aciklama))
                    self.table.setItem(r, 2, QTableWidgetItem(display_komut))
        except: pass

    def cron_cozumle(self, cron_str):
        # Basit bir açıklama oluşturucu
        p = cron_str.split()
        if len(p) != 5: return "Özel/Karmaşık"
        m, h, dom, mon, dow = p
        
        try:
            if cron_str == "* * * * *": return "Her Dakika"
            if dom == "*" and mon == "*" and dow == "*": return f"Her Gün {h}:{m}"
            if dom == "*" and mon == "*" and dow != "*": 
                gunler = ["Pazar", "Pzt", "Salı", "Çarş", "Perş", "Cuma", "Cmt"]
                return f"Her {gunler[int(dow)]} {h}:{m}"
            if dom != "*" and mon == "*" and dow == "*": return f"Her Ayın {dom}. günü {h}:{m}"
            if dom != "*" and mon != "*": return f"Her Yıl {dom}.{mon} tarihinde {h}:{m}"
        except: pass
        return "Özel Zamanlama"

    def gorev_ekle(self):
        base_komut = self.txt_komut.text().strip()
        if not base_komut:
            QMessageBox.warning(self, "Hata", "Lütfen bir komut girin.")
            return

        # Loglama ekle
        final_komut = base_komut
        if self.chk_log.isChecked():
            log_file = os.path.expanduser("~/sistem_asistani_cron.log")
            # Tarih ekleyerek logla
            final_komut = f'echo "$(date): {base_komut} calisti" >> {log_file} && {base_komut} >> {log_file} 2>&1'

        freq = self.combo_freq.currentText()
        time = self.time_edit.time()
        m = time.minute()
        h = time.hour()
        
        cron_str = ""
        
        if freq == "Günlük":
            cron_str = f"{m} {h} * * *"
        elif freq == "Haftalık":
            # Pazar=0, Cmt=6
            dow = self.combo_dow.currentIndex()
            cron_str = f"{m} {h} * * {dow}"
        elif freq == "Aylık":
            dom = self.spin_dom.value()
            cron_str = f"{m} {h} {dom} * *"
        elif freq == "Yıllık":
            dom = self.spin_dom.value()
            mon = self.combo_month.currentIndex() + 1
            cron_str = f"{m} {h} {dom} {mon} *"
        elif freq == "Her Dakika (Test İçin)":
            cron_str = "* * * * *"

        # Mevcut crontab'ı oku ve ekle
        try:
            try:
                mevcut = subprocess.check_output("crontab -l", shell=True, text=True, stderr=subprocess.DEVNULL)
            except: mevcut = ""
            
            yeni_satir = f"{cron_str} {final_komut}"
            if yeni_satir in mevcut:
                QMessageBox.warning(self, "Bilgi", "Bu görev zaten listede var.")
                return

            yeni_crontab = mevcut + "\n" + yeni_satir + "\n"
            
            p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=yeni_crontab)
            
            if p.returncode == 0:
                self.listeyi_yukle()
                self.txt_komut.clear()
                QMessageBox.information(self, "Başarılı", "Görev sisteme eklendi.")
            else:
                QMessageBox.critical(self, "Hata", "Crontab güncellenemedi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def gorev_sil(self):
        row = self.table.currentRow()
        if row < 0: return
        
        cron_part = self.table.item(row, 0).text()
        
        if QMessageBox.question(self, "Sil", "Seçili görevi silmek istiyor musunuz?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return

        try:
            mevcut = subprocess.check_output("crontab -l", shell=True, text=True)
            yeni_liste = []
            silindi = False
            
            # Tablodan seçilen komutun görsel hali (logsuz)
            secilen_gorunen_komut = self.table.item(row, 2).text()
            
            for line in mevcut.splitlines():
                line = line.strip()
                if not line or line.startswith("#"): 
                    yeni_liste.append(line)
                    continue
                
                # Eşleşme kontrolü: Zaman kodu TUTUYOR MU ve Komut İÇERİYOR MU?
                if line.startswith(cron_part) and secilen_gorunen_komut in line:
                    if not silindi: # Sadece ilk eşleşeni sil (Duplicate varsa)
                        silindi = True
                        continue
                
                yeni_liste.append(line)
            
            yeni_crontab = "\n".join(yeni_liste) + "\n"
            p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=yeni_crontab)
            self.listeyi_yukle()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))