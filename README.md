# 🐧 Sistem Asistanı (Linux System Assistant)

[![Pardus 25](https://img.shields.io/badge/Pardus-25-2ecc71?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/tvardar/sistem-asistani)

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)
![License](https://img.shields.io/badge/License-GPLv3-green.svg)
![Platform](https://img.shields.io/badge/Platform-Pardus%20%7C%20Debian-red.svg)

**Sistem Asistanı**, özellikle **Pardus** ve **Debian** tabanlı Linux dağıtımları için geliştirilmiş; sistem izleme, bakım, onarım ve yönetim işlemlerini tek bir modern arayüzde toplayan gelişmiş bir araçtır.

Python ve PyQt6 teknolojileriyle geliştirilmiş olup, son kullanıcıların karmaşık terminal komutlarına ihtiyaç duymadan sistemlerini yönetmelerini sağlar.

---

## 📸 Ekran Görüntüleri ve Modüller

Uygulama içerisindeki tüm araçların görünümü aşağıdadır:

| **1. Genel Bakış & HUD** | **2. Donanım & Güç** | **3. Süreç Yönetimi** |
|:---:|:---:|:---:|
| ![Genel Bakış](screenshots/genel_bakis.png)<br>*(HUD Modu Dahil)* | ![Donanım](screenshots/donanim.png) | ![Süreçler](screenshots/surec.png) |

| **4. Port Yöneticisi** | **5. Ağ & DNS** | **6. Wi-Fi Analizörü** |
|:---:|:---:|:---:|
| ![Port](screenshots/port.png) | ![Ağ](screenshots/ag.png) | ![WiFi](screenshots/wifi.png) |

| **7. Site Engelleyici** | **8. Zamanlanmış Görevler** | **9. Disk Analizi** |
|:---:|:---:|:---:|
| ![Site Engel](screenshots/site_engel.png) | ![Cron](screenshots/cron.png) | ![Disk Analiz](screenshots/disk_analiz.png) |

| **10. Disk Sağlığı** | **11. Sistem Temizliği** | **12. Açılış Analizi** |
|:---:|:---:|:---:|
| ![Disk Sağlık](screenshots/disk_saglik.png) | ![Temizlik](screenshots/temizle.png) | ![Açılış](screenshots/acilis.png) |

| **13. Sistem Günlüğü** | **14. Özel Komutlar** | **15. USB Yazdırıcı** |
|:---:|:---:|:---:|
| ![Günlük](screenshots/gunluk.png) | ![Komutlar](screenshots/komutlar.png) | ![USB](screenshots/usb.png) |

| **16. Sistem Yönetimi** | **17. Bakım & Onarım** | **18. Ayarlar** |
|:---:|:---:|:---:|
| ![Yönetim](screenshots/yonetim.png) | ![Bakım](screenshots/bakim.png) | ![Ayarlar](screenshots/ayarlar.png) |

| **19. Hakkında** | **HUD Penceresi** | |
|:---:|:---:|:---:|
| ![Hakkında](screenshots/hakkinda.png) | ![HUD](screenshots/hud.png) | |

---

## 🌟 Özellikler

Uygulama modüler bir yapıya sahiptir ve aşağıdaki temel araçları içerir:

### 🖥️ Sistem İzleme & Donanım
* **Genel Bakış:** CPU, RAM, Swap kullanımı, anlık ağ trafiği ve harita üzerinde konum bilgisi.
* **HUD Modu:** Masaüstünde yüzen, kompakt sistem bilgi penceresi.
* **Donanım Bilgisi:** İşlemci, GPU, Batarya sağlığı, BIOS ve Çekirdek bilgileri.
* **Süreç Yöneticisi:** Çalışan işlemleri (PID, CPU, RAM) izleme ve sonlandırma.

### 🌐 Ağ & İnternet
* **Wi-Fi Analizörü:** Çevredeki ağları tarama, sinyal gücü grafiği ve kanal önerisi (2.4GHz optimizasyonu).
* **Hız Testi:** Çoklu iş parçacığı ile İndirme (Download), Yükleme (Upload) ve Gecikme (Ping) testi.
* **DNS Yönetimi:** Tek tıkla Google, Cloudflare, OpenDNS veya Otomatik DNS geçişi.
* **Site Engelleyici:** `/etc/hosts` üzerinden istenmeyen siteleri engelleme ve zaman ayarlı internet kısıtlama.
* **Port Yöneticisi:** Açık portları listeleme ve güvenlik duvarı (UFW) üzerinden port açma/kapama.

### 🛠️ Bakım & Onarım
* **Sistem Temizliği:** Apt önbelleği, eski kernel logları, tarayıcı çöp dosyaları ve thumbnail temizliği.
* **Disk Sağlığı:** S.M.A.R.T verileri ile disk ömrü analizi ve sağlık raporu.
* **Açılış Analizi:** Sistemi yavaşlatan başlangıç servislerinin tespiti (`systemd-analyze`).
* **Otomatik Bakım:** Paket güncellemeleri, bozuk paket onarımı ve GRUB güncelleme araçları.

### 💾 Disk & Dosya
* **Disk Analizcisi:** Klasör boyutlarını ağaç yapısında görselleştirme.
* **USB Yazdırıcı:** ISO dosyalarını USB belleklere yazdırma (dd arayüzü).

### ⚙️ Yönetim & Otomasyon
* **Cron Yöneticisi:** Zamanlanmış görevleri grafik arayüzle ekleme/silme.
* **Özel Komutlar:** Sık kullandığınız uzun terminal komutlarını butonlara dönüştürme.
* **Başlangıç Yöneticisi:** Sistem açılışında çalışan uygulamaları yönetme.

---

## 🚀 Kurulum

### Yöntem 1: .deb Paketi ile Kurulum (Önerilen - Kolay)
GitHub **[Releases](https://github.com/tvardar/sistem-asistani/releases)** sayfasından son sürümü indirin ve **çift tıklayarak kurun** veya terminalden:

```bash
sudo dpkg -i sistem-asistani_1.0_amd64.deb
sudo apt-get install -f  # Eksik bağımlılık varsa tamamlar
```

### Yöntem 2: Paketleme Sihirbazı ile Kurulum (Offline Paket Oluşturma)
Bu yöntem, projenin kaynak kodlarını çeker, **gerekli tüm Python bağımlılıklarını internetten indirip içine gömer** ve size internet olmayan bilgisayarlarda da çalışabilen bir .deb paketi üretir.

```bash
git clone [https://github.com/tvardar/sistem-asistani.git](https://github.com/tvardar/sistem-asistani.git)
cd sistem-asistani
sudo sh ./paketle.sh
sudo dpkg -i sistem-asistani_1.0_amd64.deb
```

### Kaynak Koddan Çalıştırma (Geliştirici Modu)
Geliştiriciler veya depoyu klonlayıp direkt çalıştırmak isteyenler için:

```bash
sudo apt update
sudo apt install python3-pip python3-venv libxcb-cursor0 network-manager ufw smartmontools nmap

git clone [https://github.com/tvardar/sistem-asistani.git](https://github.com/tvardar/sistem-asistani.git)
cd sistem-asistani
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 sistem_asistani.py
```