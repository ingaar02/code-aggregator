import customtkinter as ctk
from tkinter import filedialog
from core.project_manager import ProjectManager, Source
from gui.utils import get_file_icon, setup_clipboard, open_file
from gui.components import ConfirmDialog


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

        ctk.CTkButton(
            self,
            text="✕",
            width=16,
            height=16,
            fg_color="transparent",
            text_color="white",
            hover_color="#c75450",
            font=ctk.CTkFont(size=10),
            command=self._remove,
        ).pack(side="left", padx=(2, 8), pady=2)

    def _remove(self):
        self.on_remove(self.text)
        self.destroy()


class ProjectEditor(ctk.CTkFrame):
    def __init__(self, parent, project=None, on_save=None, **kwargs):
        super().__init__(parent, fg_color="#1e1e1e", **kwargs)
        self.project = project
        self.on_save = on_save
        self.pm = ProjectManager()
        self._dirty = False

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

    def _mark_dirty(self):
        if not self._dirty and self.project:
            self._dirty = True
            self.save_btn.configure(state="normal")

    def _build_form(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Заголовок
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)

        self.header_name = ctk.CTkLabel(
            header, text=self.project.name, font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_name.pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"  •  {self.project.stack_detected}",
            font=ctk.CTkFont(size=12),
            text_color="#858585",
        ).pack(side="left", padx=5)

        # Форма
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)
        form._parent_canvas.configure(yscrollincrement=30)

        # === НАСТРОЙКИ ПРОЕКТА ===
        ctk.CTkLabel(
            form, text="Настройки проекта", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        # Название
        ctk.CTkLabel(form, text="Название", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.name_entry = ctk.CTkEntry(form, width=400)
        self.name_entry.insert(0, self.project.name)
        self.name_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())
        setup_clipboard(self.name_entry)
        self.name_entry.pack(anchor="w", pady=(0, 8))

        # Описание
        ctk.CTkLabel(form, text="Описание", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.desc_entry = ctk.CTkTextbox(form, width=400, height=60)
        self.desc_entry.insert("1.0", self.project.description)
        self.desc_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())
        setup_clipboard(self.desc_entry)
        self.desc_entry.pack(anchor="w", pady=(0, 8))

        # Интервал и макс бекапов
        interval_frame = ctk.CTkFrame(form, fg_color="transparent")
        interval_frame.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            interval_frame, text="Интервал бекапа (сек):", font=ctk.CTkFont(size=11)
        ).pack(side="left")
        self.interval_entry = ctk.CTkEntry(interval_frame, width=80)
        self.interval_entry.insert(0, str(self.project.auto_backup_interval))
        self.interval_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())
        setup_clipboard(self.interval_entry)
        self.interval_entry.pack(side="left", padx=5)

        ctk.CTkLabel(
            interval_frame, text="Макс. автобекапов:", font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(15, 0))
        self.max_backups_entry = ctk.CTkEntry(interval_frame, width=60)
        self.max_backups_entry.insert(0, str(self.project.max_auto_backups))
        self.max_backups_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())
        setup_clipboard(self.max_backups_entry)
        self.max_backups_entry.pack(side="left", padx=5)
        # =========================

        # Источники
        ctk.CTkLabel(
            form, text="Источники", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(15, 5))

        self.sources_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.sources_frame.pack(fill="x", pady=5)
        self._refresh_sources()

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(anchor="w", pady=5)

        ctk.CTkButton(
            btn_frame, text="Добавить папку", width=120, command=self._add_directory
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame, text="Добавить файл", width=120, command=self._add_file
        ).pack(side="left", padx=5)

        # Расширения — чипсы
        ctk.CTkLabel(
            form, text="Расширения файлов", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(15, 5))

        self.chips_container = ctk.CTkFrame(form, fg_color="transparent")
        self.chips_container.pack(anchor="w", fill="x", pady=5)

        input_frame = ctk.CTkFrame(form, fg_color="transparent")
        input_frame.pack(anchor="w", pady=(0, 10))

        self.ext_input = ctk.CTkEntry(
            input_frame, width=200, placeholder_text="Введите .ext и нажмите Enter"
        )
        self.ext_input.pack(side="left")
        setup_clipboard(self.ext_input)
        self.ext_input.bind("<Return>", self._on_ext_enter)

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

        # Выходной файл
        ctk.CTkLabel(
            form, text="Путь к выходному файлу", font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(10, 2))
        out_frame = ctk.CTkFrame(form, fg_color="transparent")
        out_frame.pack(anchor="w", pady=(0, 10))

        self.out_entry = ctk.CTkEntry(out_frame, width=320)
        self.out_entry.insert(0, self.project.output_path)
        self.out_entry.bind("<KeyRelease>", lambda e: self._mark_dirty())
        setup_clipboard(self.out_entry)
        self.out_entry.pack(side="left")

        ctk.CTkButton(
            out_frame, text="Обзор", width=60, command=self._browse_output
        ).pack(side="left", padx=5)

        # === БЕКАПЫ ===
        ctk.CTkLabel(
            form, text="Бекапы", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(15, 5))

        self.backups_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.backups_frame.pack(fill="x", pady=5)

        backup_btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        backup_btn_frame.pack(anchor="w", pady=5)

        ctk.CTkButton(
            backup_btn_frame,
            text="💾 Ручной бекап",
            width=120,
            command=self._create_manual_backup,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            backup_btn_frame,
            text="🔄 Обновить список",
            width=120,
            command=self._refresh_backups,
        ).pack(side="left", padx=5)

        self._refresh_backups()
        # =============

        # Кнопки действий
        actions_frame = ctk.CTkFrame(form, fg_color="transparent")
        actions_frame.pack(anchor="w", pady=(10, 5))

        ctk.CTkButton(
            actions_frame,
            text="🔧 Собрать файлы",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._aggregate,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame, text="📂 Исходники", width=100, command=self._open_sources
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame, text="📄 Результат", width=100, command=self._open_output
        ).pack(side="left", padx=5)

        # Статус
        self.status_label = ctk.CTkLabel(
            form, text="", font=ctk.CTkFont(size=11), text_color="#858585"
        )
        self.status_label.pack(anchor="w", pady=5)

        # Кнопка сохранения (неактивна по умолчанию)
        self.save_btn = ctk.CTkButton(
            form,
            text="💾 Сохранить проект",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_all,
            state="disabled",
        )
        self.save_btn.pack(anchor="w", pady=20)

        ctk.CTkButton(
            actions_frame,
            text="🔄 Git Pull",
            width=100,
            command=self._git_pull,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame,
            text="⬆️ Git Push",
            width=100,
            command=self._git_push,
        ).pack(side="left", padx=5)

    def _refresh_chips(self):
        for widget in self.chips_container.winfo_children():
            widget.destroy()

        for ext in self._extensions:
            chip = Chip(self.chips_container, ext, on_remove=self._remove_ext)
            chip.pack(side="left", padx=4, pady=2)

    def _on_ext_enter(self, event=None):
        text = self.ext_input.get().strip().lower()
        if not text:
            return

        if not text.startswith("."):
            text = "." + text

        if text not in self._extensions:
            self._extensions.append(text)
            self._refresh_chips()
            self._mark_dirty()

        self.ext_input.delete(0, "end")

    def _remove_ext(self, ext):
        if ext in self._extensions:
            self._extensions.remove(ext)
            self._refresh_chips()
            self._mark_dirty()

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
            else:
                icon_text, color = get_file_icon(src["path"])

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

            ctk.CTkLabel(frame, text=src["path"], font=ctk.CTkFont(size=12)).pack(
                side="left", fill="both", expand=True, padx=5, pady=5
            )

            ctk.CTkButton(
                frame,
                text="✕",
                width=24,
                height=24,
                fg_color="transparent",
                text_color="#858585",
                hover_color="#c75450",
                font=ctk.CTkFont(size=12),
                command=lambda s=src: self._remove_source(s),
            ).pack(side="right", padx=10)

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
            self._mark_dirty()

    def _add_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.project.sources.append(
                {"type": "file", "path": path, "recursive": False, "exclude": []}
            )
            self._refresh_sources()
            self._mark_dirty()

    def _remove_source(self, src):
        self.project.sources = [s for s in self.project.sources if s != src]
        self._refresh_sources()
        self._mark_dirty()

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, path)
            self._mark_dirty()

    def _save_all(self):
        self.project.name = self.name_entry.get()
        self.project.description = self.desc_entry.get("1.0", "end-1c")
        self.project.extensions = self._extensions
        self.project.output_path = self.out_entry.get()
        try:
            self.project.auto_backup_interval = int(self.interval_entry.get())
        except ValueError:
            pass
        try:
            self.project.max_auto_backups = int(self.max_backups_entry.get())
        except ValueError:
            pass

        self.pm.save(self.project)
        self._dirty = False
        self.save_btn.configure(state="disabled")
        self.header_name.configure(text=self.project.name)

        if self.on_save:
            self.on_save(self.project)

        self.status_label.configure(text="✅ Проект сохранён", text_color="#4ec9b0")

    def _aggregate(self):
        from core.aggregator import Aggregator

        self._save_all()

        agg = Aggregator()
        result = agg.aggregate(
            sources=self.project.sources,
            extensions=self._extensions,
            exclude_ext=self.project.exclude_extensions,
            output_path=self.project.output_path,
        )

        if result["success"]:
            self.status_label.configure(
                text=f"✅ Собрано: {result['files_count']} файлов | Пропущено: {result['skipped']} | {result['output_path']}",
                text_color="#4ec9b0",
            )
            self.project.last_output_hash = result["hash"]
            self.pm.save(self.project)
        else:
            self.status_label.configure(
                text=f"❌ {result['error']}", text_color="#c75450"
            )

    def _open_sources(self):
        from pathlib import Path

        if self.project.sources:
            first = self.project.sources[0]
            path = Path(first["path"])
            if path.is_file():
                path = path.parent
            if path.exists():
                open_file(str(path))

    def _open_output(self):
        from pathlib import Path

        path = Path(self.project.output_path)
        if path.exists():
            if path.is_file():
                open_file(str(path.parent))
            else:
                open_file(str(path))
        else:
            self.status_label.configure(
                text="❌ Выходной файл ещё не создан", text_color="#c75450"
            )

    def _refresh_backups(self):
        from core.backup_manager import BackupManager

        for widget in self.backups_frame.winfo_children():
            widget.destroy()

        bm = BackupManager(
            backup_dir=self.project.backup_dir,
            project_name=self.project.name,
            max_auto=self.project.max_auto_backups,
        )

        backups = bm.list_backups()

        # Автобекапы
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

                ctk.CTkLabel(
                    frame,
                    text=f"🕐 {b['time']}  |  {b['name']}  |  {b['size']:,} bytes",
                    font=ctk.CTkFont(size=10),
                ).pack(side="left", padx=10, pady=4)

                ctk.CTkButton(
                    frame,
                    text="Удалить",
                    width=50,
                    height=20,
                    fg_color="#c75450",
                    hover_color="#a0403c",
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._delete_backup(p),
                ).pack(side="right", padx=2)

                ctk.CTkButton(
                    frame,
                    text="Открыть",
                    width=50,
                    height=20,
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._open_backup(p),
                ).pack(side="right", padx=5)

        # Ручные бекапы
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

                ctk.CTkLabel(
                    frame,
                    text=f"💾 {b['time']}  |  {b['name']}  |  {b['size']:,} bytes",
                    font=ctk.CTkFont(size=10),
                ).pack(side="left", padx=10, pady=4)

                ctk.CTkButton(
                    frame,
                    text="Удалить",
                    width=50,
                    height=20,
                    fg_color="#c75450",
                    hover_color="#a0403c",
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._delete_backup(p),
                ).pack(side="right", padx=2)

                ctk.CTkButton(
                    frame,
                    text="Открыть",
                    width=50,
                    height=20,
                    font=ctk.CTkFont(size=9),
                    command=lambda p=b["path"]: self._open_backup(p),
                ).pack(side="right", padx=5)

        if not backups["auto"] and not backups["manual"]:
            ctk.CTkLabel(
                self.backups_frame,
                text="Пока нет бекапов",
                font=ctk.CTkFont(size=11),
                text_color="#858585",
            ).pack(anchor="w", pady=5)

    def _create_manual_backup(self):
        from core.backup_manager import BackupManager

        bm = BackupManager(
            backup_dir=self.project.backup_dir, project_name=self.project.name
        )

        result = bm.create_manual(self.project.output_path)
        if result:
            self.status_label.configure(
                text=f"💾 Ручной бекап создан: {result['name']}",
                text_color="#4ec9b0",
            )
            self._refresh_backups()
        else:
            self.status_label.configure(
                text="❌ Нечего бекапить — соберите файлы сначала",
                text_color="#c75450",
            )

    def _delete_backup(self, path: str):
        from core.backup_manager import BackupManager

        dialog = ConfirmDialog(self, message="Удалить этот бекап?")
        self.wait_window(dialog)

        if not dialog.result:
            return

        bm = BackupManager(
            backup_dir=self.project.backup_dir,
            project_name=self.project.name,
            max_auto=self.project.max_auto_backups,
        )

        if bm.delete_backup(path):
            self.status_label.configure(
                text="🗑️ Бекап удалён",
                text_color="#858585",
            )
            self._refresh_backups()

    def _open_backup(self, path: str):
        open_file(path)

    def _git_pull(self):
        import threading
        from pathlib import Path

        def run():
            from core.git_manager import GitManager

            # Определяем рабочую папку от первого source
            cwd = "."
            if self.project.sources:
                first = Path(self.project.sources[0]["path"])
                if first.is_file():
                    cwd = str(first.parent)
                else:
                    cwd = str(first)

            result = GitManager.pull(cwd)
            msg = (
                "✅ Git Pull: успешно"
                if result["success"]
                else f"❌ Git Pull: {result['stderr'][:120]}"
            )
            self.after(
                0,
                lambda: self.status_label.configure(
                    text=msg,
                    text_color="#4ec9b0" if result["success"] else "#c75450",
                ),
            )

        threading.Thread(target=run, daemon=True).start()
        self.status_label.configure(
            text="🔄 Git Pull выполняется...", text_color="#858585"
        )

    def _git_push(self):
        import threading
        from pathlib import Path

        def run():
            from core.git_manager import GitManager

            cwd = "."
            if self.project.sources:
                first = Path(self.project.sources[0]["path"])
                if first.is_file():
                    cwd = str(first.parent)
                else:
                    cwd = str(first)

            result = GitManager.push(cwd)
            msg = (
                "✅ Git Push: успешно"
                if result["success"]
                else f"❌ Git Push: {result['stderr'][:120]}"
            )
            self.after(
                0,
                lambda: self.status_label.configure(
                    text=msg,
                    text_color="#4ec9b0" if result["success"] else "#c75450",
                ),
            )

        threading.Thread(target=run, daemon=True).start()
        self.status_label.configure(
            text="⬆️ Git Push выполняется...", text_color="#858585"
        )
