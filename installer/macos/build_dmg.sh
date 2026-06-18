#!/bin/bash
set -e

APP_NAME="CodeAggregator"
VERSION="1.0.0"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
DMG_NAME="$APP_NAME-$VERSION.dmg"
DMG_PATH="$DIST_DIR/$DMG_NAME"

echo "▶ Создание DMG для $APP_NAME v$VERSION"

# Проверяем наличие .app
if [ ! -d "$APP_BUNDLE" ]; then
    echo "✗ Не найден: $APP_BUNDLE"
    echo "Сначала запустите: python scripts/build.py"
    exit 1
fi

# Очистка
rm -f "$DMG_PATH"

# Временная папка для DMG
TMP_DIR=$(mktemp -d)
cp -R "$APP_BUNDLE" "$TMP_DIR/"

# Создаём символическую ссылку на Applications
ln -s /Applications "$TMP_DIR/Applications"

# Создаём DMG
create-dmg \
    --volname "$APP_NAME $VERSION" \
    --volicon "$PROJECT_ROOT/assets/icons/icon.icns" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 150 200 \
    --icon "Applications" 450 200 \
    --hide-extension "$APP_NAME.app" \
    --app-drop-link 450 200 \
    --no-internet-enable \
    "$DMG_PATH" \
    "$TMP_DIR"

# Очистка
rm -rf "$TMP_DIR"

echo "✓ DMG создан: $DMG_PATH"
ls -lh "$DMG_PATH"