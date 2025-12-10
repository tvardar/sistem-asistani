# sayfalar/hud_penceresi.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QApplication)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from gorsel_araclar import SvgIkonOlusturucu, AyarlarYoneticisi
import os

class HUDPenceresi(QWidget):
    def __init__(self, ana_pencere):
        super().__init__()
        self.ana_pencere = ana_pencere
        self.ayarlar_yoneticisi = AyarlarYoneticisi()
        self.tema_ayarla()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # DEĞİŞİKLİK 1: Sabit yükseklik kaldırıldı, sadece genişlik sabit.
        self.setFixedWidth(300) 
        
        self.old_pos = None

        try:
            screen = QApplication.primaryScreen().availableGeometry()
            x = screen.width() - self.width() - 20
            y = screen.top() + 50
            self.move(x, y)
        except:
            self.move(100, 100)

        layout = QVBoxLayout(self)
        
        # DEĞİŞİKLİK 2: Pencereyi içeriğe göre otomatik boyutlandırır.
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. BAŞLIK VE LOGO
        header_layout = QHBoxLayout()
        
        # Logo
        self.lbl_logo = QLabel()
        self.update_logo() # Logoyu temaya göre yükle
        header_layout.addWidget(self.lbl_logo)
        
        # Başlık
        self.lbl_title = QLabel("SİSTEM ASİSTANI")
        self.lbl_title.setStyleSheet("color: #33AADD; font-weight: bold; font-size: 11pt;")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        lbl_info = QLabel("Çıkış: Çift Tıkla")
        lbl_info.setStyleSheet(f"color: {self.c_subtext}; font-size: 8pt;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(lbl_info)
        layout.addSpacing(10)

        # 2. EKSTRA BİLGİLER (SICAKLIK & DNS)
        info_layout = QHBoxLayout()
        
        # Sıcaklık
        self.lbl_temp = QLabel("Temp: --°C")
        self.lbl_temp.setStyleSheet(f"color: {self.c_text}; font-weight: bold;")
        info_layout.addWidget(self.lbl_temp)
        
        info_layout.addStretch()
        
        # DNS
        self.lbl_dns = QLabel("DNS: ...")
        self.lbl_dns.setStyleSheet(f"color: {self.c_text}; font-size: 9pt;")
        self.lbl_dns.setToolTip("Aktif DNS Sunucusu")
        info_layout.addWidget(self.lbl_dns)
        
        layout.addLayout(info_layout)
        layout.addSpacing(10)

        # 3. DONANIM BARLARI
        self.cpu_bar = self._bar_olustur("CPU", SvgIkonOlusturucu.process_ikonu)
        self.ram_bar = self._bar_olustur("RAM", SvgIkonOlusturucu.ram_ikonu)
        self.disk_bar = self._bar_olustur("Disk", SvgIkonOlusturucu.hardware_ikonu)
        
        layout.addLayout(self.cpu_bar[0])
        layout.addLayout(self.ram_bar[0])
        layout.addLayout(self.disk_bar[0])
        
        layout.addSpacing(15)

        # 4. AĞ TRAFİĞİ
        lbl_net_baslik = QLabel("AĞ TRAFİĞİ")
        lbl_net_baslik.setStyleSheet(f"color: {self.c_subtext}; font-size: 9pt; font-weight:bold; letter-spacing: 1px;")
        lbl_net_baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_net_baslik)

        net_layout = QHBoxLayout()
        self.lbl_dl = QLabel("▼ 0 MB")
        self.lbl_dl.setStyleSheet("color: #2ecc71; font-size: 11pt; font-weight: bold;")
        self.lbl_dl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_ul = QLabel("▲ 0 MB")
        self.lbl_ul.setStyleSheet("color: #e67e22; font-size: 11pt; font-weight: bold;")
        self.lbl_ul.setAlignment(Qt.AlignmentFlag.AlignCenter)

        net_layout.addWidget(self.lbl_dl)
        net_layout.addWidget(self.lbl_ul)
        layout.addLayout(net_layout)

        # DEĞİŞİKLİK 3: En alttaki addStretch() kaldırıldı.
        # layout.addStretch()  <- SİLİNDİ

    def tema_ayarla(self):
        secim = self.ayarlar_yoneticisi.ayarlar.get("tema", "Otomatik")
        if secim == "Otomatik":
            secim = AyarlarYoneticisi.sistem_temasini_algila()

        self.current_theme = secim # Temayı sakla (logo için)

        if secim == "Açık":
            self.c_bg_rgba = QColor(245, 247, 250, 230)
            self.c_text = "#2C3E50"
            self.c_subtext = "#7F8C8D"
            self.c_bar_bg = "#D0D0D0"
            self.c_icon = "#555555"
        else:
            self.c_bg_rgba = QColor(20, 20, 20, 180)
            self.c_text = "#E0E0E0"
            self.c_subtext = "#AAAAAA"
            self.c_bar_bg = "#333333"
            self.c_icon = "#AAAAAA"

    def update_logo(self):
        # Logo yolunu ana pencereden al (Ana pencere başlatıldıysa)
        try:
            if self.current_theme == "Açık":
                icon_path = self.ana_pencere.icon_path_dark
            else:
                icon_path = self.ana_pencere.icon_path_light
            
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo.setPixmap(pixmap)
        except:
            pass

    def _bar_olustur(self, baslik, ikon_func):
        l = QVBoxLayout()
        hl = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(ikon_func(self.c_icon, 18))
        lbl = QLabel(baslik)
        lbl.setStyleSheet(f"color: {self.c_text}; font-weight: 500;")
        val = QLabel("0%")
        val.setStyleSheet("color: #33AADD; font-weight:bold;")
        hl.addWidget(icon)
        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(val)
        bar = QProgressBar()
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"QProgressBar {{ background: {self.c_bar_bg}; border: none; border-radius: 3px; }} QProgressBar::chunk {{ background: #33AADD; border-radius: 3px; }}")
        bar.setTextVisible(False)
        l.addLayout(hl)
        l.addWidget(bar)
        return l, bar, val

    def guncelle(self, veri):
        cpu = veri.get("toplam_cpu_yuzde", 0)
        self.cpu_bar[1].setValue(int(cpu))
        self.cpu_bar[2].setText(f"%{cpu:.0f}")
        
        ram = veri.get("ram_yuzde", 0)
        self.ram_bar[1].setValue(int(ram))
        self.ram_bar[2].setText(f"%{ram:.0f}")
        
        disk_yuzde = 0
        for d in veri.get("disk_bolumleri", []):
            if d["baglanti_noktasi"] == "/":
                disk_yuzde = d["yuzde"]
                break
        self.disk_bar[1].setValue(int(disk_yuzde))
        self.disk_bar[2].setText(f"%{disk_yuzde:.0f}")

        dl_text = veri.get("ag_alinan", "0 MB")
        ul_text = veri.get("ag_gonderilen", "0 MB")
        self.lbl_dl.setText(f"▼ {dl_text}")
        self.lbl_ul.setText(f"▲ {ul_text}")
        
        # YENİ BİLGİLER
        temp = veri.get("cpu_sicaklik", 0)
        self.lbl_temp.setText(f"{temp:.0f}°C")
        
        dns = veri.get("dns_bilgi", "")
        # DNS çok uzunsa ilkini göster
        if "," in dns: dns = dns.split(",")[0]
        if not dns: dns = "Oto"
        self.lbl_dns.setText(f"DNS: {dns}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#33AADD"), 2))
        painter.setBrush(self.c_bg_rgba)
        painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 15, 15)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event): self.old_pos = None
    def mouseDoubleClickEvent(self, event):
        self.close()
        if self.ana_pencere: self.ana_pencere.showNormal()