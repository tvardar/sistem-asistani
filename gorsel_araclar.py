# Sistem Asistanı
# Copyright (C) 2025 [Tarık VARDAR]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# gorsel_araclar.py

import platform
import psutil
import requests
import subprocess
import time
import os
import re
import json
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSystemTrayIcon, QInputDialog, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF, QSize, QPointF
from PyQt6.QtGui import QFont, QColor, QPen, QPainter, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

class AyarlarYoneticisi:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/sistem-asistani")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.ayarlar = self.yukle()
    def yukle(self):
        if not os.path.exists(self.config_file): return {"tema": "Otomatik", "renk": "#33AADD"}
        try:
            with open(self.config_file, "r") as f: return json.load(f)
        except: return {"tema": "Otomatik", "renk": "#33AADD"}
    def kaydet(self, anahtar, deger):
        self.ayarlar[anahtar] = deger
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, "w") as f: json.dump(self.ayarlar, f)
    @staticmethod
    def sistem_temasini_algila():
        try:
            out = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], text=True, stderr=subprocess.DEVNULL)
            if "dark" in out.lower(): return "Koyu"
            if "light" in out.lower(): return "Açık"
        except: pass
        return "Koyu"

class SayfaBasligi(QFrame):
    def __init__(self, baslik, icon_pixmap=None):
        super().__init__()
        self.setObjectName("SayfaBasligi")
        l = QHBoxLayout(self); l.setContentsMargins(20, 10, 20, 10)
        if icon_pixmap:
            icon_lbl = QLabel(); icon_lbl.setPixmap(icon_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); l.addWidget(icon_lbl)
        lbl = QLabel(baslik); lbl.setObjectName("BaslikMetni"); l.addWidget(lbl); l.addStretch()

