import customtkinter as ctk
from tkinter import filedialog
from core.project_manager import ProjectManager, Source
from gui.utils import get_file_icon, setup_clipboard, open_file
from gui.components import ConfirmDialog
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

        ctk.CTkButton(
            header,
            text="⚙️",
            width=32,
            height=32,
            fg_color="transparent",
            text_color="#858585",
            hover_color="#2a2d2e",
            font=ctk.CTkFont(size=16),
            command=self._open_settings,
        ).pack(side="right", padx=5)

        # Форма
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)
        speed = getattr(self.project, "scroll_speed", 6)
        form._parent_canvas.configure(yscrollincrement=speed)

        # Источники
        ctk.CTkLabel(
            form, text="Источники", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

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

        # Статус
        self.status_label = ctk.CTkLabel(
            form, text="", font=ctk.CTkFont(size=11), text_color="#858585"
        )
        self.status_label.pack(anchor="w", pady=5)

    def refresh_backups_list(self):
        """Публичный метод для обновления списка бэкапов извне (автобекап)"""
        if hasattr(self, "backups_frame") and self.winfo_exists():
            self._refresh_backups()

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

    def _auto_save(self):
        """Быстрое сохранение источников и расширений без перезапуска потока"""
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
        self.status_label.configure(text="✅ Настройки сохранены", text_color="#4ec9b0")
        if self.on_save:
            self.on_save(project)

    def _aggregate(self):
        from core.aggregator import Aggregator

        # Сохраняем текущие источники/расширения
        self.project.extensions = self._extensions
        self.pm.save(self.project)

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
            if self.on_save:
                self.on_save(self.project)
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

            def update_ui():
                if not self.winfo_exists():
                    return
                self.status_label.configure(
                    text=msg,
                    text_color="#4ec9b0" if result["success"] else "#c75450",
                )

            self.after(0, update_ui)

        threading.Thread(target=run, daemon=True).start()
        if self.winfo_exists():
            self.status_label.configure(
                text="🔄 Git Pull выполняется...", text_color="#858585"
            )

    def _git_push(self):
        import threading
        from pathlib import Path

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

        def do_push():
            message = msg_entry.get().strip() or "update: changes from Code Aggregator"
            # Фикс TclError
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

                result = GitManager.push(cwd, message=message)
                msg = (
                    "✅ Git Push: успешно"
                    if result["success"]
                    else f"❌ Git Push: {result['stderr'][:120]}"
                )

                def update_ui():
                    if not self.winfo_exists():
                        return
                    self.status_label.configure(
                        text=msg,
                        text_color="#4ec9b0" if result["success"] else "#c75450",
                    )

                self.after(0, update_ui)

            threading.Thread(target=run, daemon=True).start()
            if self.winfo_exists():
                self.status_label.configure(
                    text="⬆️ Git Push выполняется...", text_color="#858585"
                )

        ctk.CTkButton(
            dialog,
            text="Push",
            fg_color="#007acc",
            hover_color="#005a9e",
            command=do_push,
        ).pack(pady=20)

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
