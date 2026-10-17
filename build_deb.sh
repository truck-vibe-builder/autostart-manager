#!/bin/bash
set -e

APP_NAME="autostart-manager"
VERSION="1.0-2"
ARCH="all"
BUILD_DIR="deb_build"
PO_FILE="locale/pt_PT/LC_MESSAGES/autostart-manager.po"
MO_FILE="locale/pt_PT/LC_MESSAGES/autostart-manager.mo"

echo "==> A preparar a estrutura do pacote .deb..."
rm -rf "$BUILD_DIR"
install -d -m 755 "$BUILD_DIR/DEBIAN"
install -d -m 755 "$BUILD_DIR/usr/bin"
install -d -m 755 "$BUILD_DIR/usr/share/applications"
install -d -m 755 "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

# 0. Compilar a tradução (se o msgfmt existir e o .po for mais recente que o .mo)
if command -v msgfmt >/dev/null 2>&1 && [ -f "$PO_FILE" ]; then
    if [ ! -f "$MO_FILE" ] || [ "$PO_FILE" -nt "$MO_FILE" ]; then
        echo "==> A compilar $PO_FILE -> $MO_FILE"
        msgfmt "$PO_FILE" -o "$MO_FILE"
    fi
fi

# 1. Copiar script principal e tornar executável
install -m 755 main.py "$BUILD_DIR/usr/bin/$APP_NAME"

# 2. Copiar ícone SVG plano
install -m 644 autostart-manager.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg"

# 3. Instalar a tradução .mo em pt_PT e pt
if [ -f "$MO_FILE" ]; then
    for L in pt_PT pt; do
        install -d -m 755 "$BUILD_DIR/usr/share/locale/$L/LC_MESSAGES"
        install -m 644 "$MO_FILE" "$BUILD_DIR/usr/share/locale/$L/LC_MESSAGES/$APP_NAME.mo"
    done
else
    echo "AVISO: Ficheiro .mo não encontrado. Certifica-te de que compilaste a tradução!"
fi

# 4. Criar o ficheiro .desktop
cat << EOF > "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Type=Application
Name=Startup Applications
Name[pt_PT]=Aplicações de Arranque
Name[pt]=Aplicações de Arranque
Comment=Manage user startup scripts and applications
Comment[pt_PT]=Gerir scripts e aplicações de arranque do utilizador
Exec=$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;Settings;
X-GNOME-Autostart-enabled=true
EOF
chmod 644 "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"

# 5. Criar o ficheiro de controlo do pacote DEBIAN (Mantenedor sem e-mail público)
cat << EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: truck-vibe-builder <https://github.com/truck-vibe-builder>
Description: Modern GTK3 Startup Applications Manager
 A lightweight, localized (PT-PT) desktop application to manage startup
 scripts and applications for Ubuntu, GNOME, XFCE, and KDE.
EOF
chmod 644 "$BUILD_DIR/DEBIAN/control"

# 6. Construir o pacote .deb
echo "==> A gerar o pacote .deb..."
dpkg-deb --root-owner-group --build "$BUILD_DIR" "${APP_NAME}_${VERSION}_${ARCH}.deb"

# Limpeza
rm -rf "$BUILD_DIR"

echo "==> Sucesso! Pacote gerado: ${APP_NAME}_${VERSION}_${ARCH}.deb"
