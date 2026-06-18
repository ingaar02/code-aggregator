import sys
import os
from pathlib import Path

src_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(src_dir))

import customtkinter as ctk
from gui.app import App


def get_icon_path():
    """Находит иконку для окна приложения."""
    # В разработке — рядом с src
    dev_icon = src_dir.parent / "assets" / "icons" / "icon.ico"
    if dev_icon.exists():
        return str(dev_icon)

    # В собранном .exe — рядом с .exe файлом
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        bundled_icon = exe_dir / "icon.ico"
        if bundled_icon.exists():
            return str(bundled_icon)

    return None


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    ctk.set_widget_scaling(1.25)

    app = App()

    # Устанавливаем иконку окна (панель задач, заголовок, Alt+Tab)
    icon_path = get_icon_path()
    if icon_path and os.path.exists(icon_path):
        try:
            app.iconbitmap(icon_path)  # Windows
        except Exception:
            pass
        try:
            # Для Linux/macOS используем PhotoImage
            from PIL import Image, ImageTk

            img = Image.open(icon_path)
            photo = ImageTk.PhotoImage(img)
            app.iconphoto(True, photo)
            app._icon_photo = photo  # держим ссылку, иначе GC уничтожит
        except Exception:
            pass

    app.mainloop()


if __name__ == "__main__":
    main()
