import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(src_dir))

import customtkinter as ctk
from gui.app import App

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    ctk.set_widget_scaling(1.25)  # ← ДОБАВЬ ЭТУ СТРОКУ
    
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()