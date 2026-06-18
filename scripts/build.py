#!/usr/bin/env python3
"""
Universal build script for PyInstaller.
Runs on Windows, macOS and Linux.
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


def log(msg):
    print(f"[BUILD] {msg}")


def ensure_icon():
    """Generate icon in proper format for current OS."""
    if not ICON_SOURCE.exists():
        log(f"ERROR: Icon not found: {ICON_SOURCE}")
        log("Create assets/icon_source.png (512x512, PNG)")
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
            log(f"Windows icon: {icon_path}")
            return icon_path
        except ImportError:
            log("ERROR: Pillow not installed, cannot create .ico")
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
            log(f"macOS icon: {icon_path}")
            return icon_path
        except Exception as e:
            log(f"ERROR: Failed to create .icns: {e}")
            return None

    else:
        icon_path = icon_dir / "icon.png"
        shutil.copy2(ICON_SOURCE, icon_path)
        log(f"Linux icon: {icon_path}")
        return icon_path


def build():
    log("Cleaning old builds...")
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            log(f"Removed: {d}")

    log("Preparing icon...")
    icon_path = ensure_icon()

    log("Running PyInstaller...")

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
        cmd.extend(["--add-data", f"{icon_path}{os.pathsep}."])

    if sys.platform == "darwin":
        cmd.extend(
            [
                "--osx-bundle-identifier",
                "com.codeaggregator.app",
            ]
        )

    cmd.append(str(SRC_DIR / "main.py"))

    log(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        log("ERROR: PyInstaller build failed")
        sys.exit(1)

    log("Build completed")

    if sys.platform == "win32":
        exe_name = "CodeAggregator.exe"
    elif sys.platform == "darwin":
        exe_name = "CodeAggregator.app"
    else:
        exe_name = "CodeAggregator"

    log(f"Checking result: {DIST_DIR / exe_name}")
    if (DIST_DIR / exe_name).exists():
        log("SUCCESS: Executable created")
    else:
        log("ERROR: Executable not found!")
        sys.exit(1)


if __name__ == "__main__":
    build()
