import customtkinter as ctk
from tkinter import filedialog


class ProjectSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, project, on_save=None):
        super().__init__(parent)
        self.project = project
        self.on_save = on_save
        self.result = False

        self.title("Настройки проекта")
        self.geometry("500x580")
        self.resizable(False, False)
        self.grab_set()

        self._build()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(form, text="Название", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(form, width=400)
        self.name_entry.insert(0, self.project.name)
        self.name_entry.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(form, text="Описание", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.desc_entry = ctk.CTkTextbox(form, width=400, height=60)
        self.desc_entry.insert("1.0", self.project.description)
        self.desc_entry.pack(anchor="w", pady=(0, 10))

        self.auto_backup_var = ctk.BooleanVar(
            value=getattr(self.project, "auto_backup_enabled", True)
        )
        ctk.CTkCheckBox(
            form,
            text="Автоматический бекап включён",
            variable=self.auto_backup_var,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=(10, 5))

        interval_frame = ctk.CTkFrame(form, fg_color="transparent")
        interval_frame.pack(anchor="w", pady=5)

        ctk.CTkLabel(
            interval_frame, text="Интервал (сек):", font=ctk.CTkFont(size=11)
        ).pack(side="left")
        self.interval_entry = ctk.CTkEntry(interval_frame, width=80)
        self.interval_entry.insert(0, str(self.project.auto_backup_interval))
        self.interval_entry.pack(side="left", padx=5)

        ctk.CTkLabel(
            interval_frame, text="Макс. автобекапов:", font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(15, 0))
        self.max_backups_entry = ctk.CTkEntry(interval_frame, width=60)
        self.max_backups_entry.insert(0, str(self.project.max_auto_backups))
        self.max_backups_entry.pack(side="left", padx=5)

        ctk.CTkLabel(
            form,
            text="Чувствительность прокрутки (пикселей):",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", pady=(10, 2))
        self.scroll_entry = ctk.CTkEntry(form, width=80)
        self.scroll_entry.insert(0, str(getattr(self.project, "scroll_speed", 6)))
        self.scroll_entry.pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            form, text="Путь к выходному файлу", font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(10, 2))
        out_frame = ctk.CTkFrame(form, fg_color="transparent")
        out_frame.pack(anchor="w", pady=(0, 10))
        self.out_entry = ctk.CTkEntry(out_frame, width=320)
        self.out_entry.insert(0, self.project.output_path)
        self.out_entry.pack(side="left")
        ctk.CTkButton(
            out_frame, text="Обзор", width=60, command=self._browse_output
        ).pack(side="left", padx=5)

        ctk.CTkLabel(form, text="Папка бекапов", font=ctk.CTkFont(size=12)).pack(
            anchor="w", pady=(10, 2)
        )
        backup_frame = ctk.CTkFrame(form, fg_color="transparent")
        backup_frame.pack(anchor="w", pady=(0, 10))
        self.backup_entry = ctk.CTkEntry(backup_frame, width=320)
        self.backup_entry.insert(0, self.project.backup_dir)
        self.backup_entry.pack(side="left")
        ctk.CTkButton(
            backup_frame, text="Обзор", width=60, command=self._browse_backup
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            form, text="Сообщение Git Push по умолчанию", font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(10, 2))
        self.git_msg_entry = ctk.CTkEntry(form, width=400)
        self.git_msg_entry.insert(
            0,
            getattr(
                self.project,
                "default_git_message",
                "update: changes from Code Aggregator",
            ),
        )
        self.git_msg_entry.pack(anchor="w", pady=(0, 10))

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13),
            command=self._save,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Отмена", font=ctk.CTkFont(size=13), command=self._cancel
        ).pack(side="left", padx=5)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, path)

    def _browse_backup(self):
        path = filedialog.askdirectory()
        if path:
            self.backup_entry.delete(0, "end")
            self.backup_entry.insert(0, path)

    def _save(self):
        # Фикс TclError: снимаем фокус и grab перед уничтожением
        self.master.focus_set()
        self.grab_release()

        self.project.name = self.name_entry.get()
        self.project.description = self.desc_entry.get("1.0", "end-1c")
        self.project.auto_backup_enabled = self.auto_backup_var.get()
        try:
            self.project.auto_backup_interval = int(self.interval_entry.get())
        except ValueError:
            pass
        try:
            self.project.max_auto_backups = int(self.max_backups_entry.get())
        except ValueError:
            pass
        try:
            self.project.scroll_speed = int(self.scroll_entry.get())
        except ValueError:
            pass
        self.project.output_path = self.out_entry.get()
        self.project.backup_dir = self.backup_entry.get()
        self.project.default_git_message = self.git_msg_entry.get()

        from core.project_manager import ProjectManager

        pm = ProjectManager()
        pm.save(self.project)

        self.result = True
        if self.on_save:
            self.on_save(self.project)
        self.destroy()

    def _cancel(self):
        self.master.focus_set()
        self.grab_release()
        self.destroy()
