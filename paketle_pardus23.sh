#!/bin/bash

# --- PROJE BİLGİLERİ (PARDUS 23 / DEBIAN 11) ---
APP_NAME="sistem-asistani"
ICON_NAME="sistem-asistani"
VERSION="1.1"
ARCH="amd64"
MAINTAINER="Tarik Vardar <tarikvardar@gmail.com>"
WEBSITE="https://www.tarikvardar.com.tr"
DESCRIPTION="Gelismiş Linux Sistem Yonetim ve Analiz Araci (Pardus 23 Uyumlu)"

# --- KLASÖR TANIMLARI ---
BUILD_DIR="build_deb"
OUTPUT_DEB="${APP_NAME}_${VERSION}_pardus23_${ARCH}.deb"
LOCAL_DEPS="bagimliliklar"

echo "🚀 PAKETLEME SİHİRBAZI BAŞLATILIYOR (Pardus 23 - v$VERSION)..."

# ==============================================================================
# 1. TEMİZLİK
# ==============================================================================
echo "🧹 Temizlik yapılıyor..."
rm -rf build dist $BUILD_DIR *.deb *.spec

# ==============================================================================
# 2. SİSTEM GEREKSİNİMLERİ (PIP & PYINSTALLER)
# ==============================================================================
if ! command -v pip3 &> /dev/null; then
    echo "⚠️  pip3 yükleniyor..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "⚠️  PyInstaller yükleniyor..."
    pip3 install pyinstaller
    export PATH="$HOME/.local/bin:$PATH"
fi

# ==============================================================================
# 3. BAĞIMLILIKLARI VE PYINSTALLER'I YEREL KLASÖRE İNDİR
# ==============================================================================
echo "⬇️  Kütüphaneler indiriliyor..."
mkdir -p $LOCAL_DEPS
pip3 install -r requirements.txt --target "$LOCAL_DEPS" --upgrade
# PyInstaller'ı da buraya indiriyoruz ki sistemde yoksa sorun çıkmasın
pip3 install pyinstaller --target "$LOCAL_DEPS" --upgrade

find "$LOCAL_DEPS" -name "__pycache__" -type d -exec rm -rf {} +
find "$LOCAL_DEPS" -name "*.dist-info" -type d -exec rm -rf {} +

# ==============================================================================
# 4. DERLEME
# ==============================================================================
echo "📦 Derleniyor..."
export PYTHONPATH="$(pwd)/$LOCAL_DEPS:$PYTHONPATH"

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
# 5. PAKETLEME
# ==============================================================================
echo "📂 Paket oluşturuluyor..."
mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/opt/$APP_NAME
mkdir -p $BUILD_DIR/usr/bin
mkdir -p $BUILD_DIR/usr/share/applications
mkdir -p $BUILD_DIR/usr/share/icons/hicolor/512x512/apps
mkdir -p $BUILD_DIR/usr/share/pixmaps

cp -r dist/SistemAsistani/* $BUILD_DIR/opt/$APP_NAME/
mkdir -p $BUILD_DIR/opt/$APP_NAME/icons
cp icons/sistem-asistani.png $BUILD_DIR/opt/$APP_NAME/icons/
cp icons/sistem-asistani-dark.png $BUILD_DIR/opt/$APP_NAME/icons/
cp icons/sistem-asistani.png $BUILD_DIR/usr/share/icons/hicolor/512x512/apps/$ICON_NAME.png
cp icons/sistem-asistani.png $BUILD_DIR/usr/share/pixmaps/$ICON_NAME.png

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

# CONTROL DOSYASI (PARDUS 23 UYUMLU)
cat > $BUILD_DIR/DEBIAN/control << EOF
Package: $APP_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: $MAINTAINER
Homepage: $WEBSITE
Depends: libc6, libgl1, libegl1, policykit-1, libxcb-cursor0, libxcb-xinerama0, libnss3, libasound2, network-manager
Recommends: smartmontools, nmap, ufw
Section: utils
Priority: optional
Description: $DESCRIPTION
 Bu paket Pardus 23 / Debian 11 uyumludur.
 Gerekli Python ve Qt kütüphaneleri pakete gömülüdür.
EOF
chmod 755 $BUILD_DIR/DEBIAN/control

chmod -R 755 $BUILD_DIR/opt/$APP_NAME
chmod -R 755 $BUILD_DIR/DEBIAN
dpkg-deb --build $BUILD_DIR $OUTPUT_DEB

echo "✅ TAMAMLANDI: $OUTPUT_DEB"
