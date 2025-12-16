# sayfalar/port_yoneticisi.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHeaderView, QMessageBox, QGroupBox, QLabel, QLineEdit, QComboBox)
from PyQt6.QtGui import QColor
from gorsel_araclar import SayfaBasligi, SvgIkonOlusturucu
import subprocess
import psutil
import shutil
import os

class PortYoneticisiSayfasi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        icon = SvgIkonOlusturucu.port_ikonu("#33AADD", 32)
        layout.addWidget(SayfaBasligi("Port Yöneticisi", icon))

        layout.addWidget(QLabel("Aktif Bağlantılar ve Dinlenen Portlar:"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["PID", "Uygulama", "Protokol", "Yerel Adres", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Stil temizlendi
        layout.addWidget(self.table)

        h_btn_list = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Listeyi Yenile")
        btn_refresh.clicked.connect(self.yenile)
        h_btn_list.addWidget(btn_refresh)
        
        btn_kill = QPushButton("⛔ Seçili İşlemi (PID) Sonlandır")
        btn_kill.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn_kill.clicked.connect(self.oldur)
        h_btn_list.addWidget(btn_kill)
        layout.addLayout(h_btn_list)

        layout.addSpacing(20)

        # --- ALT KISIM: PORT AÇMA / KAPAMA ---
        grp_firewall = QGroupBox("Güvenlik Duvarı (UFW) Port Yönetimi")
        l_fw = QHBoxLayout(grp_firewall)

        l_fw.addWidget(QLabel("Port No:"))
        self.txt_port = QLineEdit()
        self.txt_port.setPlaceholderText("Örn: 8080")
        self.txt_port.setFixedWidth(100)
        l_fw.addWidget(self.txt_port)

        l_fw.addWidget(QLabel("Protokol:"))
        self.combo_proto = QComboBox()
        self.combo_proto.addItems(["tcp", "udp"])
        l_fw.addWidget(self.combo_proto)

        # Butonlar
        btn_allow = QPushButton("✅ Portu Aç (Allow)")
        btn_allow.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_allow.clicked.connect(lambda: self.port_islem("allow"))
        l_fw.addWidget(btn_allow)

        btn_deny = QPushButton("⛔ Portu Kapat (Deny)")
        btn_deny.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn_deny.clicked.connect(lambda: self.port_islem("deny"))
        l_fw.addWidget(btn_deny)
        
        btn_delete = QPushButton("🗑️ Kuralı Sil")
        btn_delete.setStyleSheet("background-color: #7f8c8d; color: white;")
        btn_delete.clicked.connect(lambda: self.port_islem("delete"))
        l_fw.addWidget(btn_delete)

        layout.addWidget(grp_firewall)

        self.yenile()

    def yenile(self):
        self.table.setRowCount(0)
        try:
            conns = psutil.net_connections(kind='inet')
            for c in conns:
                laddr = f"{c.laddr.ip}:{c.laddr.port}"
                proto = "TCP" if c.type == 1 else "UDP"
                status = c.status
                pid = c.pid
                name = ""
                
                if pid:
                    try: name = psutil.Process(pid).name()
                    except: name = "Bilinmiyor"
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(pid) if pid else "-"))
                self.table.setItem(row, 1, QTableWidgetItem(name))
                self.table.setItem(row, 2, QTableWidgetItem(proto))
                self.table.setItem(row, 3, QTableWidgetItem(laddr))
                self.table.setItem(row, 4, QTableWidgetItem(status))
                
                if status == "LISTEN":
                    self.table.item(row, 4).setForeground(QColor("#2ecc71"))

        except Exception as e:
            pass

    def oldur(self):
        row = self.table.currentRow()
        if row < 0: 
            QMessageBox.warning(self, "Seçim Yok", "Lütfen listeden bir işlem seçin.")
            return
        
        pid_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        
        if not pid_item or pid_item.text() == "-": return
        
        pid = pid_item.text()
        name = name_item.text()
        
        if QMessageBox.question(self, "Onay", f"'{name}' (PID: {pid}) uygulamasını sonlandırmak istiyor musunuz?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                subprocess.run(["pkexec", "kill", "-9", pid], check=True)
                self.yenile()
                QMessageBox.information(self, "Başarılı", "İşlem sonlandırıldı.")
            except:
                QMessageBox.critical(self, "Hata", "İşlem sonlandırılamadı (Yetki reddedildi).")

    def port_islem(self, islem):
        port = self.txt_port.text().strip()
        proto = self.combo_proto.currentText()
        
        if not port.isdigit():
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir port numarası girin.")
            return
        
        ufw_path = shutil.which("ufw")
        if not ufw_path and os.path.exists("/usr/sbin/ufw"): 
            ufw_path = "/usr/sbin/ufw"
        
        if not ufw_path:
            QMessageBox.critical(self, "Hata", "UFW (Güvenlik Duvarı) sistemde bulunamadı.")
            return

        cmd = ["pkexec", ufw_path]
        
        if islem == "delete":
            cmd_str = (
                f"{ufw_path} --force delete allow {port}/{proto}; "
                f"{ufw_path} --force delete deny {port}/{proto}"
            )
            try:
                subprocess.run(["pkexec", "sh", "-c", cmd_str], check=False)
                QMessageBox.information(self, "Bilgi", f"{port}/{proto} için tanımlı kurallar temizlendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme işlemi başarısız: {e}")
            return

        cmd.extend([islem, f"{port}/{proto}"])
        
        try:
            subprocess.run(cmd, check=True)
            QMessageBox.information(self, "Başarılı", f"{port}/{proto} kuralı uygulandı ({islem}).")
        except subprocess.CalledProcessError:
            QMessageBox.warning(self, "Hata", "İşlem yapılamadı (Yetki reddedildi veya hata oluştu).")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Beklenmeyen hata: {str(e)}")