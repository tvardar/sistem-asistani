# sayfalar/temizlik.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QCheckBox, QMessageBox, QProgressBar, QTextEdit) # QTextEdit eklendi
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import os
import shutil
import re 
import time # Loglama için zaman gecikmesi ekleyebiliriz

# TaramaWorker sınıfı değişmiyor. (Yukarıdaki son haliyle aynı kalabilir.)
class TaramaWorker(QThread):
    sonuc_sinyali = pyqtSignal(list) 
    # ... (get_dir_size, size_fmt ve run metotları aynı kalıyor)
    def get_dir_size(self, path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
        except Exception: 
            pass
        return total

    def size_fmt(self, num):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(num) < 1024.0: return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"

    def run(self):
        items = []
        
        # 1. Apt Cache (Paket Önbelleği)
        try:
            output = subprocess.check_output("du -sb /var/cache/apt/archives 2>/dev/null", shell=True).strip().split()[0].decode()
            apt_size = int(output)
            if apt_size > 10240:
                items.append(("APT Paket Önbelleği", self.size_fmt(apt_size), "/var/cache/apt/archives", "apt"))
        except: pass

        # 2. Thumbnail Cache (~/.cache/thumbnails)
        thumb_path = os.path.expanduser("~/.cache/thumbnails")
        s = self.get_dir_size(thumb_path)
        if s > 0: 
            items.append(("Küçük Resim (Thumbnail) Önbelleği", self.size_fmt(s), thumb_path, "delete_user"))
        else:
            items.append(("Küçük Resim (Thumbnail) Önbelleği", self.size_fmt(0), thumb_path, "delete_user_empty")) # Boş da olsa göster

        # 3. Tarayıcı ve Uygulama Önbellekleri (~/.cache/mozilla, ~/.cache/google-chrome vb.)
        cache_root = os.path.expanduser("~/.cache")
        targets = ["mozilla", "google-chrome", "chromium", "vlc", "pip", "flatpak"]
        browser_paths = []
        browser_size = 0
        
        for t in targets:
            p = os.path.join(cache_root, t)
            if os.path.exists(p) and os.path.isdir(p):
                size = self.get_dir_size(p)
                if size > 0:
                    browser_size += size
                    browser_paths.append(p) 
        
        path_str = "|".join(browser_paths) 
        display_path = ", ".join(t for t in targets if os.path.join(cache_root, t) in browser_paths)

        if browser_size > 0:
            items.append(("Tarayıcı ve Uygulama Önbellekleri", self.size_fmt(browser_size), path_str, "browser_cache"))
        else:
            items.append(("Tarayıcı ve Uygulama Önbellekleri", self.size_fmt(0), path_str, "browser_cache_empty")) # Boş da olsa göster


        # 4. Journald (Eski Sistem Günlükleri)
        try:
            out = subprocess.check_output("journalctl --disk-usage 2>/dev/null", shell=True, text=True)
            match = re.search(r"take up\s+([\d\.]+)\s*([KMGT]B)", out, re.IGNORECASE)
            if match:
                size_str = match.group(1) + " " + match.group(2)
                items.append(("Eski Sistem Günlükleri (Journald)", size_str.strip(), "/var/log/journal", "journal"))
            else:
                 items.append(("Eski Sistem Günlükleri (Journald)", self.size_fmt(0), "/var/log/journal", "journal_empty"))
        except: pass
        
        # 5. Çöp Kutusu (Kullanıcı Çöpü)
        trash_root = os.path.expanduser("~/.local/share/Trash")
        trash_files = os.path.join(trash_root, "files")
        trash_info = os.path.join(trash_root, "info")
        
        total_trash = 0
        if os.path.exists(trash_files): total_trash += self.get_dir_size(trash_files)
        if os.path.exists(trash_info): total_trash += self.get_dir_size(trash_info)
            
        if total_trash > 0:
            items.append(("Çöp Kutusu", self.size_fmt(total_trash), trash_root, "trash"))
        else:
            items.append(("Çöp Kutusu", self.size_fmt(0), trash_root, "trash_empty")) # Boş da olsa göster

        self.sonuc_sinyali.emit(items)


class TemizlikSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.clean_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Sistem Temizliği", icon))

        # Bilgi
        info = QLabel("Sisteminizde yer kaplayan gereksiz dosyaları tarayın ve temizleyin.")
        info.setStyleSheet("color: palette(mid); margin-bottom: 10px;")
        layout.addWidget(info)

        # Liste
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { font-size: 11pt; } QCheckBox { padding: 5px; }")
        # Listeyi sabit bir yükseklikte tutalım
        self.list_widget.setMaximumHeight(250) 
        layout.addWidget(self.list_widget)

        # Log Konsolu
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace; padding: 5px;")
        self.console_log.setPlaceholderText("Temizlik işlemleri burada listelenecektir...")
        self.console_log.setMaximumHeight(150)
        layout.addWidget(self.console_log)


        # Alt Panel
        h_bot = QHBoxLayout()
        self.lbl_total = QLabel("Toplam Kazanç: 0 MB")
        self.lbl_total.setStyleSheet("font-weight: bold; color: #2ecc71; font-size: 12pt;")
        
        self.btn_tara = QPushButton("🔍 Tekrar Tara")
        self.btn_tara.clicked.connect(self.taramayi_baslat)
        
        self.btn_temizle = QPushButton("🧹 Seçilileri Temizle")
        self.btn_temizle.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 8px 20px;")
        self.btn_temizle.clicked.connect(self.temizle)
        self.btn_temizle.setEnabled(False)

        h_bot.addWidget(self.lbl_total)
        h_bot.addStretch()
        h_bot.addWidget(self.btn_tara)
        h_bot.addWidget(self.btn_temizle)
        layout.addLayout(h_bot)

        self.taramayi_baslat()

    def taramayi_baslat(self):
        self.list_widget.clear()
        self.console_log.clear() # Logu da temizle
        self.lbl_total.setText("Taranıyor...")
        self.btn_temizle.setEnabled(False)
        self.btn_tara.setEnabled(False)
        
        # Loga bildirim ekle
        self.append_log("Tarama işlemi başlatılıyor...")
        
        self.worker = TaramaWorker()
        self.worker.sonuc_sinyali.connect(self.tarama_bitti)
        self.worker.start()

    def tarama_bitti(self, items):
        self.items_data = items
        self.btn_tara.setEnabled(True)
        self.append_log("Tarama tamamlandı.")
        
        total_found_size = 0.0
        
        if not items:
            self.lbl_total.setText("Sistem Temiz!")
            return

        self.btn_temizle.setEnabled(True)
        
        for ad, boyut, yol, tip in items:
            item = QListWidgetItem()
            widget = QWidget()
            h = QHBoxLayout(widget); h.setContentsMargins(5, 5, 5, 5)
            
            chk = QCheckBox(ad)
            
            # Boyutu sadece doluysa listede göster, boşsa gri yap
            if "_empty" in tip:
                chk.setChecked(False) # Boş olanları varsayılan olarak seçme
                chk.setStyleSheet("font-weight: normal; color: #7f8c8d;")
                lbl_size = QLabel(boyut)
                lbl_size.setStyleSheet("color: #7f8c8d; font-weight: normal;")
            else:
                chk.setChecked(True)
                chk.setStyleSheet("font-weight: bold;")
                lbl_size = QLabel(boyut)
                lbl_size.setStyleSheet("color: #33AADD; font-weight: bold;")

            # Boyut bilgisini toplayalım (sadece dolu olanları)
            if "_empty" not in tip:
                try:
                    # Basit bir boyut toplama tahmini
                    val = float(boyut.split()[0].replace(',', '.'))
                    unit = boyut.split()[1]
                    if unit == 'KB': total_found_size += val / 1024.0
                    elif unit == 'MB': total_found_size += val
                    elif unit == 'GB': total_found_size += val * 1024.0
                except:
                    pass
            
            # Yolu sadece tarayıcı önbelleği ise kısalt
            if tip.startswith("browser_cache"):
                 lbl_desc = QLabel(f"Önbellek Yolları: {yol.replace('|', ', ')}")
            else:
                 lbl_desc = QLabel(f"{yol}")

            lbl_desc.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
            
            v = QVBoxLayout()
            v.addWidget(chk)
            v.addWidget(lbl_desc)
            
            h.addLayout(v)
            h.addStretch()
            h.addWidget(lbl_size)
            
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            
            chk.setProperty("data_type", tip)
            chk.setProperty("data_path", yol)
            
            # Boş klasörler seçilemez olmalı
            if "_empty" in tip:
                 chk.setEnabled(False) 

        self.lbl_total.setText(f"Tahmini Kazanç: {self.worker.size_fmt(total_found_size * 1024 * 1024)}")


    def append_log(self, message, is_error=False):
        """Konsola log mesajı ekler."""
        color = "#e74c3c" if is_error else "#2ecc71"
        html_message = f'<span style="color:{color}; font-weight:bold;">[{time.strftime("%H:%M:%S")}] </span> {message}<br>'
        self.console_log.insertHtml(html_message)
        self.console_log.verticalScrollBar().setValue(self.console_log.verticalScrollBar().maximum())
        
    def temizle(self):
        komutlar = []
        user_paths_to_delete = [] 
        trash_mode = False
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            chk = widget.findChild(QCheckBox)
            
            # Sadece seçili ve boş olmayan (yani silinecek bir şey olan) öğeleri topla
            if chk.isChecked() and "_empty" not in chk.property("data_type"):
                tip = chk.property("data_type")
                yol = chk.property("data_path")
                
                if tip == "apt": 
                    komutlar.append("apt-get clean")
                    self.append_log("Sistem: APT Paket Önbelleği temizleme komutu eklendi.")
                elif tip == "journal": 
                    komutlar.append("journalctl --vacuum-time=1s") 
                    self.append_log("Sistem: Eski Sistem Günlükleri (Journald) temizleme komutu eklendi.")
                elif tip == "delete_user": 
                    user_paths_to_delete.append(yol)
                    self.append_log(f"Kullanıcı: Küçük Resim Önbelleği ({yol}) silinmek üzere işaretlendi.")
                elif tip == "browser_cache":
                    browser_paths = yol.split("|")
                    user_paths_to_delete.extend(browser_paths)
                    self.append_log(f"Kullanıcı: Tarayıcı/Uygulama Önbellekleri ({len(browser_paths)} klasör) silinmek üzere işaretlendi.")
                elif tip == "trash":
                    trash_mode = True
                    self.append_log("Kullanıcı: Çöp Kutusu içeriği silinmek üzere işaretlendi (Root yetkisi gerekebilir).")


        if not komutlar and not user_paths_to_delete and not trash_mode:
            self.append_log("Temizlenecek seçili öğe bulunamadı.", is_error=True)
            return

        reply = QMessageBox.question(self, "Onay", "Seçili dosyalar kalıcı olarak silinecek. Devam edilsin mi?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        
        clean_success = True
        self.append_log("Temizlik işlemi başlatılıyor...")


        # 1. Çöp Kutusu ve Sistem Komutları (pkexec ile root yetkisi gerektirenler)
        if trash_mode:
            trash_root = os.path.expanduser("~/.local/share/Trash")
            # rm -rf komutu, içindeki dosyaların root yetkisi olsa bile silinmesini sağlar.
            trash_clean_cmd = f"rm -rf {trash_root}/files/* {trash_root}/info/*"
            komutlar.append(trash_clean_cmd)
        
        if komutlar:
            full_cmd = " && ".join(komutlar)
            self.append_log(f"ROOT KOMUTU ÇALIŞTIRILIYOR: {full_cmd}")
            try: 
                # pkexec ile root yetkisi iste
                subprocess.run(["pkexec", "sh", "-c", full_cmd], check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.append_log("Sistem/Çöp Kutusu temizliği başarılı.")
            except Exception as e: 
                QMessageBox.warning(self, "Hata", f"Sistem ve Çöp Kutusu temizliği sırasında yetki/komut hatası.")
                self.append_log(f"HATA: Sistem temizliği başarısız oldu. Yetki hatası olabilir.", is_error=True)
                clean_success = False

        # 2. Normal Kullanıcı Klasörleri (Tarayıcı önbellekleri, vb.)
        if user_paths_to_delete:
            self.append_log(f"{len(user_paths_to_delete)} adet kullanıcı dizini temizleniyor...")
            for p in user_paths_to_delete:
                try:
                    self.append_log(f"  Siliniyor: {p}")
                    if os.path.islink(p) or os.path.isfile(p): 
                        os.unlink(p)
                    elif os.path.isdir(p): 
                        shutil.rmtree(p)
                except Exception as e: 
                    self.append_log(f"HATA: {p} silinemedi: İzin hatası.", is_error=True)
                    clean_success = False
            self.append_log("Kullanıcı dizini temizliği tamamlandı.")


        # Temizlik sonucunu bildir
        if clean_success:
            QMessageBox.information(self, "Tamamlandı", "Temizlik işlemi başarıyla tamamlandı.")
        else:
            QMessageBox.warning(self, "Kısmen Tamamlandı", "Temizlik işlemi tamamlandı, ancak bazı dosyalara ulaşılamadığı için silinemedi (izin hatası olabilir).")
            
        # Temizlik sonrası listeyi güncelle
        self.taramayi_baslat()