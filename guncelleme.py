# guncelleme.py

import requests
import os
import sys
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
import webbrowser

class GuncellemeKontrolcusu(QThread):
    guncelleme_var_sinyali = pyqtSignal(str, str, str) # Sürüm, Açıklama, İndirme Linki
    hata_sinyali = pyqtSignal(str)
    
    def __init__(self, mevcut_surum):
        super().__init__()
        self.mevcut_surum = mevcut_surum
        self.GITHUB_USER = "tvardar"
        self.REPO_NAME = "sistem-asistani"
        self.API_URL = f"https://api.github.com/repos/{self.GITHUB_USER}/{self.REPO_NAME}/releases/latest"

    def run(self):
        try:
            response = requests.get(self.API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").strip()
                download_url = ""
                body = data.get("body", "Yeni özellikler ve hata düzeltmeleri.")

                for asset in data.get("assets", []):
                    if asset["name"].endswith(".deb"):
                        download_url = asset["browser_download_url"]
                        break
                
                if latest_version:
                    # Versiyon Karşılaştırma (DÜZELTİLDİ)
                    try:
                        v_mevcut = int(self.mevcut_surum.lower().replace("v", "").replace(".", ""))
                        v_yeni = int(latest_version.lower().replace("v", "").replace(".", ""))
                    except:
                        v_mevcut = 0
                        v_yeni = 0
                    
                    # Sadece YENİ sürüm ESKİ sürümden büyükse sinyal gönder
                    if v_yeni > v_mevcut:
                        self.guncelleme_var_sinyali.emit(latest_version, body, download_url)
            
        except Exception as e:
            self.hata_sinyali.emit(str(e))

def guncelleme_sor(parent, yeni_surum, notlar, link):
    msg = QMessageBox(parent)
    msg.setWindowTitle("Güncelleme Mevcut")
    msg.setText(f"<b>Yeni Sürüm: {yeni_surum}</b><br><br>Yenilikler:<br>{notlar}")
    msg.setInformativeText("Yeni sürümü indirip kurmak ister misiniz?")
    msg.setIcon(QMessageBox.Icon.Information)
    
    btn_indir = msg.addButton("İndir ve Kur", QMessageBox.ButtonRole.AcceptRole)
    btn_iptal = msg.addButton("Daha Sonra", QMessageBox.ButtonRole.RejectRole)
    
    msg.exec()
    
    if msg.clickedButton() == btn_indir:
        if link:
            dosya_adi = link.split("/")[-1]
            # Kullaniciya islem gosteren terminal komutu
            komut = f"""
            cd /tmp && \
            echo 'İndiriliyor: {dosya_adi}...' && \
            wget -q --show-progress -O {dosya_adi} {link} && \
            echo 'Kuruluyor...' && \
            sudo dpkg -i {dosya_adi} && \
            echo '-----------------------------------------------' && \
            echo 'GÜNCELLEME BAŞARIYLA TAMAMLANDI!' && \
            echo 'Uygulama kapatılıyor, lütfen yeniden başlatın.' && \
            read -p 'Çıkmak için Enter a basın...' && \
            exit
            """
            try:
                subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c \"{komut}\""])
                sys.exit(0) 
            except:
                webbrowser.open(link)
        else:
            QMessageBox.warning(parent, "Hata", "İndirme linki bulunamadı.")