# ana_pencere.py

import sys
import os
import subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

# --- MODÜLLER ---
from sayfalar.genel_bakis import GenelBakisSayfasi
from sayfalar.donanim import DonanimSayfasi
from sayfalar.surec_yonetimi import SurecYonetimiSayfasi
from sayfalar.ag_araclari import AgAraclariSayfasi
from sayfalar.yonetim import YonetimSayfasi
from sayfalar.bakim import BakimSayfasi
from sayfalar.hakkinda import HakkindaSayfasi
from sayfalar.hud_penceresi import HUDPenceresi
from sayfalar.disk_analizi import DiskAnaliziSayfasi
from sayfalar.usb_yazdir import UsbYazdirSayfasi
from sayfalar.acilis_analizi import AcilisAnaliziSayfasi
from sayfalar.sistem_gunlugu import SistemGunluguSayfasi
from sayfalar.disk_sagligi import DiskSagligiSayfasi
from sayfalar.ozel_komutlar import OzelKomutlarSayfasi
from sayfalar.port_yoneticisi import PortYoneticisiSayfasi
from sayfalar.site_engelleyici import SiteEngelleyiciSayfasi
from sayfalar.cron_yoneticisi import CronYoneticisiSayfasi
from sayfalar.ayarlar import AyarlarSayfasi
from sayfalar.temizlik import TemizlikSayfasi
from sayfalar.wifi_analiz import WifiAnalizSayfasi

from gorsel_araclar import BilgiIsleyicisi, SvgIkonOlusturucu, AyarlarYoneticisi
from stil_sayfasi import get_stil

