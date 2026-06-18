#!/usr/bin/env python3
"""
Универсальный скрипт сборки для PyInstaller.
Запускается на Windows, macOS и Linux.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
ICON_SOURCE = PROJECT_ROOT / "assets" / "icon_source.png"

GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"


def print_step(msg):
    print(f"\n{BLUE}▶ {msg}{RESET}")


def print_ok(msg):
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")


def ensure_icon():
    """Генерирует иконку нужного формата для текущей ОС."""
    if not ICON_SOURCE.exists():
        print_error(f"Иконка не найдена: {ICON_SOURCE}")
        print("Создайте assets/icon_source.png (512x512, PNG)")
        sys.exit(1)

    icon_dir = PROJECT_ROOT / "assets" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)

    system = sys.platform

    if system == "win32":
        try:
            from PIL import Image

            img = Image.open(ICON_SOURCE)
            icon_path = icon_dir / "icon.ico"
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(icon_path, format="ICO", sizes=sizes)
            print_ok(f"Иконка Windows: {icon_path}")
            return icon_path
        except ImportError:
            print_error("Pillow не установлен, нельзя создать .ico")
            return None

    elif system == "darwin":
        try:
            icon_path = icon_dir / "icon.icns"
            temp_dir = icon_dir / "icon.iconset"
            temp_dir.mkdir(exist_ok=True)

            sizes = [16, 32, 64, 128, 256, 512]
            for size in sizes:
                subprocess.run(
                    [
                        "sips",
                        "-z",
                        str(size),
                        str(size),
                        str(ICON_SOURCE),
                        "--out",
                        str(temp_dir / f"icon_{size}x{size}.png"),
                    ],
                    check=True,
                    capture_output=True,
                )
                if size <= 256:
                    subprocess.run(
                        [
                            "sips",
                            "-z",
                            str(size * 2),
                            str(size * 2),
                            str(ICON_SOURCE),
                            "--out",
                            str(temp_dir / f"icon_{size}x{size}@2x.png"),
                        ],
                        check=True,
                        capture_output=True,
                    )

            subprocess.run(
                ["iconutil", "-c", "icns", str(temp_dir), "-o", str(icon_path)],
                check=True,
            )
            shutil.rmtree(temp_dir)
            print_ok(f"Иконка macOS: {icon_path}")
            return icon_path
        except Exception as e:
            print_error(f"Не удалось создать .icns: {e}")
            return None

    else:
        icon_path = icon_dir / "icon.png"
        shutil.copy2(ICON_SOURCE, icon_path)
        print_ok(f"Иконка Linux: {icon_path}")
        return icon_path


def build():
    print_step("Очистка старых сборок...")
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print_ok(f"Удалена папка: {d}")

    print_step("Подготовка иконки...")
    icon_path = ensure_icon()

    print_step("Сборка PyInstaller...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        "CodeAggregator",
        "--add-data",
        f"{SRC_DIR}{os.pathsep}src",
        "--clean",
        "--noconfirm",
    ]

    if icon_path and icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        # Копируем иконку рядом с .exe для main.py
        cmd.extend(["--add-data", f"{icon_path}{os.pathsep}."])

    if sys.platform == "darwin":
        cmd.extend(
            [
                "--osx-bundle-identifier",
                "com.codeaggregator.app",
            ]
        )

    cmd.append(str(SRC_DIR / "main.py"))

    print(f"Команда: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print_error("Сборка PyInstaller провалена")
        sys.exit(1)

    print_ok("Сборка завершена")

    # Проверка
    if sys.platform == "win32":
        exe_name = "CodeAggregator.exe"
    elif sys.platform == "darwin":
        exe_name = "CodeAggregator.app"
    else:
        exe_name = "CodeAggregator"

    print_step(f"Проверка результата: {DIST_DIR / exe_name}")
    if (DIST_DIR / exe_name).exists():
        print_ok("Исполняемый файл создан")
    else:
        print_error("Исполняемый файл не найден!")
        sys.exit(1)


if __name__ == "__main__":
    build()
