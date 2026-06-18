import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from PIL import Image
from core.project_manager import ProjectManager, Source
from gui.utils import get_file_icon, setup_clipboard, open_file
from gui.components import ConfirmDialog, Tooltip
from gui.settings_dialog import ProjectSettingsDialog


class Chip(ctk.CTkFrame):
    def __init__(self, parent, text, on_remove, **kwargs):
        super().__init__(
            parent, fg_color="#007acc", corner_radius=12, height=28, **kwargs
        )
        self.text = text
        self.on_remove = on_remove

        ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color="white",
            anchor="center",
        ).pack(side="left", padx=(10, 2), pady=2)

        btn = ctk.CTkButton(
            self,
            text="✕",
            width=16,
            height=16,
            fg_color="transparent",
            text_color="white",
            hover_color="#c75450",
            font=ctk.CTkFont(size=10),
            command=self._remove,
        )
        btn.pack(side="left", padx=(2, 8), pady=2)
        Tooltip(btn, f"Удалить расширение {text}", delay=300)

    def _remove(self):
        self.on_remove(self.text)
        self.destroy()


class ProjectEditor(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        project=None,
        on_save=None,
        status_callback=None,
        progress_callback=None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="#1e1e1e", **kwargs)
        self.project = project
        self.on_save = on_save
        self.status_callback = status_callback
        self.progress_callback = progress_callback
        self.pm = ProjectManager()

        if not project:
            self._show_empty()
            return

        self._build_form()

    def _show_empty(self):
        label = ctk.CTkLabel(
            self,
            text="Выберите проект или создайте новый",
            font=ctk.CTkFont(size=14),
            text_color="#858585",
        )
        label.pack(expand=True)

    def _set_status(self, text, color="#858585"):
        if self.status_callback:
            self.status_callback(text, color)

    def _progress(self, action, value=None):
        if self.progress_callback:
            self.progress_callback(action, value)

    def _build_form(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Заголовок
        header = ctk.CTkFrame(self, fg_color="transparent", height=50)
        header.pack_propagate(False)
        header.pack(fill="x", padx=20, pady=(10, 0))

        # Иконка проекта
        self._header_icon = None
        if self.project.icon_path and Path(self.project.icon_path).exists():
            try:
                img = Image.open(self.project.icon_path)
                self._header_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(32, 32)
                )
                icon_lbl = ctk.CTkLabel(
                    header, image=self._header_icon, text="", width=32, height=32
                )
                icon_lbl.pack(side="left", padx=(0, 10))
                Tooltip(icon_lbl, "Иконка проекта", delay=400)
            except Exception:
                pass

        self.header_name = ctk.CTkLabel(
            header, text=self.project.name, font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_name.pack(side="left")
        Tooltip(
            self.header_name,
            f"ID: {self.project.id}\n{self.project.description or 'Нет описания'}",
            delay=400,
            wrap=400,
        )

        stack_lbl = ctk.CTkLabel(
            header,
            text=f"  •  {self.project.stack_detected}",
            font=ctk.CTkFont(size=12),
            text_color="#858585",
        )
        stack_lbl.pack(side="left", padx=5)
        Tooltip(stack_lbl, "Автоопределённый стек технологий", delay=400)

        btn_settings = ctk.CTkButton(
            header,
            text="⚙️",
            width=32,
            height=32,
            fg_color="transparent",
            text_color="#858585",
            hover_color="#2a2d2e",
            font=ctk.CTkFont(size=16),
            command=self._open_settings,
        )
        btn_settings.pack(side="right", padx=5)
        Tooltip(btn_settings, "Настройки проекта", delay=400)

        # Вкладки
        self.tabview = ctk.CTkTabview(
            self,
            fg_color="#1e1e1e",
            segmented_button_fg_color="#252526",
            segmented_button_selected_color="#007acc",
            segmented_button_selected_hover_color="#005a9e",
            segmented_button_unselected_color="#2d2d30",
            segmented_button_unselected_hover_color="#3e3e42",
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        tab_sources = self.tabview.add("📁 Источники")
        self._build_sources_tab(tab_sources)

        tab_build = self.tabview.add("🔧 Сборка и бекапы")
        self._build_build_tab(tab_build)

        tab_git = self.tabview.add("🌐 Git")
        self._build_git_tab(tab_git)

    def _build_sources_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        speed = getattr(self.project, "scroll_speed", 6)
        scroll._parent_canvas.configure(yscrollincrement=speed)

        ctk.CTkLabel(
            scroll, text="Источники", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        self.sources_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.sources_frame.pack(fill="x", pady=5)
        self._refresh_sources()

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=5)

        btn_add_dir = ctk.CTkButton(
            btn_frame, text="➕ Добавить папку", width=160, command=self._add_directory
        )
        btn_add_dir.pack(side="left", padx=5)
        Tooltip(
            btn_add_dir, "Выбрать папку с исходным кодом через проводник", delay=400
        )

        btn_add_file = ctk.CTkButton(
            btn_frame, text="➕ Добавить файл", width=160, command=self._add_file
        )
        btn_add_file.pack(side="left", padx=5)
        Tooltip(btn_add_file, "Выбрать отдельный файл через проводник", delay=400)

        ctk.CTkLabel(
            scroll, text="Расширения файлов", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        self.chips_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self.chips_container.pack(fill="x", pady=5)

        input_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        input_frame.pack(anchor="w", pady=(0, 10))

        self.ext_input = ctk.CTkEntry(
            input_frame, width=250, placeholder_text="Введите .ext и нажмите Enter"
        )
        self.ext_input.pack(side="left")
        setup_clipboard(self.ext_input)
        self.ext_input.bind("<Return>", self._on_ext_enter)
        Tooltip(
            self.ext_input,
            "Например: .py, .js, .tsx. Нажмите Enter для добавления.",
            delay=400,
        )

        ctk.CTkLabel(
            input_frame,
            text="  Нажмите Enter, чтобы добавить",
            font=ctk.CTkFont(size=10),
            text_color="#858585",
        ).pack(side="left", padx=10)

        self._extensions = (
            list(self.project.extensions)
            if self.project.extensions
            else [".js", ".jsx", ".ts", ".tsx", ".py", ".kt", ".xml"]
        )
        self._refresh_chips()

    def _build_build_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        speed = getattr(self.project, "scroll_speed", 6)
        scroll._parent_canvas.configure(yscrollincrement=speed)

        ctk.CTkLabel(
            scroll, text="Выходной файл", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        out_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        out_frame.pack(anchor="w", fill="x", pady=(0, 10))
        self.out_entry = ctk.CTkEntry(out_frame, width=400)
        self.out_entry.insert(0, self.project.output_path)
        self.out_entry.pack(side="left", fill="x", expand=True)
        Tooltip(self.out_entry, "Путь к файлу, куда будет собран результат", delay=400)

        btn_out = ctk.CTkButton(
            out_frame, text="📁 Обзор", width=90, command=self._browse_output
        )
        btn_out.pack(side="right", padx=5)
        Tooltip(btn_out, "Выбрать путь для сохранения результата", delay=400)

        ctk.CTkLabel(
            scroll, text="Действия", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(15, 5))
        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.pack(anchor="w", pady=5)

        btn_agg = ctk.CTkButton(
            actions,
            text="🔧 Собрать файлы",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._aggregate,
        )
        btn_agg.pack(side="left", padx=5)
        Tooltip(btn_agg, "Собрать все файлы в один документ", delay=400)

        btn_src = ctk.CTkButton(
            actions, text="📂 Исходники", width=120, command=self._open_sources
        )
        btn_src.pack(side="left", padx=5)
        Tooltip(btn_src, "Открыть папку с исходниками в проводнике", delay=400)

        btn_res = ctk.CTkButton(
            actions, text="📄 Результат", width=120, command=self._open_output
        )
        btn_res.pack(side="left", padx=5)
        Tooltip(btn_res, "Открыть папку с результатом в проводнике", delay=400)

        ctk.CTkLabel(
            scroll, text="Бекапы", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(20, 5))

        self.backups_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.backups_frame.pack(fill="x", pady=5)

        backup_btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        backup_btn_frame.pack(anchor="w", pady=5)

        btn_manual = ctk.CTkButton(
            backup_btn_frame,
            text="💾 Ручной бекап",
            width=160,
            command=self._create_manual_backup,
        )
        btn_manual.pack(side="left", padx=5)
        Tooltip(btn_manual, "Создать бекап вручную (сохраняется навсегда)", delay=400)

        btn_refresh = ctk.CTkButton(
            backup_btn_frame,
            text="🔄 Обновить список",
            width=160,
            command=self._refresh_backups,
        )
        btn_refresh.pack(side="left", padx=5)
        Tooltip(btn_refresh, "Обновить список бекапов", delay=400)

        self._refresh_backups()

    def _build_git_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        speed = getattr(self.project, "scroll_speed", 6)
        scroll._parent_canvas.configure(yscrollincrement=speed)

        ctk.CTkLabel(scroll, text="Git", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w", pady=(0, 5)
        )

        git_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        git_frame.pack(anchor="w", pady=10)

        btn_pull = ctk.CTkButton(
            git_frame, text="🔄 Git Pull", width=160, command=self._git_pull
        )
        btn_pull.pack(side="left", padx=5)
        Tooltip(btn_pull, "git pull из первого источника проекта", delay=400)

        btn_push = ctk.CTkButton(
            git_frame, text="⬆️ Git Push", width=160, command=self._git_push
        )
        btn_push.pack(side="left", padx=5)
        Tooltip(btn_push, "git add, commit, push с настраиваемым сообщением", delay=400)

        ctk.CTkLabel(
            scroll, text="Сообщение коммита по умолчанию:", font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=(15, 2))
        self.git_msg_display = ctk.CTkLabel(
            scroll,
            text=getattr(
                self.project,
                "default_git_message",
                "update: changes from Code Aggregator",
            ),
            font=ctk.CTkFont(size=11),
            text_color="#858585",
        )
        self.git_msg_display.pack(anchor="w")
        Tooltip(
            self.git_msg_display, "Сообщение по умолчанию для git commit", delay=400
        )

        ctk.CTkLabel(
            scroll,
            text="Измените в ⚙️ Настройках",
            font=ctk.CTkFont(size=10),
            text_color="#555555",
        ).pack(anchor="w", pady=(5, 0))

    def _refresh_chips(self):
        for widget in self.chips_container.winfo_children():
            widget.destroy()

        cols = 6
        for i, ext in enumerate(self._extensions):
            chip = Chip(self.chips_container, ext, on_remove=self._remove_ext)
            chip.grid(row=i // cols, column=i % cols, padx=4, pady=2, sticky="w")

    def _on_ext_enter(self, event=None):
        text = self.ext_input.get().strip().lower()
        if not text:
            return

        if not text.startswith("."):
            text = "." + text

        if text not in self._extensions:
            self._extensions.append(text)
            self._refresh_chips()
            self._auto_save()

        self.ext_input.delete(0, "end")

    def _remove_ext(self, ext):
        if ext in self._extensions:
            self._extensions.remove(ext)
            self._refresh_chips()
            self._auto_save()

    def _refresh_sources(self):
        for widget in self.sources_frame.winfo_children():
            widget.destroy()

        for src in self.project.sources:
            frame = ctk.CTkFrame(
                self.sources_frame, fg_color="#2a2d2e", corner_radius=6, height=48
            )
            frame.pack_propagate(False)
            frame.pack(fill="x", pady=3)

            if src["type"] == "directory":
                icon_text = "📁"
                color = "#007acc"
                tip = (
                    f"Папка: {src['path']}\n"
                    f"Рекурсивно: {src.get('recursive', True)}\n"
                    f"Исключения: {', '.join(src.get('exclude', [])) or 'нет'}"
                )
            else:
                icon_text, color = get_file_icon(src["path"])
                tip = f"Файл: {src['path']}"

            icon_label = ctk.CTkLabel(
                frame,
                text=icon_text,
                font=ctk.CTkFont(size=22),
                width=40,
                height=40,
                fg_color=color,
                corner_radius=6,
                anchor="center",
            )
            icon_label.pack(side="left", padx=(12, 10), pady=4)
            Tooltip(icon_label, tip, delay=500, wrap=400)

            path_lbl = ctk.CTkLabel(frame, text=src["path"], font=ctk.CTkFont(size=12))
            path_lbl.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            Tooltip(path_lbl, tip, delay=500, wrap=400)

            btn_del = ctk.CTkButton(
                frame,
                text="✕",
                width=24,
                height=24,
                fg_color="transparent",
                text_color="#858585",
                hover_color="#c75450",
                font=ctk.CTkFont(size=12),
                command=lambda s=src: self._remove_source(s),
            )
            btn_del.pack(side="right", padx=10)
            Tooltip(btn_del, "Удалить источник из проекта", delay=400)

    def _add_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.project.sources.append(
                {
                    "type": "directory",
                    "path": path,
                    "recursive": True,
                    "exclude": ["node_modules", ".git", "__pycache__", "dist", "build"],
                }
            )
            self._refresh_sources()
            self._auto_save()

    def _add_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.project.sources.append(
                {"type": "file", "path": path, "recursive": False, "exclude": []}
            )
            self._refresh_sources()
            self._auto_save()

    def _remove_source(self, src):
        self.project.sources = [s for s in self.project.sources if s != src]
        self._refresh_sources()
        self._auto_save()

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, path)
            self._auto_save()

    def _auto_save(self):
        self.project.extensions = self._extensions
        self.pm.save(self.project)
        if self.on_save:
            self.on_save(self.project)

    def _open_settings(self):
        dialog = ProjectSettingsDialog(
            self, self.project, on_save=self._on_settings_save
        )
        self.wait_window(dialog)

    def _on_settings_save(self, project):
        self.project = project
        self.header_name.configure(text=project.name)
        self.git_msg_display.configure(text=project.default_git_message)

        # Обновляем иконку в заголовке без пересоздания формы
        if project.icon_path and Path(project.icon_path).exists():
            try:
                img = Image.open(project.icon_path)
                self._header_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(32, 32)
                )
                for child in self.winfo_children()[0].winfo_children():
                    if isinstance(child, ctk.CTkLabel) and child.cget("image") != "":
                        child.configure(image=self._header_icon, text="")
                        break
            except Exception:
                pass

        self._set_status("Настройки сохранены", "#4ec9b0")
        if self.on_save:
            self.on_save(project)

    def _aggregate(self):
        from core.aggregator import Aggregator

        self.project.extensions = self._extensions
        self.project.output_path = self.out_entry.get()
        self.pm.save(self.project)

        self._set_status("Сборка файлов...", "#858585")
        self._progress("show", 0.2)
        self.update()

        agg = Aggregator()
        result = agg.aggregate(
            sources=self.project.sources,
            extensions=self._extensions,
            exclude_ext=self.project.exclude_extensions,
            output_path=self.project.output_path,
        )

        self._progress("hide")

        if result["success"]:
            self._set_status(
                f"Собрано: {result['files_count']} файлов | {result['output_path']}",
                "#4ec9b0",
            )
            self.project.last_output_hash = result["hash"]
            self.pm.save(self.project)
            if self.on_save:
                self.on_save(self.project)
        else:
            self._set_status(f"Ошибка: {result['error']}", "#c75450")

    def _open_sources(self):
        if self.project.sources:
            first = Path(self.project.sources[0]["path"])
            path = first.parent if first.is_file() else first
            if path.exists():
                open_file(str(path))

    def _open_output(self):
        path = Path(self.project.output_path)
        if path.exists():
            open_file(str(path.parent) if path.is_file() else str(path))
        else:
            self._set_status("Выходной файл ещё не создан", "#c75450")

    def refresh_backups_list(self):
        if hasattr(self, "backups_frame") and self.backups_frame.winfo_exists():
            self._refresh_backups()

    def _refresh_backups(self):
        from core.backup_manager import BackupManager

        for widget in self.backups_frame.winfo_children():
            widget.destroy()

        bm = BackupManager(
            backup_dir=self.project.backup_dir,
            project_name=self.project.name,
            max_auto=self.project.max_auto_backups,
            aliases=getattr(self.project, "aliases", []),
        )

        backups = bm.list_backups()

        if backups["auto"]:
            ctk.CTkLabel(
                self.backups_frame,
                text=f"Автоматические ({len(backups['auto'])}/{self.project.max_auto_backups}):",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#858585",
            ).pack(anchor="w", pady=(5, 2))

            for b in backups["auto"]:
                frame = ctk.CTkFrame(
                    self.backups_frame, fg_color="#2a2d2e", corner_radius=4
                )
                frame.pack(fill="x", pady=1)

                lbl = ctk.CTkLabel(
                    frame,
                    text=f"🕐 {b['time']}  |  {b['name']}  |  {b['size']:,} bytes",
                    font=ctk.CTkFont(size=10),
                )
                lbl.pack(side="left", padx=10, pady=4)
                Tooltip(lbl, f"Автобекап: {b['name']}\n{b['path']}", delay=400)

                btn_del = ctk.CTkButton(
                    frame,
                    text="Удалить",
                    width=60,
                    height=20,
                    fg_color="#c75450",
                    hover_color="#a0403c",
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._delete_backup(p),
                )
                btn_del.pack(side="right", padx=2)
                Tooltip(btn_del, "Удалить автобекап", delay=400)

                btn_open = ctk.CTkButton(
                    frame,
                    text="Открыть",
                    width=60,
                    height=20,
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._open_backup(p),
                )
                btn_open.pack(side="right", padx=5)
                Tooltip(btn_open, "Открыть бекап в проводнике", delay=400)

        if backups["manual"]:
            ctk.CTkLabel(
                self.backups_frame,
                text=f"Ручные ({len(backups['manual'])}):",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#858585",
            ).pack(anchor="w", pady=(10, 2))

            for b in backups["manual"]:
                frame = ctk.CTkFrame(
                    self.backups_frame, fg_color="#2a2d2e", corner_radius=4
                )
                frame.pack(fill="x", pady=1)

                lbl = ctk.CTkLabel(
                    frame,
                    text=f"💾 {b['time']}  |  {b['name']}  |  {b['size']:,} bytes",
                    font=ctk.CTkFont(size=10),
                )
                lbl.pack(side="left", padx=10, pady=4)
                Tooltip(lbl, f"Ручной бекап: {b['name']}\n{b['path']}", delay=400)

                btn_del = ctk.CTkButton(
                    frame,
                    text="Удалить",
                    width=60,
                    height=20,
                    fg_color="#c75450",
                    hover_color="#a0403c",
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._delete_backup(p),
                )
                btn_del.pack(side="right", padx=2)
                Tooltip(btn_del, "Удалить ручной бекап", delay=400)

                btn_open = ctk.CTkButton(
                    frame,
                    text="Открыть",
                    width=60,
                    height=20,
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._open_backup(p),
                )
                btn_open.pack(side="right", padx=5)
                Tooltip(btn_open, "Открыть бекап в проводнике", delay=400)

        if not backups["auto"] and not backups["manual"]:
            ctk.CTkLabel(
                self.backups_frame,
                text="Пока нет бекапов",
                font=ctk.CTkFont(size=11),
                text_color="#858585",
            ).pack(anchor="w", pady=5)

    def _create_manual_backup(self):
        from core.backup_manager import BackupManager

        self._progress("show", 0.4)
        bm = BackupManager(
            backup_dir=self.project.backup_dir, project_name=self.project.name
        )

        result = bm.create_manual(self.project.output_path)
        self._progress("hide")
        if result:
            self._set_status(f"Ручной бекап: {result['name']}", "#4ec9b0")
            self._refresh_backups()
        else:
            self._set_status("Нечего бекапить — соберите файлы сначала", "#c75450")

    def _delete_backup(self, path: str):
        from core.backup_manager import BackupManager

        dialog = ConfirmDialog(self.winfo_toplevel(), message="Удалить этот бекап?")
        self.wait_window(dialog)

        if not dialog.result:
            return

        self._progress("show", 0.3)
        bm = BackupManager(
            backup_dir=self.project.backup_dir,
            project_name=self.project.name,
            max_auto=self.project.max_auto_backups,
        )

        if bm.delete_backup(path):
            self._progress("hide")
            self._set_status("Бекап удалён", "#858585")
            self._refresh_backups()

    def _open_backup(self, path: str):
        open_file(path)

    def _git_pull(self):
        import threading

        def run():
            from core.git_manager import GitManager

            cwd = "."
            if self.project.sources:
                first = Path(self.project.sources[0]["path"])
                if first.is_file():
                    cwd = str(first.parent)
                else:
                    cwd = str(first)

            if not GitManager.is_repo(cwd):

                def update_ui():
                    if not self.winfo_exists():
                        return
                    self._set_status(
                        "❌ Git-репозиторий не найден. Выполните git init в папке проекта.",
                        "#c75450",
                    )

                self.after(0, update_ui)
                return

            self._progress("show", 0.4)
            self._set_status("Git Pull выполняется...", "#858585")
            result = GitManager.pull(cwd)
            self._progress("hide")
            msg = (
                "Git Pull: успешно"
                if result["success"]
                else f"Git Pull: {result['stderr'][:120]}"
            )
            color = "#4ec9b0" if result["success"] else "#c75450"

            def update_ui():
                if not self.winfo_exists():
                    return
                self._set_status(msg, color)

            self.after(0, update_ui)

        threading.Thread(target=run, daemon=True).start()

    def _git_push(self):
        import threading

        dialog = ctk.CTkToplevel(self)
        dialog.title("Git Push")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Сообщение коммита:", font=ctk.CTkFont(size=12)).pack(
            pady=(20, 5)
        )
        msg_entry = ctk.CTkEntry(dialog, width=450)
        msg_entry.insert(
            0,
            getattr(
                self.project,
                "default_git_message",
                "update: changes from Code Aggregator",
            ),
        )
        setup_clipboard(msg_entry)
        msg_entry.pack(pady=5)
        Tooltip(msg_entry, "Сообщение для git commit", delay=400)

        def do_push():
            message = msg_entry.get().strip() or "update: changes from Code Aggregator"
            dialog.grab_release()
            dialog.master.focus_set()
            dialog.destroy()

            def run():
                from core.git_manager import GitManager

                cwd = "."
                if self.project.sources:
                    first = Path(self.project.sources[0]["path"])
                    if first.is_file():
                        cwd = str(first.parent)
                    else:
                        cwd = str(first)

                if not GitManager.is_repo(cwd):

                    def update_ui():
                        if not self.winfo_exists():
                            return
                        self._set_status(
                            "❌ Git-репозиторий не найден. Выполните git init в папке проекта.",
                            "#c75450",
                        )

                    self.after(0, update_ui)
                    return

                self._progress("show", 0.4)
                self._set_status("Git Push выполняется...", "#858585")
                result = GitManager.push(cwd, message=message)
                self._progress("hide")
                msg = (
                    "Git Push: успешно"
                    if result["success"]
                    else f"Git Push: {result['stderr'][:120]}"
                )
                color = "#4ec9b0" if result["success"] else "#c75450"

                def update_ui():
                    if not self.winfo_exists():
                        return
                    self._set_status(msg, color)

                self.after(0, update_ui)

            threading.Thread(target=run, daemon=True).start()

        btn_push = ctk.CTkButton(
            dialog,
            text="Push",
            fg_color="#007acc",
            hover_color="#005a9e",
            command=do_push,
        )
        btn_push.pack(pady=20)
        Tooltip(btn_push, "Выполнить git add, commit, push", delay=400)

        dialog.update_idletasks()
        toplevel = self.winfo_toplevel()
        x = toplevel.winfo_x() + (toplevel.winfo_width() - 500) // 2
        y = toplevel.winfo_y() + (toplevel.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
