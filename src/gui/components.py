import customtkinter as ctk


class Toast(ctk.CTkToplevel):
    def __init__(self, parent, message, duration=3000):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
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
        self.grab_release()
        self.master.focus_set()
        self.result = False
        self.destroy()

    def _confirm(self):
        self.grab_release()
        self.master.focus_set()
        self.result = True
        self.destroy()


class Tooltip:
    """Универсальный тултип для любого виджета customtkinter/tkinter."""

    def __init__(self, widget, text="", delay=500, wrap=350):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wrap = wrap
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)

    def set_text(self, text):
        self.text = text

    def _on_enter(self, event=None):
        self.id = self.widget.after(self.delay, self._show)

    def _on_leave(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self._hide()

    def _show(self):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tipwindow = ctk.CTkToplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        self.tipwindow.attributes("-topmost", True)
        self.tipwindow.configure(fg_color="#2d2d30")

        frame = ctk.CTkFrame(self.tipwindow, fg_color="#2d2d30", corner_radius=6)
        frame.pack(padx=1, pady=1)

        label = ctk.CTkLabel(
            frame,
            text=self.text,
            font=ctk.CTkFont(size=11),
            text_color="#cccccc",
            wraplength=self.wrap,
            justify="left",
        )
        label.pack(padx=10, pady=6)

        self.tipwindow.update_idletasks()
        tw = self.tipwindow.winfo_width()
        th = self.tipwindow.winfo_height()
        sw = self.widget.winfo_screenwidth()
        sh = self.widget.winfo_screenheight()

        if x + tw > sw:
            x = sw - tw - 10
        if y + th > sh:
            y = self.widget.winfo_rooty() - th - 5

        self.tipwindow.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class ProgressStatusBar(ctk.CTkFrame):
    """Статус-бар с интегрированным прогресс-баром."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#252526", height=32, **kwargs)
        self.pack_propagate(False)

        self.label = ctk.CTkLabel(
            self, text="Готов", font=ctk.CTkFont(size=11), text_color="#858585"
        )
        self.label.pack(side="left", padx=15, pady=4)

        self.progress = ctk.CTkProgressBar(
            self,
            width=150,
            height=8,
            fg_color="#3e3e42",
            progress_color="#007acc",
            border_width=0,
        )
        self.progress.set(0)
        self._progress_visible = False

    def set(self, text, color="#858585"):
        self.label.configure(text=text, text_color=color)

    def show_progress(self, value=0.3):
        if not self._progress_visible:
            self.progress.pack(side="right", padx=15, pady=4)
            self._progress_visible = True
        self.progress.set(value)

    def set_progress(self, value):
        self.progress.set(value)

    def hide_progress(self):
        if self._progress_visible:
            self.progress.pack_forget()
            self._progress_visible = False
            self.progress.set(0)
