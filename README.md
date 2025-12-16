# 🐧 Sistem Asistanı (System Assistant)

![Durum](https://img.shields.io/badge/durum-aktif-success.svg) ![Sürüm](https://img.shields.io/badge/sürüm-v1.1-blue.svg) ![Python](https://img.shields.io/badge/Python-3.10%2B-yellow.svg) ![Lisans](https://img.shields.io/badge/lisans-GPLv3-red.svg)

**Sistem Asistanı**, Linux tabanlı işletim sistemleri (özellikle **Pardus**, Debian ve Ubuntu türevleri) için geliştirilmiş; sistem izleme, bakım, ağ yönetimi ve donanım analizini tek bir modern arayüzde birleştiren kapsamlı bir masaüstü uygulamasıdır.

**Python** ve **PyQt6** teknolojileri ile geliştirilen uygulama, sistem kaynaklarını yormadan arka planda çalışabilir, **HUD Modu** ile ekranınızda yer kaplamadan anlık bilgi sunabilir.

---

## 🌟 Öne Çıkan Özellikler

Uygulama, aşağıdaki gelişmiş araçları sunar:

### 🖥️ 1. Gelişmiş Arayüz ve Kullanım
* **Modern Dashboard:** CPU (Çekirdek bazlı), RAM, Swap ve Sıcaklık değerlerini anlık grafiklerle izleme.
* **HUD Modu (Heads-Up Display):** Ana pencereyi gizleyip, masaüstünde yüzen, her zaman üstte duran minimal bir bilgi penceresine geçiş yapabilme.
* **Sistem Tepsisi (Tray) Entegrasyonu:** Uygulama kapatıldığında arka planda çalışmaya devam eder, tepsi ikonundan yönetilebilir.
* **Tema Desteği:** Sistem temasını (Karanlık/Aydınlık) otomatik algılar veya manuel seçim imkanı sunar.

### 🌐 2. Ağ ve Bağlantı Araçları
* **ISS Haritası:** İnternete bağlandığınız veri merkezi (İSS) kabaca konum bilgisini verir. (Anlık takip etmez, veri kullanmaz, "Yenile" tıklanırsa yeniden veri kullanır)
* **Wi-Fi Şifre Gösterici:** Bağlı olduğunuz kablosuz ağın şifresini tek tıkla görüntüleme (Unutulan şifreler için pratik çözüm).
* **Port Yöneticisi:** Sistemdeki açık portları ve dinleyen servisleri listeleme. Port açma, kapatma, silme vb.
* **Site Engelleyici / İnternet Kısıtlayıcı:** İstenmeyen web sitelerine erişimi kolayca kısıtlama. Ya da belirlediğiniz saat aralığında internet bağlantısını komple kısıtlama.
* **Wi-Fi Analizörü:** Çevredeki kablosuz ağların sinyal kalitesini analiz etme.
* **Ağ Tarayıcı:** Ağınıza bağlı o an veri çekmekte olan cihazların listesi, IP, isim ve MAC adreslerini gösterir. (Komşum Wi-Fi ağımdan beleşe internete giriyor mu? kontrol edin).
* **Hız Testi:** Ping, Giden ve Gelen paket ölçümü ile program içerisinden İnternet Hız testi yapın.

### 🛠️ 3. Sistem Yönetimi ve Bakım
* **Süreç ve Servis Yönetimi:** Çalışan işlemleri (kill/suspend) ve sistem servislerini (Apache, MySQL vb.) yönetme.
* **Disk Araçları:** Disk sağlığı (S.M.A.R.T), doluluk analizi ve bölümleme bilgileri.
* **USB Yazdırıcı:** ISO dosyalarını USB belleklere güvenli bir şekilde yazdırma aracı.
* **Zamanlanmış Görevler (Cron):** Karmaşık terminal komutları olmadan zamanlanmış görevler oluşturma.
* **Sistem Temizliği:** Önbellek, geçici dosyalar ve gereksiz paket artıklarını temizleme.
* **Özel Komutlar:** Sık kullanılan terminal komutlarını butonlara atayıp tek tıkla çalıştırma.

### 🚀 4. Performans ve Güvenlik
* **Tekil Çalışma (Single Instance):** `QLocalServer` soket yapısı sayesinde uygulamanın ikinci kez açılmasını engeller, mevcut pencereyi öne getirir.
* **Donanım Algılama:** İşlemci modeli, Ekran kartı (GPU), Batarya durumu ve Sensör sıcaklıklarını otomatik tespit eder.

---

## 📸 Ekran Görüntüleri

| Genel Bakış & Harita | HUD Modu (Mini Pencere) |
|:---:|:---:|
| ![Dashboard](screenshots/genel_bakis.png) | ![HUD](screenshots/hud.png) |

---

## ⚙️ Kurulum ve Çalıştırma

Bu proje **Python 3** ve **PyQt6** kütüphanelerini kullanır.

### Gereksinimler

requeriments.txt içerisinden kendisi tüm gereksinimleri indirmektedir. 

---

### Adım Adım Yükleme / Kurulum

### Yöntem 1 : (deb paketini indirip çift tıklayın)

**Pardus 23 ve ya daha eski sürümler (Debian 11 > ) için :** (https://github.com/tvardar/sistem-asistani/releases/download/v0.9/sistem-asistani_1.0_pardus23_amd64.deb)

**Pardus 25 ve ya daha yeni sürümler (Debian 12 = < ) için :** (https://github.com/tvardar/sistem-asistani/releases/download/v1.1/sistem-asistani_1.1_amd64.deb)

Bu dosyalardan sisteminize uygun olanı indirip **çift tıklayarak** kurabilir **ya da**  indirdiğiniz klasöre girerek ;

(dosya_adi kısmına indirdiğiniz dosya adını yazın)

```bash
    sudo dpkg -i dosya_adi.deb
    sudo apt-get install -f  # Eksik bağımlılık varsa tamamlar
```
---

### Yöntem 2 : (Kaynak dosyadan kendiniz paketleyin)

Buradan : (https://github.com/tvardar/sistem-asistani/archive/refs/heads/main.zip) kaynak dosyayı indirin.

Bir klasöre çıkarın ve o klasör içerisinde terminal açın

**Pardus 25 - Debian 12 ve yeni sürümler için**

```bash
    sudo sh ./paketle_pardus25.sh
```

**Pardus 23 - Debian 11 ve eski sürümler**

```bash
    sudo sh ./paketle_pardus23.sh
```

---

## 🤝 Katkıda Bulunma

Açık kaynak felsefesine inanıyoruz! Katkıda bulunmak için:

1.  Bu depoyu "Fork"layın.
2.  Yeni bir özellik dalı (branch) oluşturun (`git checkout -b yeni-ozellik`).
3.  Yaptığınız geliştirmeleri commit'leyin.
4.  Dalınızı "Push"layın ve bir "Pull Request" oluşturun.

---

## 📝 Lisans

Bu proje **GNU General Public License v3.0 (GPLv3)** ile lisanslanmıştır.
Bu, yazılımı özgürce kullanabileceğiniz, değiştirebileceğiniz ve paylaşabileceğiniz anlamına gelir. Daha fazla detay için `LICENSE` dosyasına bakınız.

---

## 👨‍💻 Geliştirici ve İletişim

Bu proje **Tarık VARDAR** tarafından geliştirilmektedir.

* **Web:** [www.tarikvardar.com.tr](https://www.tarikvardar.com.tr)
* **E-posta:** [tarikvardar@gmail.com](mailto:tarikvardar@gmail.com)

*Sistem Asistanı, Pardus topluluğuna ve Linux dünyasına katkı sağlamak amacıyla sevgiyle kodlanmıştır.* ❤️

---
