#!/bin/bash
set -e

APP_NAME="autostart-manager"
VERSION="1.0-3"
ARCH="all"
BUILD_DIR="deb_build"
PO_FILE="locale/pt_PT/LC_MESSAGES/autostart-manager.po"
MO_FILE="locale/pt_PT/LC_MESSAGES/autostart-manager.mo"
REPO_URL="https://github.com/truck-vibe-builder/autostart-manager"

echo "==> Preparing .deb package structure..."
rm -rf "$BUILD_DIR"
install -d -m 755 "$BUILD_DIR/DEBIAN"
install -d -m 755 "$BUILD_DIR/usr/bin"
install -d -m 755 "$BUILD_DIR/usr/share/applications"
install -d -m 755 "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"
install -d -m 755 "$BUILD_DIR/usr/share/metainfo"
install -d -m 755 "$BUILD_DIR/usr/share/doc/$APP_NAME"

# 0. Compile localization catalog if msgfmt is present
if command -v msgfmt >/dev/null 2>&1 && [ -f "$PO_FILE" ]; then
    if [ ! -f "$MO_FILE" ] || [ "$PO_FILE" -nt "$MO_FILE" ]; then
        echo "==> Compiling translation catalog: $PO_FILE -> $MO_FILE"
        msgfmt "$PO_FILE" -o "$MO_FILE"
    fi
fi

# 1. Install main executable script
install -m 755 main.py "$BUILD_DIR/usr/bin/$APP_NAME"

# 2. Install application icon
install -m 644 autostart-manager.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg"

# 3. Install binary translation (.mo)
if [ -f "$MO_FILE" ]; then
    for L in pt_PT pt; do
        install -d -m 755 "$BUILD_DIR/usr/share/locale/$L/LC_MESSAGES"
        install -m 644 "$MO_FILE" "$BUILD_DIR/usr/share/locale/$L/LC_MESSAGES/$APP_NAME.mo"
    done
fi

# 4. Install desktop launcher
install -m 644 "${APP_NAME}.desktop" "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"

# 5. Install AppStream Metainfo XML
install -m 644 "${APP_NAME}.metainfo.xml" "$BUILD_DIR/usr/share/metainfo/$APP_NAME.metainfo.xml"

# 6. Install Debian Copyright file
install -m 644 copyright "$BUILD_DIR/usr/share/doc/$APP_NAME/copyright"

# 7. Generate DEBIAN control metadata
cat << EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: truck-vibe-builder <https://github.com/truck-vibe-builder>
Homepage: $REPO_URL
Description: Modern GTK3 Startup Applications Manager
 A lightweight desktop application to manage startup scripts and
 applications for Ubuntu, Linux Mint, GNOME, XFCE, and KDE.
EOF
chmod 644 "$BUILD_DIR/DEBIAN/control"

# 8. Build final .deb binary package
echo "==> Building .deb package..."
dpkg-deb --root-owner-group --build "$BUILD_DIR" "${APP_NAME}_${VERSION}_${ARCH}.deb"

# Cleanup
rm -rf "$BUILD_DIR"

echo "==> Success! Generated package: ${APP_NAME}_${VERSION}_${ARCH}.deb"