class AnaPencere(QMainWindow):
    def __init__(self, socket_name="SistemAsistaniInstance"):
        super().__init__()
        self.setWindowTitle("Sistem Asistanı")
        
        # *** GÜNCELLENEN BOYUTLAR ***
        self.resize(1100, 780) # Varsayılan boyutu biraz küçülttük
        self.setMinimumSize(950, 680) # Minimum boyutu 700'e yakın bir değere indirdik.
        # ****************************
        
        self.ayarlar = AyarlarYoneticisi()
        
        # --- SÜRÜM SABİTLENDİ ---
        self.SURUM = "v1.1"

        # --- İKON YOLU (DÜZELTİLDİ) ---
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.icons_dir = os.path.join(self.base_dir, "icons")
        self.icon_path_light = os.path.join(self.icons_dir, "sistem-asistani.png")      
        self.icon_path_dark = os.path.join(self.icons_dir, "sistem-asistani-dark.png") 

        # İkonu Yükle
        if os.path.exists(self.icon_path_light):
            self.app_icon = QIcon(self.icon_path_light)
        else:
            self.app_icon = QIcon("icons/sistem-asistani.png")

        self.setWindowIcon(self.app_icon)
        QApplication.setWindowIcon(self.app_icon)

        self.socket_name = socket_name
        self.server = QLocalServer()
        try:
            if sys.platform != "win32":
                if os.path.exists(f"/tmp/{self.socket_name}") or os.path.exists(self.socket_name): QLocalServer.removeServer(self.socket_name)
        except: pass
        self.server.listen(self.socket_name)
        self.server.newConnection.connect(self.yeni_baglanti_geldi)

        self.hud_window = None
        self.logo_label = QLabel() 
        self.arayuzu_kur()
        self.tray_kur() 
        self.backend_baslat()
        self.tema_uygula()
        self.ekran_ortala()

    def ekran_ortala(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def yeni_baglanti_geldi(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.pencereyi_one_getir(socket))

    def pencereyi_one_getir(self, socket):
        """Çalışan uygulamaya tıklandığında pencereyi öne getirir."""
        # Socket'ten gelen SHOW komutunu oku (okunması gerekiyor)
        _ = socket.readAll() 
        
        # HUD modu açıksa kapat
        if self.hud_window and self.hud_window.isVisible(): 
            self.hud_window.close() 
            
        # Ana pencereyi normal boyutta göster (küçültülmüşse normalleştirir)
        self.showNormal() 
        
        # Pencereyi ekranın ortasına getir
        self.ekran_ortala() 
        
        # Pencereyi aktif hale getir (Odakla)
        self.activateWindow() 
        
        # Pencereyi diğerlerinin üstüne çıkar (Linux'ta bazen activateWindow yetmez)
        self.raise_() 

    def tema_uygula(self):
        self.ayarlar.ayarlar = self.ayarlar.yukle()
        secim = self.ayarlar.ayarlar.get("tema", "Otomatik")
        renk = self.ayarlar.ayarlar.get("renk", "#33AADD")
        tema = AyarlarYoneticisi.sistem_temasini_algila() if secim == "Otomatik" else secim
        
        self.setStyleSheet(get_stil(tema, renk))
        
        if tema == "Açık":
            target_icon = self.icon_path_dark if os.path.exists(self.icon_path_dark) else self.icon_path_light
        else:
            target_icon = self.icon_path_light
            
        if os.path.exists(target_icon):
            pixmap = QPixmap(target_icon).scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
             self.logo_label.setText("SİSTEM\nASİSTANI")
             self.logo_label.setStyleSheet(f"color: {renk}; font-weight: bold; font-size: 16pt;")

    def arayuzu_kur(self):
        ana_widget = QWidget()
        self.setCentralWidget(ana_widget)
        main_layout = QHBoxLayout(ana_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setObjectName("YanMenuScroll")
        self.menu_scroll.setFixedWidth(280)
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.menu_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.menu_panel = QWidget()
        self.menu_panel.setObjectName("YanMenu")
        menu_layout = QVBoxLayout(self.menu_panel)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(5)

        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background:transparent; border:none; margin-bottom:10px;")
        menu_layout.addWidget(self.logo_label)
        
        t = QLabel("Araçlar & Modüller")
        t.setObjectName("UygulamaBaslik")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size: 12pt; color: #AAAAAA; font-weight:bold; letter-spacing: 1px;")
        menu_layout.addWidget(t)
        menu_layout.addSpacing(10)

        self.stack = QStackedWidget()
        
        self.pages = [
            ("Genel Bakış", SvgIkonOlusturucu.dashboard_ikonu, GenelBakisSayfasi(parent=self)),
            ("Donanım & Güç", SvgIkonOlusturucu.hardware_ikonu, DonanimSayfasi()),
            ("Süreç Yönetimi", SvgIkonOlusturucu.process_ikonu, SurecYonetimiSayfasi()),
            ("Port Yöneticisi", SvgIkonOlusturucu.port_ikonu, PortYoneticisiSayfasi()), 
            ("Ağ & DNS", SvgIkonOlusturucu.network_ikonu, AgAraclariSayfasi()),
            ("Wi-Fi Analizörü", SvgIkonOlusturucu.network_ikonu, WifiAnalizSayfasi()), 
            ("Site Engelleyici", SvgIkonOlusturucu.block_ikonu, SiteEngelleyiciSayfasi()), 
            ("Zamanlanmış Görevler", SvgIkonOlusturucu.cron_ikonu, CronYoneticisiSayfasi()),
            ("Disk Analizi", SvgIkonOlusturucu.disk_analiz_ikonu, DiskAnaliziSayfasi()),
            ("Disk Sağlığı", SvgIkonOlusturucu.health_ikonu, DiskSagligiSayfasi()),
            ("Sistem Temizliği", SvgIkonOlusturucu.clean_ikonu, TemizlikSayfasi()),
            ("Açılış Analizi", SvgIkonOlusturucu.boot_ikonu, AcilisAnaliziSayfasi()),
            ("Sistem Günlüğü", SvgIkonOlusturucu.log_ikonu, SistemGunluguSayfasi()),
            ("Özel Komutlar", SvgIkonOlusturucu.script_ikonu, OzelKomutlarSayfasi()),
            ("USB Yazdırıcı", SvgIkonOlusturucu.usb_ikonu, UsbYazdirSayfasi()),
            ("Sistem Yönetimi", SvgIkonOlusturucu.anahtar_ikonu, YonetimSayfasi(parent=self)),
            ("Bakım & Onarım", SvgIkonOlusturucu.maintenance_ikonu, BakimSayfasi()),
            ("Ayarlar", SvgIkonOlusturucu.ayarlar_ikonu, AyarlarSayfasi(parent=self)),
            ("Hakkında", SvgIkonOlusturucu.info_ikonu, HakkindaSayfasi(self.SURUM, self.icon_path_light))
        ]

        self.menu_buttons = []

        for i, (ad, ikon_func, w) in enumerate(self.pages):
            b = QPushButton(ad)
            b.setObjectName("MenuDugmesi")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setIcon(QIcon(ikon_func("#AAAAAA", 24)))
            b.setIconSize(QSize(22, 22))
            
            if i == 0: b.setChecked(True)
            b.clicked.connect(lambda checked, idx=i: self.sayfa_degistir(idx))
            menu_layout.addWidget(b)
            self.stack.addWidget(w)
            self.menu_buttons.append(b)

        menu_layout.addStretch()
        self.menu_scroll.setWidget(self.menu_panel)
        main_layout.addWidget(self.menu_scroll)
        main_layout.addWidget(self.stack)
    
    def hud_moduna_gec(self):
        self.hide()
        if not self.hud_window: self.hud_window = HUDPenceresi(self)
        self.hud_window.show()

    def backend_baslat(self):
        self.thread = BilgiIsleyicisi()
        self.thread.bilgi_guncelle_sinyal.connect(self.veri_dagitici)
        self.thread.bildirim_sinyali.connect(self.bildirim_goster)
        self.thread.disk_degisti_sinyali.connect(self.disk_degisimi_algilandi)
        self.thread.start()

    def disk_degisimi_algilandi(self):
        self.bildirim_goster("Donanım Algılandı", "Disk birimleri değişti, listeler güncelleniyor.")
        for _, _, widget in self.pages:
            if isinstance(widget, UsbYazdirSayfasi): widget.diskleri_getir()
            elif isinstance(widget, DiskSagligiSayfasi): widget.diskleri_bul()
            elif isinstance(widget, DonanimSayfasi): widget.donanim_tara()

    def bildirim_goster(self, baslik, mesaj):
        if hasattr(self, 'tray') and self.tray.isVisible(): self.tray.showMessage(baslik, mesaj, QSystemTrayIcon.MessageIcon.Information, 5000)

    def veri_dagitici(self, veri):
        if self.hud_window and self.hud_window.isVisible(): self.hud_window.guncelle(veri)
        elif self.isVisible():
            cw = self.stack.currentWidget()
            if hasattr(cw, 'guncelle'):
                try: cw.guncelle(veri)
                except: pass

    # --- TRAY (TEPSİ) KURULUMU DÜZELTİLDİ ---
    def tray_kur(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self)
            
            # İkonu kesinleştir
            if not self.app_icon.isNull(): 
                self.tray.setIcon(self.app_icon)
            else:
                # Fallback: Eğer ikon dosyası yoksa sistem ikonunu kullan
                self.tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
                
            menu = QMenu()
            show_act = QAction("Göster", self)
            show_act.triggered.connect(self.showNormal)
            quit_act = QAction("Çıkış", self)
            quit_act.triggered.connect(self.uygulamayi_kapat)
            
            menu.addAction(show_act)
            menu.addAction(quit_act)
            self.tray.setContextMenu(menu)
            self.tray.show()
            self.tray.setToolTip(f"Sistem Asistanı {self.SURUM}")
            self.tray.activated.connect(self.tray_tiklandi)
        else:
            print("Hata: Sistem tepsisi kullanılamıyor.")

    def tray_tiklandi(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: self.showNormal(); self.activateWindow()

    def closeEvent(self, event):
        if hasattr(self, 'tray') and self.tray.isVisible():
            self.hide()
            if not self.ayarlar.ayarlar.get("tray_bilgisi_verildi"):
                self.tray.showMessage("Sistem Asistanı", "Uygulama tepsiye küçültüldü.", QSystemTrayIcon.MessageIcon.Information, 2000)
                self.ayarlar.kaydet("tray_bilgisi_verildi", True)
            event.ignore()
        else: self.uygulamayi_kapat()

    def uygulamayi_kapat(self):
        if hasattr(self, 'thread') and self.thread.isRunning(): self.thread.requestInterruption(); self.thread.quit(); self.thread.wait(2000)
        self.server.close(); QLocalServer.removeServer(self.socket_name); QApplication.instance().quit()

    def sayfa_degistir(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            if i != index: btn.setChecked(False)
            else: btn.setChecked(True)