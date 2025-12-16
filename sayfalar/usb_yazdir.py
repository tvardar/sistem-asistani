# sayfalar/usb_yazdir.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QFileDialog, QMessageBox, 
                             QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import os
import re
import time

# --- YAZDIRMA İŞ PARÇACIĞI ---
class YazdirmaWorker(QThread):
    ilerleme_sinyali = pyqtSignal(str) # Konsola yazılacak her satır için
    tamamlandi_sinyali = pyqtSignal(bool, str) # Başarı durumu ve mesaj

    def __init__(self, iso_path, usb_dev):
        super().__init__()
        self.iso_path = iso_path
        self.usb_dev = usb_dev

    def run(self):
        # dd komutu root yetkisi gerektirir ve ilerleme bilgisi stderr'e yazılır.
        cmd = f"pkexec dd if='{self.iso_path}' of={self.usb_dev} bs=4M status=progress oflag=sync"
        
        try:
            self.ilerleme_sinyali.emit("Yazma işlemi başlatılıyor. Root yetkisi için şifre istenebilir...")
            time.sleep(1.5) # pkexec penceresinin açılması için kısa bekleme

            process = subprocess.Popen(
                cmd, 
                shell=True,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1 # Satır bazlı çıktı okumayı kolaylaştırır
            )
            
            # Canlı stderr çıktısını okuma (dd'nin ilerleme bilgisi)
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.ilerleme_sinyali.emit(line.strip())
            
            # İşlem bittikten sonra dönüş kodunu kontrol et
            return_code = process.wait()

            if return_code == 0:
                self.tamamlandi_sinyali.emit(True, "ISO kalıbı başarılı bir şekilde yazdırıldı! USB artık çalıştırılabilir (bootable).")
            else:
                self.tamamlandi_sinyali.emit(False, f"Yazdırma işlemi başarısız oldu. Hata kodu: {return_code}. Lütfen şifreyi doğru girdiğinizden emin olun.")

        except Exception as e:
            self.tamamlandi_sinyali.emit(False, f"İşlem sırasında beklenmedik bir hata oluştu: {e}")

