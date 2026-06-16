import customtkinter as ctk


class Toast(ctk.CTkToplevel):
    def __init__(self, parent, message, duration=3000):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Убираем фон окна через tk, не через CTk
        self.configure(fg_color="#007acc")

        ctk.CTkLabel(
            self, text=message, text_color="white", font=ctk.CTkFont(size=12)
        ).pack(padx=16, pady=8)

        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()

        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()

        x = px + (pw - w) // 2
        y = py + ph - h - 50

        self.geometry(f"{w}x{h}+{x}+{y}")
        self.after(duration, self.destroy)


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Подтверждение", message="Вы уверены?"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.grab_set()

        self.result = False

        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14)).pack(pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Отмена", width=100, command=self._cancel).pack(
            side="left", padx=10
        )
        ctk.CTkButton(
            btn_frame,
            text="Да",
            width=100,
            fg_color="#c75450",
            hover_color="#a0403c",
            command=self._confirm,
        ).pack(side="left", padx=10)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        self.geometry(f"+{x}+{y}")

    def _cancel(self):
        self.result = False
        self.destroy()

    def _confirm(self):
        self.result = True
        self.destroy()
