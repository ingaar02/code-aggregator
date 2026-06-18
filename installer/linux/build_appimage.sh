#!/bin/bash
set -e

APP_NAME="CodeAggregator"
VERSION="1.0.0"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
APPDIR="$DIST_DIR/AppDir"
APPIMAGE_NAME="$APP_NAME-$VERSION-x86_64.AppImage"
APPIMAGE_PATH="$DIST_DIR/$APPIMAGE_NAME"

echo "▶ Создание AppImage для $APP_NAME v$VERSION"

# Проверяем наличие бинарника
if [ ! -f "$DIST_DIR/$APP_NAME" ]; then
    echo "✗ Не найден: $DIST_DIR/$APP_NAME"
    echo "Сначала запустите: python scripts/build.py"
    exit 1
fi

# Скачиваем appimagetool если нет
APPIMAGETOOL="$PROJECT_ROOT/tools/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    mkdir -p "$PROJECT_ROOT/tools"
    echo "▶ Скачивание appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Создаём AppDir
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$APPDIR/usr/lib"

# Копируем бинарник
cp "$DIST_DIR/$APP_NAME" "$APPDIR/usr/bin/"
chmod +x "$APPDIR/usr/bin/$APP_NAME"

# Создаём .desktop файл
cat > "$APPDIR/usr/share/applications/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=Code Aggregator
Exec=$APP_NAME
Icon=$APP_NAME
Type=Application
Categories=Development;Utility;
Comment=Aggregate code files into a single document
EOF

# Симлинк .desktop в корень AppDir
ln -s "usr/share/applications/$APP_NAME.desktop" "$APPDIR/$APP_NAME.desktop"

# Копируем иконку
cp "$PROJECT_ROOT/assets/icons/icon.png" "$APPDIR/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"
ln -s "usr/share/icons/hicolor/512x512/apps/$APP_NAME.png" "$APPDIR/$APP_NAME.png"

# Создаём AppRun
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
EXEC="${HERE}/usr/bin/CodeAggregator"
exec "${EXEC}" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Собираем AppImage
echo "▶ Сборка AppImage..."
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_PATH"

# Очистка
rm -rf "$APPDIR"

echo "✓ AppImage создан: $APPIMAGE_PATH"
ls -lh "$APPIMAGE_PATH"