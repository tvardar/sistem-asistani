# sayfalar/temizlik.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, 
                             QCheckBox, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import os
import shutil

class TaramaWorker(QThread):
    sonuc_sinyali = pyqtSignal(list) # [ (Ad, Boyut_Str, Yol, Komut/Tip) ]

    def get_dir_size(self, path):
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file(): total += entry.stat().st_size
                elif entry.is_dir(): total += self.get_dir_size(entry.path)
        except: pass
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
            apt_size = int(subprocess.check_output("du -sb /var/cache/apt/archives 2>/dev/null | cut -f1", shell=True).strip())
            if apt_size > 10240:
                items.append(("APT Paket Önbelleği", self.size_fmt(apt_size), "/var/cache/apt/archives", "apt"))
        except: pass

        # 2. Thumbnail Cache
        thumb_path = os.path.expanduser("~/.cache/thumbnails")
        if os.path.exists(thumb_path):
            s = self.get_dir_size(thumb_path)
            if s > 0: items.append(("Küçük Resim (Thumbnail) Önbelleği", self.size_fmt(s), thumb_path, "delete_user"))

        # 3. Tarayıcılar
        cache_root = os.path.expanduser("~/.cache")
        targets = ["mozilla", "google-chrome", "chromium", "vlc", "pip"]
        browser_size = 0
        for t in targets:
            p = os.path.join(cache_root, t)
            if os.path.exists(p): browser_size += self.get_dir_size(p)
        
        if browser_size > 0:
            items.append(("Tarayıcı ve Uygulama Önbellekleri", self.size_fmt(browser_size), "mozilla/chrome/vlc", "browser_cache"))

        # 4. Journald
        try:
            out = subprocess.check_output("journalctl --disk-usage", shell=True, text=True)
            if "take up" in out:
                size_str = out.split("take up")[1].split("in")[0].strip()
                items.append(("Eski Sistem Günlükleri (Journald)", size_str, "/var/log/journal", "journal"))
        except: pass
        
        # 5. Çöp Kutusu (DÜZELTİLDİ: files + info)
        trash_root = os.path.expanduser("~/.local/share/Trash")
        trash_files = os.path.join(trash_root, "files")
        trash_info = os.path.join(trash_root, "info")
        
        total_trash = 0
        if os.path.exists(trash_files): total_trash += self.get_dir_size(trash_files)
        if os.path.exists(trash_info): total_trash += self.get_dir_size(trash_info)
            
        if total_trash > 0:
            items.append(("Çöp Kutusu", self.size_fmt(total_trash), trash_root, "trash"))

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
        layout.addWidget(self.list_widget)

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
        self.lbl_total.setText("Taranıyor...")
        self.btn_temizle.setEnabled(False)
        self.btn_tara.setEnabled(False)
        
        self.worker = TaramaWorker()
        self.worker.sonuc_sinyali.connect(self.tarama_bitti)
        self.worker.start()

    def tarama_bitti(self, items):
        self.items_data = items
        self.btn_tara.setEnabled(True)
        
        if not items:
            self.lbl_total.setText("Sistem Temiz!")
            return

        self.btn_temizle.setEnabled(True)
        
        for ad, boyut, yol, tip in items:
            item = QListWidgetItem()
            widget = QWidget()
            h = QHBoxLayout(widget); h.setContentsMargins(5, 5, 5, 5)
            
            chk = QCheckBox(ad)
            chk.setChecked(True)
            chk.setStyleSheet("font-weight: bold;")
            
            lbl_desc = QLabel(f"{yol}")
            lbl_desc.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
            
            lbl_size = QLabel(boyut)
            lbl_size.setStyleSheet("color: #33AADD; font-weight: bold;")
            
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

        self.lbl_total.setText("Seçim Yapınız")

    def temizle(self):
        komutlar = []
        user_paths = []
        trash_mode = False
        
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            chk = widget.findChild(QCheckBox)
            
            if chk.isChecked():
                tip = chk.property("data_type")
                yol = chk.property("data_path")
                
                if tip == "apt": komutlar.append("apt-get clean")
                elif tip == "journal": komutlar.append("journalctl --vacuum-time=1s")
                elif tip == "delete_user": user_paths.append(yol)
                elif tip == "browser_cache":
                    targets = ["mozilla", "google-chrome", "chromium", "vlc", "pip", "thumbnails"]
                    base = os.path.expanduser("~/.cache")
                    for t in targets:
                        p = os.path.join(base, t)
                        if os.path.exists(p): user_paths.append(p)
                elif tip == "trash":
                    trash_mode = True

        if not komutlar and not user_paths and not trash_mode: return

        reply = QMessageBox.question(self, "Onay", "Seçili dosyalar kalıcı olarak silinecek. Devam edilsin mi?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        # 1. Çöp Kutusu (Özel İşlem)
        if trash_mode:
            trash_root = os.path.expanduser("~/.local/share/Trash")
            # İçindeki dosyaları sil, klasörü değil
            for sub in ["files", "info"]:
                target = os.path.join(trash_root, sub)
                if os.path.exists(target):
                    for filename in os.listdir(target):
                        file_path = os.path.join(target, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
                            elif os.path.isdir(file_path): shutil.rmtree(file_path)
                        except Exception as e: print(e)

        # 2. Kullanıcı Klasörleri
        for p in user_paths:
            try:
                if os.path.isfile(p): os.remove(p)
                elif os.path.isdir(p): shutil.rmtree(p)
            except: pass

        # 3. Sistem (Root)
        if komutlar:
            full_cmd = " && ".join(komutlar)
            try: subprocess.run(["pkexec", "sh", "-c", full_cmd], check=True)
            except: QMessageBox.warning(self, "Hata", "Sistem temizliği sırasında yetki hatası.")

        QMessageBox.information(self, "Tamamlandı", "Temizlik işlemi tamamlandı.")
        self.taramayi_baslat()