#!/bin/bash

# --- PROJE BİLGİLERİ ---
APP_NAME="sistem-asistani"
ICON_NAME="sistem-asistani"
VERSION="1.1"
ARCH="amd64"
MAINTAINER="Tarik Vardar <tarikvardar@gmail.com>"
WEBSITE="https://www.tarikvardar.com.tr"
DESCRIPTION="Gelismiş Linux Sistem Yonetim ve Analiz Araci"

# --- KLASÖR TANIMLARI ---
BUILD_DIR="build_deb"
OUTPUT_DEB="${APP_NAME}_${VERSION}_${ARCH}.deb"
LOCAL_DEPS="bagimliliklar"

echo "🚀 PAKETLEME SİHİRBAZI BAŞLATILIYOR (v$VERSION)..."

# ==============================================================================
# 1. TEMİZLİK
# ==============================================================================
echo "🧹 Temizlik yapılıyor..."
rm -rf build dist $BUILD_DIR *.deb *.spec
# Not: bagimliliklar klasörünü silmiyoruz, varsa güncelliyoruz.

# ==============================================================================
# 2. BAĞIMLILIKLARI YEREL KLASÖRE İNDİR (Offline Destek İçin)
# ==============================================================================
echo "⬇️  Bağımlılıklar '$LOCAL_DEPS' klasörüne indiriliyor..."
if ! command -v pip3 &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

mkdir -p $LOCAL_DEPS
# --upgrade stratejisi ile sadece gerekli olanları indirir
pip3 install -r requirements.txt --target "$LOCAL_DEPS" --upgrade --break-system-packages

# Gereksiz önbellekleri temizle
find "$LOCAL_DEPS" -name "__pycache__" -type d -exec rm -rf {} +
find "$LOCAL_DEPS" -name "*.dist-info" -type d -exec rm -rf {} +

# ==============================================================================
# 3. PYINSTALLER İLE DERLEME
# ==============================================================================
echo "📦 PyInstaller ile tek parça haline getiriliyor..."
# PYTHONPATH'e yerel bağımlılıkları ekliyoruz ki PyInstaller oradan alsın
export PYTHONPATH="$(pwd)/$LOCAL_DEPS:$PYTHONPATH"

# --paths="$LOCAL_DEPS" ekleyerek PyInstaller'a kütüphaneleri gösteriyoruz
python3 -m PyInstaller sistem_asistani.py \
    --name="SistemAsistani" \
    --onedir \
    --windowed \
    --noconsole \
    --clean \
    --noconfirm \
    --strip \
    --paths="$LOCAL_DEPS" \
    --add-data="icons:icons" \
    --add-data="sayfalar:sayfalar" \
    --icon="icons/sistem-asistani.png" \
    --contents-directory="libs" \
    --hidden-import="PyQt6" \
    --hidden-import="PyQt6.QtCore" \
    --hidden-import="PyQt6.QtGui" \
    --hidden-import="PyQt6.QtWidgets" \
    --hidden-import="PyQt6.QtWebEngineWidgets" \
    --hidden-import="PyQt6.QtWebEngineCore" \
    --hidden-import="PyQt6.QtNetwork" \
    --collect-all="PyQt6" \
    --collect-all="PyQt6_WebEngine" \
    --collect-all="requests" \
    --collect-all="psutil"

if [ ! -d "dist/SistemAsistani" ]; then
    echo "❌ HATA: Derleme başarısız oldu!"
    exit 1
fi

# ==============================================================================
# 4. DEB PAKET YAPISI
# ==============================================================================
echo "📂 .deb paket yapısı kuruluyor..."

mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/opt/$APP_NAME
mkdir -p $BUILD_DIR/usr/bin
mkdir -p $BUILD_DIR/usr/share/applications
mkdir -p $BUILD_DIR/usr/share/icons/hicolor/512x512/apps
mkdir -p $BUILD_DIR/usr/share/pixmaps

# Uygulamayı /opt altına kopyala
cp -r dist/SistemAsistani/* $BUILD_DIR/opt/$APP_NAME/

# İkonları kopyala
mkdir -p $BUILD_DIR/opt/$APP_NAME/icons
cp icons/sistem-asistani.png $BUILD_DIR/opt/$APP_NAME/icons/
cp icons/sistem-asistani-dark.png $BUILD_DIR/opt/$APP_NAME/icons/

# Sistem ikonları
cp icons/sistem-asistani.png $BUILD_DIR/usr/share/icons/hicolor/512x512/apps/$ICON_NAME.png
cp icons/sistem-asistani.png $BUILD_DIR/usr/share/pixmaps/$ICON_NAME.png

# ==============================================================================
# 5. BAŞLATICI VE DESKTOP DOSYASI
# ==============================================================================
cat > $BUILD_DIR/usr/bin/$APP_NAME << EOF
#!/bin/bash
export QT_QPA_PLATFORM=xcb
cd /opt/$APP_NAME
./SistemAsistani "\$@"
EOF
chmod 755 $BUILD_DIR/usr/bin/$APP_NAME

cat > $BUILD_DIR/usr/share/applications/$APP_NAME.desktop << EOF
[Desktop Entry]
Name=Sistem Asistanı
Comment=Sistem Bakım ve Analiz Aracı
Exec=/usr/bin/$APP_NAME
Icon=$ICON_NAME
Terminal=false
Type=Application
Categories=System;Utility;
StartupNotify=true
EOF
chmod 644 $BUILD_DIR/usr/share/applications/$APP_NAME.desktop

# ==============================================================================
# 6. CONTROL DOSYASI
# ==============================================================================
# NOT: python3-pyqt6.qtwebengine paketi, libqt6* kütüphanelerini otomatik çeker.
# Bu yöntem Pardus 25 ve Debian 12 için en güvenli yoldur.
cat > $BUILD_DIR/DEBIAN/control << EOF
Package: $APP_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: $MAINTAINER
Homepage: $WEBSITE
Depends: libc6, libgl1, libegl1, pkexec, libxcb-cursor0, libxcb-xinerama0, libnss3, libasound2, network-manager, python3-pyqt6.qtwebengine
Recommends: smartmontools, nmap, ufw
Section: utils
Priority: optional
Description: $DESCRIPTION
 Bu paket tam sürüm olup internet gerektirmez.
 Tüm Python bağımlılıkları pakete gömülüdür.
EOF
chmod 755 $BUILD_DIR/DEBIAN/control

# ==============================================================================
# 7. PAKETLEME
# ==============================================================================
echo "🔒 İzinler ayarlanıyor..."
chmod -R 755 $BUILD_DIR/opt/$APP_NAME
chmod -R 755 $BUILD_DIR/DEBIAN

echo "📦 .deb paketi oluşturuluyor..."
dpkg-deb --root-owner-group --build $BUILD_DIR $OUTPUT_DEB

echo "✅ TAMAMLANDI: $OUTPUT_DEB"