class GostergeWidget(QWidget):
    def sizeHint(self): return QSize(150, 150)
    def __init__(self, parent=None, baslik="Kullanım"):
        super().__init__(parent); self.setMinimumSize(150, 150); self.deger = 0; self.max_deger = 100; self.baslik = baslik; self.tema_renk = "#33AADD"
    def degeri_ayarla(self, deger): self.deger = deger; self.update()
    def set_tema_rengi(self, renk): self.tema_renk = renk; self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect(); mx, my = r.width() / 2, r.height() / 2; rad = min(r.width(), r.height()) / 2 - 10
        rect = QRectF(mx - rad, my - rad, rad * 2, rad * 2)
        p.setPen(QPen(QColor(150, 150, 150, 50), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(rect, int(45 * 16), int(-270 * 16))
        angle = int(270 * (self.deger / self.max_deger)); p.setPen(QPen(QColor(self.tema_renk), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); p.drawArc(rect, int(45 * 16), int(-angle * 16))
        text_color = self.palette().color(self.foregroundRole())
        p.setPen(QColor(self.tema_renk)); p.setFont(QFont("Arial", 20, QFont.Weight.Bold)); p.drawText(QRectF(mx - 50, my - 20, 100, 40), Qt.AlignmentFlag.AlignCenter, f"{int(self.deger)}%")
        p.setPen(text_color); p.setFont(QFont("Arial", 10)); p.drawText(QRectF(mx - 50, my + rad - 25, 100, 20), Qt.AlignmentFlag.AlignCenter, self.baslik)

class HaritaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.layout = QVBoxLayout(self); self.layout.setContentsMargins(0, 0, 0, 0)
        self.harita = QWebEngineView(); s = self.harita.settings(); s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True); s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True); s.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        self.layout.addWidget(self.harita); self.setMinimumSize(300, 200)
        self.html_sablon = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" /><style>body {{ margin: 0; background: #222; }} #map {{ height: 100vh; width: 100%; }}</style></head><body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>window.onload = function() {{ if (typeof L === 'undefined') {{ document.body.innerHTML = "<h3 style='color:white;text-align:center;margin-top:50px;font-family:sans-serif'>Harita Yüklenemedi</h3>"; return; }} try {{ var map = L.map('map').setView([{lat}, {lon}], 13); L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19, attribution: 'OSM' }}).addTo(map); L.marker([{lat}, {lon}]).addTo(map); }} catch(e) {{ console.log(e); }} }};</script></body></html>"""
        self.konumu_guncelle(39.9334, 32.8597)
    def konumu_guncelle(self, lat, lon): self.harita.setHtml(self.html_sablon.format(lat=lat, lon=lon))

class SvgIkonOlusturucu:
    @staticmethod
    def _draw_icon(draw_func, renk, boyut):
        p = QPixmap(boyut, boyut); p.fill(Qt.GlobalColor.transparent); pt = QPainter(p); pt.setRenderHint(QPainter.RenderHint.Antialiasing); pt.setPen(QPen(QColor(renk), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); pt.setBrush(Qt.BrushStyle.NoBrush); draw_func(pt, boyut); pt.end(); return p
    @staticmethod
    def get_pixmap(svg_data, boyut=24): return SvgIkonOlusturucu.ayarlar_ikonu("#33AADD", boyut)
    @staticmethod
    def termometre_getir(renk="#ff5555", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.setBrush(QColor(renk)), pt.drawRoundedRect(int(s * 0.35), int(s * 0.1), int(s * 0.3), int(s * 0.6), 3, 3), pt.drawEllipse(int(s * 0.25), int(s * 0.6), int(s * 0.5), int(s * 0.5))), renk, s)
    @staticmethod
    def indir_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.setPen(QPen(QColor(renk), 3)), pt.drawLine(int(s/2), int(s*0.2), int(s/2), int(s*0.8)), pt.drawLine(int(s/2), int(s*0.8), int(s*0.2), int(s*0.5)), pt.drawLine(int(s/2), int(s*0.8), int(s*0.8), int(s*0.5))), renk, s)
    @staticmethod
    def yukle_ikonu(renk="#e67e22", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.setPen(QPen(QColor(renk), 3)), pt.drawLine(int(s/2), int(s*0.8), int(s/2), int(s*0.2)), pt.drawLine(int(s/2), int(s*0.2), int(s*0.2), int(s*0.5)), pt.drawLine(int(s/2), int(s*0.2), int(s*0.8), int(s*0.5))), renk, s)
    @staticmethod
    def anahtar_ikonu(renk="#aaaaaa", s=20): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(int(s*0.2), int(s*0.2), int(s*0.4), int(s*0.4)), pt.drawLine(int(s*0.5), int(s*0.5), int(s*0.8), int(s*0.8))), renk, s)
    @staticmethod
    def ayarlar_ikonu(renk="#E0E0E0", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(int(s*0.25), int(s*0.25), int(s*0.5), int(s*0.5)), pt.drawLine(int(s/2), 0, int(s/2), int(s*0.2)), pt.drawLine(int(s/2), int(s*0.8), int(s/2), s), pt.drawLine(0, int(s/2), int(s*0.2), int(s/2)), pt.drawLine(int(s*0.8), int(s/2), s, int(s/2))), renk, s)
    @staticmethod
    def hud_ikonu(renk="#ffffff", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRoundedRect(int(s*0.1), int(s*0.1), int(s*0.8), int(s*0.8), 4, 4), pt.drawRect(int(s*0.3), int(s*0.3), int(s*0.4), int(s*0.4))), renk, s)
    @staticmethod
    def dashboard_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRect(int(s*0.1), int(s*0.1), int(s*0.35), int(s*0.35)), pt.drawRect(int(s*0.55), int(s*0.1), int(s*0.35), int(s*0.35)), pt.drawRect(int(s*0.1), int(s*0.55), int(s*0.35), int(s*0.35)), pt.drawRect(int(s*0.55), int(s*0.55), int(s*0.35), int(s*0.35))), renk, s)
    @staticmethod
    def hardware_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: pt.drawRoundedRect(int(s*0.2), int(s*0.2), int(s*0.6), int(s*0.6), 2, 2), renk, s)
    @staticmethod
    def process_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: pt.drawPolyline([QPointF(0, s*0.5), QPointF(s*0.3, s*0.5), QPointF(s*0.45, s*0.2), QPointF(s*0.6, s*0.8), QPointF(s*0.75, s*0.5), QPointF(s, s*0.5)]), renk, s)
    @staticmethod
    def network_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawArc(int(s*0.1), int(s*0.1), int(s*0.8), int(s*0.8), 45*16, 90*16), pt.drawArc(int(s*0.3), int(s*0.3), int(s*0.4), int(s*0.4), 45*16, 90*16), pt.setBrush(QColor(renk)), pt.drawEllipse(QPointF(s*0.5, s*0.8), s*0.08, s*0.08)), renk, s)
    @staticmethod
    def maintenance_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.translate(s/2, s/2), pt.rotate(-45), pt.translate(-s/2, -s/2), pt.drawRoundedRect(int(s*0.42), int(s*0.4), int(s*0.16), int(s*0.55), 2, 2), pt.drawEllipse(int(s*0.25), int(s*0.05), int(s*0.5), int(s*0.5)), pt.setBrush(QColor("#252526")), pt.setPen(Qt.PenStyle.NoPen), pt.drawRect(int(s*0.42), int(s*0.05), int(s*0.16), int(s*0.2)), pt.resetTransform()), renk, s)
    @staticmethod
    def info_ikonu(renk="#33AADD", s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(1, 1, s-2, s-2), pt.drawLine(int(s*0.5), int(s*0.4), int(s*0.5), int(s*0.75)), pt.drawPoint(int(s*0.5), int(s*0.25))), renk, s)
    @staticmethod
    def refresh_ikonu(renk, s=24): return SvgIkonOlusturucu.ayarlar_ikonu(renk, s)
    @staticmethod
    def clean_ikonu(renk, s=24): return SvgIkonOlusturucu.maintenance_ikonu(renk, s)
    @staticmethod
    def fix_ikonu(renk, s=24): return SvgIkonOlusturucu.ayarlar_ikonu(renk, s)
    @staticmethod
    def ram_ikonu(renk, s=24): return SvgIkonOlusturucu.hardware_ikonu(renk, s)
    @staticmethod
    def log_ikonu(renk, s=24): return SvgIkonOlusturucu.dashboard_ikonu(renk, s)
    @staticmethod
    def grub_ikonu(renk, s=24): return SvgIkonOlusturucu.dashboard_ikonu(renk, s)
    @staticmethod
    def usb_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRect(int(s*0.3), int(s*0.4), int(s*0.4), int(s*0.5)), pt.drawLine(int(s*0.4), int(s*0.9), int(s*0.4), int(s*1.0)), pt.drawLine(int(s*0.6), int(s*0.9), int(s*0.6), int(s*1.0)), pt.drawRect(int(s*0.35), int(s*0.1), int(s*0.3), int(s*0.3))), renk, s)
    @staticmethod
    def store_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRect(int(s*0.1), int(s*0.3), int(s*0.8), int(s*0.6)), pt.drawArc(int(s*0.3), int(s*0.1), int(s*0.4), int(s*0.4), 0, 180*16)), renk, s)
    @staticmethod
    def disk_analiz_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(int(s*0.1), int(s*0.1), int(s*0.8), int(s*0.8)), pt.drawLine(int(s/2), int(s/2), int(s/2), int(s*0.1))), renk, s)
    @staticmethod
    def boot_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(int(s*0.1), int(s*0.1), int(s*0.8), int(s*0.8)), pt.drawLine(int(s/2), int(s/2), int(s*0.7), int(s*0.2))), renk, s)
    @staticmethod
    def health_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRect(int(s*0.2), int(s*0.3), int(s*0.6), int(s*0.5)), pt.drawLine(int(s*0.3), int(s*0.55), int(s*0.7), int(s*0.55))), renk, s)
    @staticmethod
    def script_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRect(int(s*0.2), int(s*0.2), int(s*0.6), int(s*0.6)), pt.drawText(QRectF(0,0,s,s), Qt.AlignmentFlag.AlignCenter, ">_")), renk, s)
    @staticmethod
    def port_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(int(s*0.2), int(s*0.2), int(s*0.6), int(s*0.6)), pt.drawLine(0, int(s/2), int(s*0.2), int(s/2)), pt.drawLine(int(s*0.8), int(s/2), s, int(s/2))), renk, s)
    @staticmethod
    def block_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawRoundedRect(int(s*0.2), int(s*0.2), int(s*0.6), int(s*0.7), 5, 5), pt.drawLine(int(s*0.3), int(s*0.3), int(s*0.7), int(s*0.7)), pt.drawLine(int(s*0.7), int(s*0.3), int(s*0.3), int(s*0.7))), renk, s)
    @staticmethod
    def cron_ikonu(renk, s=24): return SvgIkonOlusturucu._draw_icon(lambda pt, s: (pt.drawEllipse(int(s*0.1), int(s*0.1), int(s*0.8), int(s*0.8)), pt.drawLine(int(s/2), int(s/2), int(s/2), int(s*0.2)), pt.drawLine(int(s/2), int(s/2), int(s*0.7), int(s*0.5))), renk, s)

