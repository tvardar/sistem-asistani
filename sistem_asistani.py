# Sistem Asistanı
# Copyright (C) 2025 [Tarık VARDAR]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# sistem_asistani.py

import sys
import os
import traceback
import platform
from datetime import datetime

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    pass
# ------------------------------------------------

def hata_raporu_yaz(exctype, value, tb):
    """
    Hata oluştuğunda Masaüstüne detaylı log dosyası oluşturur.
    """
    try:
        # 1. Hata Metnini Hazırla
        hata_zamani = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hata_detayi = "".join(traceback.format_exception(exctype, value, tb))
        sistem_bilgisi = f"{platform.system()} {platform.release()} ({platform.machine()})"
        
        rapor = (
            f"\n{'='*50}\n"
            f"SİSTEM ASİSTANI - HATA RAPORU\n"
            f"Zaman: {hata_zamani}\n"
            f"Sistem: {sistem_bilgisi}\n"
            f"{'-'*50}\n"
            f"{hata_detayi}"
            f"{'='*50}\n"
        )

        # 2. Masaüstü Yolunu Bul (Türkçe/İngilizce uyumlu)
        home = os.path.expanduser("~")
        desktop = os.path.join(home, "Masaüstü")
        if not os.path.exists(desktop):
            desktop = os.path.join(home, "Desktop")
            if not os.path.exists(desktop):
                desktop = home # Masaüstü bulunamazsa Ev dizinine yaz

        dosya_yolu = os.path.join(desktop, "Sistem-Asistani-Hata.txt")

        # 3. Dosyaya Yaz (Append modu - üstüne ekler)
        with open(dosya_yolu, "a", encoding="utf-8") as f:
            f.write(rapor)
        
        print(f"HATA OLUŞTU! Rapor kaydedildi: {dosya_yolu}")
        
    except Exception as e:
        print(f"Hata raporu yazılırken bile hata oluştu: {e}")

# Beklenmeyen hataları yakalamak için kancayı (hook) ayarla
sys.excepthook = hata_raporu_yaz

def bagimliliklari_ayarla():
    """
    Eğer 'bagimliliklar' klasörü varsa, onu Python'un arama yoluna ekler.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    deps_dir = os.path.join(base_dir, "bagimliliklar")
    
    if os.path.exists(deps_dir):
        if deps_dir not in sys.path:
            sys.path.insert(0, deps_dir)

def uygulamayi_baslat():
    # WebEngine ayarları
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --disable-logging --ignore-certificate-errors"
    
    try:
        # 1. Bağımlılık yolunu ayarla
        bagimliliklari_ayarla()

        # 2. Modülleri çağır
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtNetwork import QLocalSocket
        from PyQt6.QtGui import QFont

        # Uygulama örneğini oluştur
        app = QApplication(sys.argv)
        app.setApplicationName("Sistem Asistanı")
        
        # Tekil çalışma kontrolü (Socket)
        socket_name = "SistemAsistaniInstance"
        socket = QLocalSocket()
        socket.connectToServer(socket_name)

        if socket.waitForConnected(500):
            print("Program zaten çalışıyor. Mevcut pencere öne getiriliyor...")
            socket.write(b"SHOW")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            sys.exit(0)
        
        # Ana pencereyi yükle
        from ana_pencere import AnaPencere

        font = QFont("Sans Serif", 10)
        app.setFont(font)

        p = AnaPencere(socket_name=socket_name)
        p.show()

        sys.exit(app.exec())

    except Exception as e:
        # Ana döngü başlamadan çökme olursa burası yakalar
        exc_type, exc_value, exc_traceback = sys.exc_info()
        hata_raporu_yaz(exc_type, exc_value, exc_traceback)
        sys.exit(1)

if __name__ == '__main__':
    uygulamayi_baslat()
