import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from PIL import Image
from gui.utils import setup_clipboard
from gui.components import Tooltip


class ProjectSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, project, on_save=None):
        super().__init__(parent)
        self.project = project
        self.on_save = on_save
        self.result = False
        self._icon_image = None
        self._pending_icon_path = None

        self.title("Настройки проекта")
        self.geometry("600x750")
        self.resizable(False, False)
        self.grab_set()

        self._build()

        self.update_idletasks()
        toplevel = parent.winfo_toplevel()
        x = toplevel.winfo_x() + (toplevel.winfo_width() - 600) // 2
        y = toplevel.winfo_y() + (toplevel.winfo_height() - 750) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack_propagate(False)
        header.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(
            header,
            text="⚙️ Настройки проекта",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", pady=5)

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=10)
        form._parent_canvas.configure(yscrollincrement=6)

        # === ИКОНКА ===
        ctk.CTkLabel(
            form, text="Иконка проекта", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        icon_frame = ctk.CTkFrame(form, fg_color="transparent")
        icon_frame.pack(anchor="w", pady=5, fill="x")

        self.icon_preview = ctk.CTkLabel(
            icon_frame,
            text="",
            width=80,
            height=80,
            fg_color="#2d2d30",
            corner_radius=8,
        )
        self.icon_preview.pack(side="left", padx=(0, 10))
        self._update_icon_preview()

        icon_right = ctk.CTkFrame(icon_frame, fg_color="transparent")
        icon_right.pack(side="left", fill="both", expand=True)

        btn_load = ctk.CTkButton(
            icon_right, text="📁 Загрузить...", width=140, command=self._load_icon
        )
        btn_load.pack(anchor="w", pady=(0, 5))
        Tooltip(btn_load, "Выбрать изображение любого формата", delay=400)

        ctk.CTkLabel(
            icon_right,
            text="Квадрат, любой формат. Обрежется и сожмётся до 512×512.",
            font=ctk.CTkFont(size=10),
            text_color="#858585",
            wraplength=380,
            justify="left",
        ).pack(anchor="w")
        # ==============

        ctk.CTkLabel(
            form, text="Название", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(15, 2))
        self.name_entry = ctk.CTkEntry(form, width=520)
        self.name_entry.insert(0, self.project.name)
        self.name_entry.pack(anchor="w", pady=(0, 10), fill="x")
        setup_clipboard(self.name_entry)
        Tooltip(
            self.name_entry,
            "Название проекта. При смене старое имя сохранится в алиасы.",
            delay=400,
        )

        aliases = getattr(self.project, "aliases", [])
        if aliases:
            ctk.CTkLabel(
                form,
                text="Прошлые названия:",
                font=ctk.CTkFont(size=10),
                text_color="#858585",
            ).pack(anchor="w")
            ctk.CTkLabel(
                form,
                text=", ".join(aliases),
                font=ctk.CTkFont(size=10),
                text_color="#555555",
                wraplength=520,
                justify="left",
            ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            form, text="Описание", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 2))
        self.desc_entry = ctk.CTkTextbox(form, width=520, height=70)
        self.desc_entry.insert("1.0", self.project.description)
        self.desc_entry.pack(anchor="w", pady=(0, 10), fill="x")
        setup_clipboard(self.desc_entry)
        Tooltip(
            self.desc_entry,
            "Описание проекта. Отображается в тултипе при наведении на проект.",
            delay=400,
        )

        self.auto_backup_var = ctk.BooleanVar(
            value=getattr(self.project, "auto_backup_enabled", True)
        )
        cb = ctk.CTkCheckBox(
            form,
            text="Автоматический бекап включён",
            variable=self.auto_backup_var,
            font=ctk.CTkFont(size=12),
        )
        cb.pack(anchor="w", pady=5)
        Tooltip(
            cb,
            "Автоматически создавать бекап при изменении выходного файла",
            delay=400,
        )

        interval_frame = ctk.CTkFrame(form, fg_color="transparent")
        interval_frame.pack(anchor="w", pady=5, fill="x")

        ctk.CTkLabel(
            interval_frame, text="Интервал (сек):", font=ctk.CTkFont(size=11)
        ).pack(side="left")
        self.interval_entry = ctk.CTkEntry(interval_frame, width=100)
        self.interval_entry.insert(0, str(self.project.auto_backup_interval))
        self.interval_entry.pack(side="left", padx=10)
        setup_clipboard(self.interval_entry)
        Tooltip(
            self.interval_entry,
            "Интервал проверки изменений (в секундах)",
            delay=400,
        )

        ctk.CTkLabel(
            interval_frame, text="Макс. автобекапов:", font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(20, 0))
        self.max_backups_entry = ctk.CTkEntry(interval_frame, width=80)
        self.max_backups_entry.insert(0, str(self.project.max_auto_backups))
        self.max_backups_entry.pack(side="left", padx=10)
        setup_clipboard(self.max_backups_entry)
        Tooltip(
            self.max_backups_entry,
            "Максимум автоматических бекапов (старые удаляются)",
            delay=400,
        )

        ctk.CTkLabel(
            form, text="Интерфейс", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        scroll_frame = ctk.CTkFrame(form, fg_color="transparent")
        scroll_frame.pack(anchor="w", pady=5, fill="x")
        ctk.CTkLabel(
            scroll_frame,
            text="Чувствительность прокрутки (пикселей):",
            font=ctk.CTkFont(size=11),
        ).pack(side="left")
        self.scroll_entry = ctk.CTkEntry(scroll_frame, width=80)
        self.scroll_entry.insert(0, str(getattr(self.project, "scroll_speed", 6)))
        self.scroll_entry.pack(side="left", padx=10)
        setup_clipboard(self.scroll_entry)
        Tooltip(
            self.scroll_entry,
            "Шаг прокрутки колёсиком мыши в списках",
            delay=400,
        )

        ctk.CTkLabel(
            form,
            text="Путь к выходному файлу",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(15, 2))
        out_frame = ctk.CTkFrame(form, fg_color="transparent")
        out_frame.pack(anchor="w", pady=(0, 10), fill="x")
        self.out_entry = ctk.CTkEntry(out_frame, width=440)
        self.out_entry.insert(0, self.project.output_path)
        self.out_entry.pack(side="left", fill="x", expand=True)
        setup_clipboard(self.out_entry)
        Tooltip(self.out_entry, "Куда сохранять собранный результат", delay=400)

        btn_out = ctk.CTkButton(
            out_frame, text="📁 Обзор", width=90, command=self._browse_output
        )
        btn_out.pack(side="right", padx=5)
        Tooltip(btn_out, "Выбрать файл через проводник", delay=400)

        ctk.CTkLabel(
            form, text="Папка бекапов", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 2))
        backup_frame = ctk.CTkFrame(form, fg_color="transparent")
        backup_frame.pack(anchor="w", pady=(0, 10), fill="x")
        self.backup_entry = ctk.CTkEntry(backup_frame, width=440)
        self.backup_entry.insert(0, self.project.backup_dir)
        self.backup_entry.pack(side="left", fill="x", expand=True)
        setup_clipboard(self.backup_entry)
        Tooltip(
            self.backup_entry,
            "Где хранить автоматические и ручные бекапы",
            delay=400,
        )

        btn_backup = ctk.CTkButton(
            backup_frame, text="📁 Обзор", width=90, command=self._browse_backup
        )
        btn_backup.pack(side="right", padx=5)
        Tooltip(btn_backup, "Выбрать папку через проводник", delay=400)

        ctk.CTkLabel(form, text="Git", font=ctk.CTkFont(size=12, weight="bold")).pack(
            anchor="w", pady=(15, 2)
        )
        ctk.CTkLabel(
            form, text="Сообщение коммита по умолчанию:", font=ctk.CTkFont(size=11)
        ).pack(anchor="w")
        self.git_msg_entry = ctk.CTkEntry(form, width=520)
        self.git_msg_entry.insert(
            0,
            getattr(
                self.project,
                "default_git_message",
                "update: changes from Code Aggregator",
            ),
        )
        self.git_msg_entry.pack(anchor="w", pady=(0, 10), fill="x")
        setup_clipboard(self.git_msg_entry)
        Tooltip(
            self.git_msg_entry,
            "Шаблон сообщения для git commit",
            delay=400,
        )

        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        btn_frame.pack_propagate(False)
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=15)

        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13),
            width=120,
            command=self._save,
        )
        btn_save.pack(side="right", padx=5)
        Tooltip(btn_save, "Сохранить все изменения", delay=400)

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Отмена",
            font=ctk.CTkFont(size=13),
            width=100,
            command=self._cancel,
        )
        btn_cancel.pack(side="right", padx=5)
        Tooltip(btn_cancel, "Закрыть без сохранения", delay=400)

    def _update_icon_preview(self):
        if self.project.icon_path and Path(self.project.icon_path).exists():
            try:
                img = Image.open(self.project.icon_path)
                self._icon_image = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(80, 80)
                )
                self.icon_preview.configure(image=self._icon_image, text="")
            except Exception:
                self.icon_preview.configure(text="🖼️", font=ctk.CTkFont(size=30))
        else:
            self.icon_preview.configure(text="🖼️", font=ctk.CTkFont(size=30))

    def _load_icon(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.ico")]
        )
        if path:
            self._pending_icon_path = path
            try:
                img = Image.open(path)
                self._icon_image = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(80, 80)
                )
                self.icon_preview.configure(image=self._icon_image, text="")
            except Exception:
                pass

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
        self.grab_release()
        self.master.focus_set()

        old_name = self.project.name
        new_name = self.name_entry.get().strip()
        if (
            old_name
            and old_name != new_name
            and old_name not in getattr(self.project, "aliases", [])
        ):
            if not hasattr(self.project, "aliases"):
                self.project.aliases = []
            self.project.aliases.append(old_name)

        self.project.name = new_name
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

        # Обработка иконки
        if self._pending_icon_path:
            from core.icon_processor import IconProcessor

            icon_path = f"config/projects/{self.project.id}/icon.png"
            try:
                IconProcessor.process(self._pending_icon_path, icon_path, size=512)
                self.project.icon_path = icon_path
            except Exception as e:
                print(f"[Icon] Error: {e}")

        from core.project_manager import ProjectManager

        pm = ProjectManager()
        pm.save(self.project)

        self.result = True
        if self.on_save:
            self.on_save(self.project)
        self.destroy()

    def _cancel(self):
        self.grab_release()
        self.master.focus_set()
        self.destroy()