class BilgiIsleyicisi(QThread):
    bilgi_guncelle_sinyal = pyqtSignal(dict)
    bildirim_sinyali = pyqtSignal(str, str)
    disk_degisti_sinyali = pyqtSignal()

    def __init__(self): 
        super().__init__()
        self.cached_konum = None
        self.last_notify_time = 0
        self.onceki_diskler = set()
        self.ag_bilgisi_guncelle_istegi = False
        try:
             if os.path.exists('/sys/class/block'):
                 self.onceki_diskler = set(os.listdir('/sys/class/block'))
        except: pass

    def ag_bilgilerini_yenile(self):
        self.ag_bilgisi_guncelle_istegi = True

    def konum_bul(self):
        try: j = requests.get('http://ip-api.com/json', timeout=5).json(); return {"ip": j.get("query"), "lat": j.get("lat"), "lon": j.get("lon"), "org": j.get("isp"), "sehir": j.get("city"), "ulke": j.get("countryCode")}
        except: return {"ip": "N/A", "lat": 0, "lon": 0}
    def bayt_cevir(self, b): return f"{b / 1048576:.1f} MB"
    def get_gpu_model(self):
        try: return subprocess.check_output("lspci | grep -i 'VGA\\|3D'", shell=True, text=True, stderr=subprocess.DEVNULL).strip().split(':', 2)[-1].strip()
        except: return "Standart VGA / Bilinmiyor"
    def get_disk_models(self):
        models = {}
        try:
            out = subprocess.check_output(["lsblk", "-d", "-n", "-o", "NAME,MODEL"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                parts = line.strip().split(maxsplit=1)
                if len(parts) >= 2: models[parts[0]] = parts[1]
                else: models[parts[0]] = "Disk Birimi"
        except: pass
        return models
    def get_battery(self):
        try: b = psutil.sensors_battery(); return {"percent": b.percent, "plugged": b.power_plugged, "secsleft": b.secsleft} if b else {"status_yok": True}
        except: return {"status_yok": True}
    def get_temp(self):
        try: return int(open("/sys/class/thermal/thermal_zone0/temp").read().strip()) / 1000.0
        except: pass
        try: return psutil.sensors_temperatures()['coretemp'][0].current
        except: return 0
    def run(self):
        while not self.isInterruptionRequested():
            try:
                # Disk Kontrol
                if os.path.exists('/sys/class/block'):
                    simdiki_diskler = set(os.listdir('/sys/class/block'))
                    if simdiki_diskler != self.onceki_diskler:
                        self.onceki_diskler = simdiki_diskler
                        self.disk_degisti_sinyali.emit()
                
                # Konum/IP Güncelleme
                if self.ag_bilgisi_guncelle_istegi or not self.cached_konum or self.cached_konum.get("ip") == "N/A":
                    self.cached_konum = self.konum_bul()
                    self.ag_bilgisi_guncelle_istegi = False
                
                c_pct = psutil.cpu_percent(percpu=True) or [0]
                ram = psutil.virtual_memory(); swap = psutil.swap_memory(); net = psutil.net_io_counters()
                
                avg_cpu = sum(c_pct) / len(c_pct) if c_pct else 0
                now = time.time()
                if now - self.last_notify_time > 60:
                    if avg_cpu > 90:
                        self.bildirim_sinyali.emit("Yüksek CPU Kullanımı", f"İşlemci kullanımı %{avg_cpu:.1f} seviyesinde!")
                        self.last_notify_time = now
                    elif ram.percent > 90:
                        self.bildirim_sinyali.emit("Yüksek RAM Kullanımı", f"Bellek kullanımı %{ram.percent} seviyesinde!")
                        self.last_notify_time = now

                uptime_sec = time.time() - psutil.boot_time()
                m, s = divmod(uptime_sec, 60); h, m = divmod(m, 60); d, h = divmod(h, 24)
                uptime_str = f"{int(d)}g {int(h)}sa {int(m)}dk"

                # DNS (TEK SATIR DÜZELTMESİ)
                dns_info = "Bilinmiyor"
                try:
                    with open("/etc/resolv.conf", "r") as f:
                        dns_list = [line.split()[1] for line in f if line.startswith("nameserver")]
                        if dns_list:
                            # Sadece ilk DNS adresini al
                            dns_info = dns_list[0]
                except: pass
                
                disk_models = self.get_disk_models(); disk_list = []; ignore_fs = ['squashfs', 'tmpfs', 'devtmpfs', 'proc', 'sysfs', 'debugfs', 'tracefs']
                for p in psutil.disk_partitions(all=True):
                    if p.fstype in ignore_fs or not p.device or "/dev/loop" in p.device or "/dev/sr" in p.device: continue
                    try:
                        u = psutil.disk_usage(p.mountpoint)
                        if u.total == 0: continue
                        dev_name = p.device.split('/')[-1]; raw_disk_name = re.sub(r'p?\d+$', '', dev_name)
                        model = disk_models.get(raw_disk_name, disk_models.get(dev_name, "Disk Birimi"))
                        if not model and ("/media/" in p.mountpoint or "/run/media/" in p.mountpoint): model = "USB / Harici Disk"
                        disk_list.append({"aygit": p.device, "baglanti_noktasi": p.mountpoint, "yuzde": u.percent, "kullanilan": f"{u.used / (1024 ** 3):.1f} GB", "toplam": f"{u.total / (1024 ** 3):.1f} GB", "model": model})
                    except: pass
                
                toplam_kullanim_all = sum(float(d['kullanilan'].split()[0]) for d in disk_list)
                toplam_kapasite_all = sum(float(d['toplam'].split()[0]) for d in disk_list)
                yuzde_all = (toplam_kullanim_all / toplam_kapasite_all * 100) if toplam_kapasite_all > 0 else 0
                
                fiziksel_hddler = [d for d in disk_list if re.search(r'/dev/sd[a-z]', d['aygit'])]
                toplam_kullanim = sum(float(d['kullanilan'].split()[0]) for d in fiziksel_hddler)
                toplam_kapasite = sum(float(d['toplam'].split()[0]) for d in fiziksel_hddler)
                yuzde_fiz = (toplam_kullanim / toplam_kapasite * 100) if toplam_kapasite > 0 else 0

                try: ssid = subprocess.check_output("nmcli -t -f NAME connection show --active", shell=True, text=True, stderr=subprocess.DEVNULL).strip().split('\n')[0]
                except: ssid = "Kablolu"
                ni = "Eth"; 
                for i, d in psutil.net_if_stats().items(): 
                    if d.isup and i != 'lo': ni = i; break

                self.bilgi_guncelle_sinyal.emit({
                    "cpu_yuzde": c_pct, "toplam_cpu_yuzde": avg_cpu, 
                    "ram_yuzde": ram.percent, "ram_toplam": f"{ram.total >> 30} GB", 
                    "swap_yuzde": swap.percent, "swap_kullanilan": self.bayt_cevir(swap.used), "swap_toplam": self.bayt_cevir(swap.total), 
                    "uptime": uptime_str, "dns_bilgi": dns_info, 
                    "ag_gonderilen": self.bayt_cevir(net.bytes_sent), "ag_alinan": self.bayt_cevir(net.bytes_recv), 
                    "disk_bolumleri": disk_list, "konum_bilgisi": self.cached_konum, 
                    "ag_ssid": ssid, "ag_arayuz": ni, 
                    "cpu_sicaklik": self.get_temp(), 
                    "dagitim_detay": self.get_distro(), "islemci_model": self.get_cpu_name(), "ekran_karti_model": self.get_gpu_model(), 
                    "batarya": self.get_battery(), 
                    "fiziksel_hdd_kullanim": f"{toplam_kullanim:.1f} GB", "fiziksel_hdd_toplam": f"{toplam_kapasite:.1f} GB", "fiziksel_hdd_yuzde": f"{yuzde_fiz:.1f}%", 
                    "tum_disk_kullanim": f"{toplam_kullanim_all:.1f} GB", "tum_disk_toplam": f"{toplam_kapasite_all:.1f} GB", "tum_disk_yuzde": f"{yuzde_all:.1f}%"
                })
            except: pass
            self.msleep(1000)
    def get_distro(self):
        try: return subprocess.check_output(['lsb_release', '-ds'], text=True).strip()
        except: return platform.platform()
    def get_cpu_name(self):
        try: return [l.split(":")[1].strip() for l in open("/proc/cpuinfo") if "model name" in l][0]
        except: return "Bilinmiyor"
