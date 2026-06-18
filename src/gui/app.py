import os
import customtkinter as ctk
from gui.project_editor import ProjectEditor
from gui.components import Toast, ConfirmDialog, ProgressStatusBar, Tooltip
from core.project_manager import ProjectManager, Source
from core.auto_backup import AutoBackupThread


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Code Aggregator")
        self.geometry("1200x800")
        self.minsize(1000, 700)

        self.update_idletasks()
        w, h = 1200, 800
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.pm = ProjectManager()
        self.current_project = None
        self.backup_thread = None
        self._project_map = {}

        os.makedirs("projects-data", exist_ok=True)

        # === ТУЛБАР ===
        self.toolbar = ctk.CTkFrame(self, fg_color="#252526", height=44)
        self.toolbar.pack_propagate(False)
        self.toolbar.pack(fill="x", side="top")

        self.project_selector = ctk.CTkOptionMenu(
            self.toolbar,
            values=[],
            width=240,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            command=self._on_project_selected,
        )
        self.project_selector.pack(side="left", padx=15, pady=5)
        Tooltip(
            self.project_selector,
            "Выберите проект. Описание отображается при наведении.",
            delay=300,
        )

        self._selector_tooltip = Tooltip(self.project_selector, "", delay=300)

        btn_add = ctk.CTkButton(
            self.toolbar,
            text="+",
            width=32,
            height=32,
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._on_create,
        )
        btn_add.pack(side="left", padx=5)
        Tooltip(btn_add, "Создать новый проект", delay=300)

        btn_del = ctk.CTkButton(
            self.toolbar,
            text="🗑",
            width=32,
            height=32,
            fg_color="transparent",
            text_color="#858585",
            hover_color="#c75450",
            font=ctk.CTkFont(size=14),
            command=self._on_delete_current,
        )
        btn_del.pack(side="left", padx=5)
        Tooltip(btn_del, "Удалить текущий проект", delay=300)

        # Тонкая линия-разделитель (1px)
        ctk.CTkFrame(self, height=1, fg_color="#3e3e42").pack(fill="x")
        # ==============

        # Контент
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        self.editor = ProjectEditor(
            self.content,
            status_callback=self._set_status,
            progress_callback=self._progress_callback,
        )
        self.editor.pack(fill="both", expand=True)

        # Статус-бар с прогрессом
        self.status_bar = ProgressStatusBar(self.content)
        self.status_bar.pack(side="bottom", fill="x")

        self._refresh_selector()

        last_id = self.pm.config.get("last_project_id")
        if last_id:
            project = self.pm.load(last_id)
            if project:
                self._open_project(project)

    def _refresh_selector(self):
        projects = self.pm.list_all()
        self._project_map = {p.name: p.id for p in projects}
        names = list(self._project_map.keys())
        self.project_selector.configure(values=names or ["Нет проектов"])
        if self.current_project:
            self.project_selector.set(self.current_project.name)
        elif names:
            self.project_selector.set(names[0])
        else:
            self.project_selector.set("Нет проектов")

    def _on_project_selected(self, name):
        if name in self._project_map:
            project = self.pm.load(self._project_map[name])
            if project:
                self._open_project(project)

    def _set_status(self, text, color="#858585"):
        if hasattr(self, "status_bar") and self.status_bar.winfo_exists():
            self.status_bar.set(text, color)

    def _progress_callback(self, action, value=None):
        """Управление прогресс-баром из дочерних компонентов."""
        if not hasattr(self, "status_bar"):
            return
        if action == "show":
            self.status_bar.show_progress(value if value is not None else 0.3)
        elif action == "set":
            self.status_bar.set_progress(value if value is not None else 0.5)
        elif action == "hide":
            self.status_bar.hide_progress()

    def _start_backup_thread(self, project):
        if self.backup_thread:
            self.backup_thread.stop()
            self.backup_thread = None

        if (
            project
            and getattr(project, "auto_backup_enabled", True)
            and project.output_path
        ):
            self.backup_thread = AutoBackupThread(
                project=project,
                interval=project.auto_backup_interval,
                callback=self._on_auto_backup,
            )
            self.backup_thread.start()

    def _on_auto_backup(self, result):
        def update():
            if not self.winfo_exists():
                return
            self._show_toast(f"🕐 Автобекап: {result['name']}")
            self._set_status(f"Автобекап создан: {result['name']}", "#4ec9b0")
            if hasattr(self.editor, "refresh_backups_list"):
                self.editor.refresh_backups_list()

        self.after(0, update)

    def _open_project(self, project):
        if self.backup_thread:
            self.backup_thread.stop()
            self.backup_thread = None

        self.current_project = project
        self.pm.config.set("last_project_id", project.id)

        desc = getattr(project, "description", "") or "Нет описания"
        self._selector_tooltip.set_text(f"{project.name}\n{desc}")

        self.editor.destroy()
        self.editor = ProjectEditor(
            self.content,
            project=project,
            on_save=self._on_save,
            status_callback=self._set_status,
            progress_callback=self._progress_callback,
        )
        self.editor.pack(fill="both", expand=True)

        self._start_backup_thread(project)
        self._set_status(f"Проект «{project.name}» открыт")
        self.project_selector.set(project.name)

    def _on_create(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Новый проект")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        dialog.grab_set()

        from gui.utils import setup_clipboard

        ctk.CTkLabel(
            dialog,
            text="Создание нового проекта",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(20, 15))

        ctk.CTkLabel(dialog, text="Название проекта *", font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=30
        )
        name_entry = ctk.CTkEntry(dialog, width=440)
        name_entry.pack(pady=(0, 10), padx=30)
        setup_clipboard(name_entry)
        Tooltip(name_entry, "Введите уникальное название проекта", delay=400)

        ctk.CTkLabel(
            dialog, text="Папка с исходниками", font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30)
        dir_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        dir_frame.pack(pady=(0, 15), padx=30, fill="x")

        dir_entry = ctk.CTkEntry(dir_frame, width=360)
        dir_entry.pack(side="left", fill="x", expand=True)
        setup_clipboard(dir_entry)
        Tooltip(dir_entry, "Путь к корневой папке проекта", delay=400)

        def browse():
            path = ctk.filedialog.askdirectory()
            if path:
                dir_entry.delete(0, "end")
                dir_entry.insert(0, path)

        btn_browse = ctk.CTkButton(dir_frame, text="📁 Обзор", width=80, command=browse)
        btn_browse.pack(side="right", padx=(10, 0))
        Tooltip(btn_browse, "Выбрать папку через проводник", delay=400)

        create_btn = ctk.CTkButton(
            dialog,
            text="Создать проект",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13),
            width=200,
            state="disabled",
        )
        create_btn.pack(pady=10)

        def validate():
            if name_entry.get().strip():
                create_btn.configure(state="normal")
            else:
                create_btn.configure(state="disabled")

        name_entry.bind("<KeyRelease>", lambda e: validate())

        def create():
            name = name_entry.get().strip()
            path = dir_entry.get().strip()
            if not name:
                return

            data_dir = os.path.join("projects-data", name)
            os.makedirs(data_dir, exist_ok=True)

            sources = []
            if path:
                sources.append(
                    Source(
                        type="directory",
                        path=path,
                        recursive=True,
                        exclude=[
                            "node_modules",
                            ".git",
                            "__pycache__",
                            "build",
                            ".gradle",
                            ".idea",
                        ],
                    )
                )

            project = self.pm.create(
                name=name,
                sources=sources,
                extensions=[
                    ".js",
                    ".jsx",
                    ".ts",
                    ".tsx",
                    ".py",
                    ".kt",
                    ".xml",
                    ".java",
                    ".gradle",
                    ".dart",
                ],
                output_path=os.path.join(data_dir, "output.txt"),
                backup_dir=os.path.join(data_dir, "backups"),
            )

            dialog.destroy()
            self._refresh_selector()
            self._open_project(project)
            self._show_toast(f"Проект «{name}» создан")

        create_btn.configure(command=create)

        ctk.CTkButton(
            dialog,
            text="Отмена",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="#858585",
            hover_color="#2a2d2e",
            command=dialog.destroy,
        ).pack(pady=5)

        dialog.update_idletasks()
        dx = self.winfo_x() + (self.winfo_width() - 500) // 2
        dy = self.winfo_y() + (self.winfo_height() - 350) // 2
        dialog.geometry(f"+{dx}+{dy}")

    def _on_delete_current(self):
        if not self.current_project:
            self._set_status("Нет открытого проекта", "#c75450")
            return

        dialog = ConfirmDialog(
            self, message=f"Удалить проект «{self.current_project.name}»?"
        )
        self.wait_window(dialog)

        if dialog.result:
            if self.backup_thread:
                self.backup_thread.stop()
                self.backup_thread = None

            self.pm.delete(self.current_project.id)
            self.current_project = None
            self.editor.destroy()
            self.editor = ProjectEditor(
                self.content,
                status_callback=self._set_status,
                progress_callback=self._progress_callback,
            )
            self.editor.pack(fill="both", expand=True)

            self._refresh_selector()
            self._show_toast("Проект удалён")
            self._set_status("Проект удалён")

    def _on_save(self, project):
        self._show_toast(f"Проект «{project.name}» сохранён")
        self._set_status("Проект сохранён", "#4ec9b0")
        self._refresh_selector()
        if self.backup_thread:
            self.backup_thread.stop()
            self.backup_thread = None
        self._start_backup_thread(project)

    def _show_toast(self, message):
        Toast(self, message)

    def destroy(self):
        if self.backup_thread:
            self.backup_thread.stop()
        super().destroy()
