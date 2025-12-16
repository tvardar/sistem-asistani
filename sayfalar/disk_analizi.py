# sayfalar/disk_analizi.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QProgressBar, QFileDialog, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import os

class TaramaWorker(QThread):
    progres_sinyal = pyqtSignal(int)
    sonuc_sinyal = pyqtSignal(dict)
    
    def __init__(self, yol):
        super().__init__()
        self.yol = yol
    
    def get_size(self, start_path):
        total_size = 0
        file_list = []
        try:
            with os.scandir(start_path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat().st_size
                            total_size += size
                            file_list.append({"ad": entry.name, "boyut": size, "tip": "dosya"})
                        elif entry.is_dir(follow_symlinks=False):
                            size, sub_files = self.get_size(entry.path)
                            total_size += size
                            file_list.append({"ad": entry.name, "boyut": size, "tip": "klasor", "icerik": sub_files})
                    except: pass
        except: pass
        return total_size, file_list

    def run(self):
        try:
            self.progres_sinyal.emit(10)
            boyut, agac = self.get_size(self.yol)
            self.progres_sinyal.emit(100)
            self.sonuc_sinyal.emit({"kok": self.yol, "boyut": boyut, "icerik": agac})
        except Exception as e:
            print(e)

class DiskAnaliziSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.disk_analiz_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Disk Alanı Analizcisi", icon))

        h_top = QHBoxLayout()
        self.btn_sec = QPushButton("📂 Klasör Seç ve Analiz Et")
        self.btn_sec.clicked.connect(self.klasor_sec)
        self.btn_sec.setMinimumHeight(40)
        h_top.addWidget(self.btn_sec)
        layout.addLayout(h_top)

        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ad", "Boyut", "Kullanım %"])
        self.tree.setColumnWidth(0, 400)
        layout.addWidget(self.tree)

    def klasor_sec(self):
        yol = QFileDialog.getExistingDirectory(self, "Analiz Edilecek Klasörü Seç")
        if yol:
            self.tree.clear()
            self.progress.setValue(0)
            self.progress.show()
            self.btn_sec.setEnabled(False)
            self.worker = TaramaWorker(yol)
            self.worker.progres_sinyal.connect(self.progress.setValue)
            self.worker.sonuc_sinyal.connect(self.sonuc_goster)
            self.worker.start()

    def human_readable(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024: return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def sonuc_goster(self, data):
        self.progress.hide()
        self.btn_sec.setEnabled(True)
        kok_size = data["boyut"]
        if kok_size == 0: kok_size = 1 # Div zero fix
        
        top = QTreeWidgetItem(self.tree)
        top.setText(0, data["kok"])
        top.setText(1, self.human_readable(kok_size))
        top.setText(2, "100%")
        
        # İçeriği boyuta göre sırala
        sorted_content = sorted(data["icerik"], key=lambda x: x["boyut"], reverse=True)
        self.ekle_recursive(top, sorted_content, kok_size)
        top.setExpanded(True)

    def ekle_recursive(self, parent_item, liste, total_ref):
        for item in liste:
            node = QTreeWidgetItem(parent_item)
            node.setText(0, ("📁 " if item["tip"] == "klasor" else "📄 ") + item["ad"])
            node.setText(1, self.human_readable(item["boyut"]))
            
            yuzde = (item["boyut"] / total_ref) * 100
            bar = QProgressBar()
            bar.setValue(int(yuzde))
            bar.setTextVisible(True)
            bar.setFormat(f"%{yuzde:.1f}")
            bar.setStyleSheet(f"""
                QProgressBar {{ border:none; background:transparent; }} 
                QProgressBar::chunk {{ background-color: {'#e74c3c' if yuzde > 50 else '#2ecc71'}; border-radius: 2px; }}
            """)
            bar.setFixedHeight(15)
            self.tree.setItemWidget(node, 2, bar)

            if item["tip"] == "klasor" and "icerik" in item:
                # Sadece büyük dosyaları göster (Performans için)
                sorted_sub = sorted(item["icerik"], key=lambda x: x["boyut"], reverse=True)
                self.ekle_recursive(node, sorted_sub[:10], total_ref) # İlk 10 büyük