# --- ARABİRİM SINIFI ---
class UsbYazdirSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.usb_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("USB ISO Yazdırıcı", icon))

        # *** GÜVEN VEREN AÇIKLAMA ***
        info = QLabel(
            "Bu araç, **dd modu** kullanılarak ISO dosyanızdan çalıştırılabilir (bootable) bir USB oluşturur. "
            "Lütfen doğru diski seçtiğinizden emin olun, zira **seçilen USB belleğin içeriği tamamen SİLİNECEKTİR**."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #2980b9; padding: 5px; border: 1px solid #3498db; background-color: #ecf0f1;")
        layout.addWidget(info)
        layout.addSpacing(10)


        # 1. ISO Seçim Alanı
        layout.addWidget(QLabel("1. ISO Dosyası Seçin:"))
        self.btn_iso = QPushButton("Dosya Seç...")
        self.btn_iso.clicked.connect(self.iso_sec)
        
        h_iso = QHBoxLayout()
        h_iso.addWidget(self.btn_iso)
        self.lbl_iso = QLabel("Seçilmedi")
        self.lbl_iso.setStyleSheet("color:#e67e22;")
        h_iso.addWidget(self.lbl_iso)
        layout.addLayout(h_iso)
        

        # 2. USB Seçim Alanı
        layout.addSpacing(20)
        layout.addWidget(QLabel("2. Hedef USB Bellek Seçin (DİKKAT: Veriler Silinir!):"))
        self.combo_usb = QComboBox()
        layout.addWidget(self.combo_usb)
        self.btn_refresh = QPushButton("🔄 Listeyi Yenile")
        self.btn_refresh.clicked.connect(self.diskleri_getir)
        layout.addWidget(self.btn_refresh)

        # 3. Konsol Çıktı Alanı
        layout.addSpacing(15)
        layout.addWidget(QLabel("3. Yazdırma İlerlemesi (dd Çıktısı):"))
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace; padding: 5px;")
        self.console_log.setPlaceholderText("Yazdırma işlemi başlatıldığında ilerleme bilgileri burada görünecektir...")
        self.console_log.setMaximumHeight(150)
        layout.addWidget(self.console_log)


        # 4. Başlat Butonu
        layout.addSpacing(20)
        self.btn_yaz = QPushButton("🔥 YAZDIRMAYI BAŞLAT")
        self.btn_yaz.setStyleSheet("background-color:#c0392b; color:white; font-weight:bold; font-size:12pt; padding:10px;")
        self.btn_yaz.clicked.connect(self.yazdir)
        layout.addWidget(self.btn_yaz)

        self.diskleri_getir()
        layout.addStretch()

    # --- Yardımcı Metotlar ---
    def append_log(self, message):
        """Konsola log mesajı ekler."""
        self.console_log.append(message)
        self.console_log.ensureCursorVisible()

    def iso_sec(self):
        f, _ = QFileDialog.getOpenFileName(self, "ISO Seç", "", "Disk Kalıbı (*.iso)")
        if f:
            self.lbl_iso.setText(f)
            self.lbl_iso.setStyleSheet("color:#2ecc71;")

    def diskleri_getir(self):
        self.combo_usb.clear()
        self.append_log("USB aygıtları listeleniyor...")
        try:
            # Sadece diskleri listeler, TYPE=disk ve TRAN=usb olanları filtreler
            out = subprocess.check_output("lsblk -d -n -o NAME,MODEL,SIZE,TYPE,TRAN", shell=True, text=True)
            usb_found = False
            for line in out.splitlines():
                if "disk" in line.lower() and "usb" in line.lower():
                    parts = line.split()
                    
                    try:
                        name = parts[0]
                        size = parts[-3]
                        # Model ismini ortadan bulmaya çalışıyoruz
                        model_parts = parts[1:-3]
                        model = " ".join(model_parts)
                        
                        dev = f"/dev/{name}"
                        self.combo_usb.addItem(f"{model} ({size}) - {dev}", dev)
                        usb_found = True
                    except IndexError:
                         pass # Hatalı satırları atla
            
            if not usb_found:
                 self.combo_usb.addItem("USB Bellek Bulunamadı")
                 self.append_log("USB aygıtı bulunamadı.")
            else:
                 self.append_log(f"{self.combo_usb.count()} adet USB aygıtı bulundu.")

        except Exception as e: 
            self.combo_usb.addItem("Liste Hata Verdi")
            self.append_log(f"Hata: Disk listesi alınamadı: {e}")

    # --- Yazdırma Metodu ---
    def yazdir(self):
        iso = self.lbl_iso.text()
        if not os.path.exists(iso) or iso == "Seçilmedi":
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir ISO dosyası seçin.")
            return
        
        usb_dev = self.combo_usb.currentData()
        if not usb_dev or usb_dev == "USB Bellek Bulunamadı" or not usb_dev.startswith("/dev/"):
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir USB bellek seçin.")
            return

        reply = QMessageBox.question(self, "SON UYARI", 
                                     f"Hedef: {usb_dev}\n\nBu aygıttaki TÜM VERİLER SİLİNECEK.\nDD modu kullanılacaktır.\nDevam etmek istiyor musunuz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Butonları devre dışı bırak
            self.btn_yaz.setEnabled(False)
            self.btn_iso.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.console_log.clear()
            
            # Yazdırma iş parçacığını başlat
            self.worker = YazdirmaWorker(iso, usb_dev)
            self.worker.ilerleme_sinyali.connect(self.append_log)
            self.worker.tamamlandi_sinyali.connect(self.yazdirma_bitti)
            self.worker.start()
            
    def yazdirma_bitti(self, success, message):
        # Butonları tekrar etkinleştir
        self.btn_yaz.setEnabled(True)
        self.btn_iso.setEnabled(True)
        self.btn_refresh.setEnabled(True)

        if success:
            QMessageBox.information(self, "Başarılı", message)
            self.append_log(f"*** BİTTİ: {message} ***")
        else:
            QMessageBox.critical(self, "Hata", message)
            self.append_log(f"*** HATA: {message} ***")
            
        self.worker = None # İş parçacığını temizle