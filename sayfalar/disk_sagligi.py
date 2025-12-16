# sayfalar/disk_sagligi.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QComboBox, QTextEdit, QProgressBar, QMessageBox, QApplication)
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import os

class DiskSagligiSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.health_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Disk Sağlığı Analizi", icon))

        if os.path.exists("/usr/sbin/smartctl"):
            self.smart_bin = "/usr/sbin/smartctl"
        elif os.path.exists("/sbin/smartctl"):
            self.smart_bin = "/sbin/smartctl"
        else:
            self.smart_bin = "/usr/sbin/smartctl"

        h_sel = QHBoxLayout()
        self.combo_disk = QComboBox()
        self.diskleri_bul()
        h_sel.addWidget(QLabel("Disk Seç:"))
        h_sel.addWidget(self.combo_disk)
        
        btn_tara = QPushButton("🩺 Sağlık Taraması Yap")
        btn_tara.setStyleSheet("background-color: #33AADD; color: white; font-weight: bold;")
        btn_tara.clicked.connect(self.tara)
        h_sel.addWidget(btn_tara)
        layout.addLayout(h_sel)

        self.lbl_sonuc = QLabel("Durum: Bekleniyor")
        self.lbl_sonuc.setStyleSheet("font-size: 14pt; font-weight: bold; margin: 10px;")
        layout.addWidget(self.lbl_sonuc)

        self.txt_detay = QTextEdit()
        self.txt_detay.setReadOnly(True)
        # Daha modern, konsol benzeri font ve hafif koyu arka plan (eğer tema açıksa bile okunur olsun)
        self.txt_detay.setStyleSheet("font-family: 'Consolas', 'Monospace'; font-size: 10pt; line-height: 1.2;")
        layout.addWidget(self.txt_detay)

        # Onarım Butonu
        btn_onar = QPushButton("🛠️ Disk Hatalarını Onar (fsck - Reboot Gerekir)")
        btn_onar.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 10px;")
        btn_onar.clicked.connect(self.onarim_baslat)
        layout.addWidget(btn_onar)

    def diskleri_bul(self):
        self.combo_disk.clear() 
        try:
            out = subprocess.check_output("lsblk -d -n -o NAME,MODEL,TYPE", shell=True, text=True)
            for line in out.splitlines():
                if "disk" in line:
                    parts = line.split()
                    name = parts[0]
                    model = " ".join(parts[1:-1])
                    self.combo_disk.addItem(f"/dev/{name} - {model}", f"/dev/{name}")
        except: pass

    def raporu_detayli_turkcelestir(self, ham_metin):
        """Smartctl çıktısını analiz edip modern, detaylı Türkçe rapor çıkarır."""
        kimlik = []
        saglik = []
        istatistik = []
        hatalar = []
        
        lines = ham_metin.splitlines()
        disk_turu = "SATA/HDD"
        if "NVMe" in ham_metin: disk_turu = "NVMe/SSD"

        for line in lines:
            line = line.strip()
            
            # --- 1. KİMLİK BİLGİLERİ ---
            if line.startswith("Model Family:") or line.startswith("Model Number:"):
                kimlik.append(f"• Model:         {line.split(':', 1)[1].strip()}")
            elif line.startswith("Serial Number:"):
                kimlik.append(f"• Seri No:       {line.split(':', 1)[1].strip()}")
            elif line.startswith("User Capacity:"):
                cap = line.split(':', 1)[1].strip()
                if "[" in cap: cap = cap.split("[")[1].replace("]", "")
                kimlik.append(f"• Kapasite:      {cap}")
            elif line.startswith("Firmware Version:"):
                kimlik.append(f"• Yazılım Sür.:  {line.split(':', 1)[1].strip()}")

            # --- 2. SAĞLIK DURUMU ---
            elif "SMART overall-health" in line:
                stat = line.split(':', 1)[1].strip()
                saglik.append(f"• GENEL DURUM:   {'✅ SAĞLAM' if 'PASSED' in stat else '❌ BAŞARISIZ'}")
            elif "SMART Health Status:" in line:
                stat = line.split(':', 1)[1].strip()
                saglik.append(f"• GENEL DURUM:   {'✅ SAĞLAM' if 'OK' in stat else '❌ HATA'}")
            elif "Critical Warning:" in line:
                warn = line.split(':', 1)[1].strip()
                durum = "✅ Yok" if warn == "0x00" else f"⚠️ VAR ({warn})"
                saglik.append(f"• Kritik Uyarı:  {durum}")

            # --- 3. İSTATİSTİKLER (SATA ve NVMe Karışık) ---
            elif "Power_On_Hours" in line:
                # SATA formatı: ID# ATTRIBUTE_NAME FLAG VALUE WORST THRESH TYPE UPDATED WHEN_FAILED RAW_VALUE
                parts = line.split()
                if len(parts) > 9: istatistik.append(f"• Çalışma Süresi: {parts[-1]} Saat")
            elif "Power On Hours:" in line: # NVMe formatı
                istatistik.append(f"• Çalışma Süresi: {line.split(':', 1)[1].strip().replace(',','')} Saat")
                
            elif "Power_Cycle_Count" in line:
                parts = line.split()
                if len(parts) > 9: istatistik.append(f"• Açma/Kapama:    {parts[-1]} Kez")
            elif "Power Cycles:" in line: # NVMe
                istatistik.append(f"• Açma/Kapama:    {line.split(':', 1)[1].strip().replace(',','')} Kez")

            elif "Temperature_Celsius" in line:
                parts = line.split()
                if len(parts) > 9: istatistik.append(f"• Sıcaklık:       {parts[-1]} °C")
            elif "Temperature:" in line and "Celsius" in line:
                temp = line.split()[1]
                if temp != "0": istatistik.append(f"• Sıcaklık:       {temp} °C")

            # NVMe Özel Veri (Toplam Yazılan)
            elif "Data Units Written:" in line:
                # Genelde 512 byte units verilir, kabaca TB'a çevirelim
                raw_val = line.split(':', 1)[1].split('[')[0].strip().replace(',', '')
                try:
                    tb_val = int(raw_val) * 512 / (1024**4) # TB hesabı
                    istatistik.append(f"• Toplam Yazılan: {tb_val:.2f} TB")
                except: pass

            # --- 4. KRİTİK HATALAR (Eğer 0 değilse göster) ---
            # Reallocated_Sector_Ct
            if "Reallocated_Sector_Ct" in line:
                parts = line.split()
                raw = int(parts[-1])
                if raw > 0: hatalar.append(f"⚠️ Bozuk Sektör (Reallocated): {raw}")
            
            # Current_Pending_Sector
            elif "Current_Pending_Sector" in line:
                parts = line.split()
                raw = int(parts[-1])
                if raw > 0: hatalar.append(f"⚠️ Bekleyen Sektör (Pending): {raw}")
            
            # UDMA_CRC_Error_Count (Kablo hatası)
            elif "UDMA_CRC_Error_Count" in line:
                parts = line.split()
                raw = int(parts[-1])
                if raw > 0: hatalar.append(f"ℹ️ İletişim Hatası (CRC): {raw} (Kabloyu kontrol et)")
            
            # Media_and_Data_Integrity_Errors (NVMe)
            elif "Media and Data Integrity Errors:" in line:
                val = line.split(':', 1)[1].strip()
                if val != "0": hatalar.append(f"⚠️ Veri Bütünlüğü Hatası: {val}")

        # --- RAPOR OLUŞTURMA ---
        final_report = []
        final_report.append(f"=== {disk_turu} SAĞLIK RAPORU ===")
        final_report.append("")
        
        final_report.append("--- [1] CİHAZ BİLGİLERİ ---")
        final_report.extend(kimlik)
        final_report.append("")
        
        final_report.append("--- [2] SAĞLIK DURUMU ---")
        final_report.extend(saglik)
        if not hatalar:
            final_report.append("• Disk yüzeyinde kritik hata tespit edilmedi.")
        final_report.append("")
        
        if hatalar:
            final_report.append("--- [!] TESPİT EDİLEN SORUNLAR ---")
            final_report.extend(hatalar)
            final_report.append("")

        final_report.append("--- [3] İSTATİSTİKLER ---")
        final_report.extend(istatistik)
        
        return "\n".join(final_report)

    def tara(self):
        if not os.path.exists(self.smart_bin):
            QMessageBox.critical(self, "Eksik Bileşen", "smartmontools paketi eksik.\nKurmak için: sudo apt install smartmontools"); return

        dev = self.combo_disk.currentData()
        if not dev: return
        
        self.lbl_sonuc.setText("Taranıyor...")
        self.txt_detay.clear()
        QApplication.processEvents()
        
        final_output = ""
        
        try:
            # TEK SEFERDE YETKİLENDİRME (Auto -> SCSI Fallback)
            shell_cmd = (
                f"output=$({self.smart_bin} -a -d auto {dev} 2>&1); "
                f"if echo \"$output\" | grep -E -q 'Unknown USB bridge|specify device type'; then "
                f"{self.smart_bin} -a -d scsi {dev}; "
                f"else echo \"$output\"; fi"
            )
            
            cmd = ["pkexec", "sh", "-c", shell_cmd]
            process = subprocess.run(cmd, capture_output=True, text=True)
            final_output = process.stdout
            
            if not final_output.strip() and process.stderr:
                final_output = process.stderr

        except Exception as e:
            final_output = str(e)

        # Çıktıyı DETAYLI Türkçeleştir ve Göster
        # Eğer çok kısa bir çıktıysa (hata veya desteklenmiyor) direkt göster
        if len(final_output) < 300 and "Unknown" in final_output:
             self.txt_detay.setText(f"Disk verisi tam okunamadı.\nHata:\n{final_output}")
        else:
             turkce_cikti = self.raporu_detayli_turkcelestir(final_output)
             self.txt_detay.setText(turkce_cikti)
        
        # --- DURUM BELİRLEME (Görsel Renklendirme) ---
        durum = "BELIRSIZ"
        
        if "SMART Health Status: OK" in final_output: durum = "SAGLAM"
        elif "test result: PASSED" in final_output: durum = "SAGLAM"
        elif "Health Status: OK" in final_output: durum = "SAGLAM"
        elif "Critical Warning: 0x00" in final_output: durum = "SAGLAM"
        elif "test result: FAILED" in final_output or "Health Status: BAD" in final_output: durum = "HATALI"
        elif "Unknown USB bridge" in final_output: 
            self.lbl_sonuc.setText("⚠️ USB Tanınamadı")
            self.lbl_sonuc.setStyleSheet("font-size: 14pt; font-weight: bold; color: #f1c40f;")
            return

        if durum == "SAGLAM":
            self.lbl_sonuc.setText("✅ Durum: SAĞLAM")
            self.lbl_sonuc.setStyleSheet("font-size: 14pt; font-weight: bold; color: #2ecc71;")
        elif durum == "HATALI":
            self.lbl_sonuc.setText("❌ Durum: HATALI")
            self.lbl_sonuc.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e74c3c;")
        else:
            self.lbl_sonuc.setText("⚠️ Durum: Veri Yok / Belirsiz")
            self.lbl_sonuc.setStyleSheet("font-size: 14pt; font-weight: bold; color: #f1c40f;")

    def onarim_baslat(self):
        dev = self.combo_disk.currentData()
        if not dev: return
        if QMessageBox.question(self, "Onarım Planla", f"{dev} için fsck onarımı planlanacak (Yeniden başlatma gerekir).", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                subprocess.run(["pkexec", "touch", "/forcefsck"], check=True)
                QMessageBox.information(self, "Başarılı", "Onarım planlandı. Bilgisayarı yeniden başlatın.")
            except: QMessageBox.critical(self, "Hata", "Onarım planlanamadı.")