# Руководство по релизу

## Подготовка

1. Убедись, что `assets/icon_source.png` существует (512×512 PNG)
2. Обнови версию в:
   - `installer/windows/installer.iss` (строка `#define MyAppVersion`)
   - `installer/macos/build_dmg.sh` (переменная `VERSION`)
   - `installer/linux/build_appimage.sh` (переменная `VERSION`)
   - `CHANGELOG.md`

## Создание релиза

### Автоматически (GitHub Actions)

```bash
# Закоммить все изменения
git add .
git commit -m "release: v1.0.0"

# Создай и запушь тег
git tag v1.0.0
git push origin main
git push origin v1.0.0