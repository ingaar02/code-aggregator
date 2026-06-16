import customtkinter as ctk
from tkinter import filedialog
from core.project_manager import ProjectManager, Source
from gui.utils import get_file_icon, setup_clipboard


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

        ctk.CTkLabel(
            header, text=self.project.name, font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"  •  {self.project.stack_detected}",
            font=ctk.CTkFont(size=12),
            text_color="#858585",
        ).pack(side="left", padx=5)

        # Форма
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # ← ВОТ ЭТА СТРОКА: увеличиваем скорость прокрутки в 6 раз
        form._parent_canvas.configure(yscrollincrement=6)

        # Название
        ctk.CTkLabel(form, text="Название", font=ctk.CTkFont(size=12)).pack(
            anchor="w", pady=(10, 2)
        )
        self.name_entry = ctk.CTkEntry(form, width=400)
        self.name_entry.insert(0, self.project.name)
        setup_clipboard(self.name_entry)
        self.name_entry.pack(anchor="w", pady=(0, 10))

        # Описание
        ctk.CTkLabel(form, text="Описание", font=ctk.CTkFont(size=12)).pack(
            anchor="w", pady=(10, 2)
        )
        self.desc_entry = ctk.CTkTextbox(form, width=400, height=80)
        self.desc_entry.insert("1.0", self.project.description)
        setup_clipboard(self.desc_entry)
        self.desc_entry.pack(anchor="w", pady=(0, 10))

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
        setup_clipboard(self.out_entry)
        self.out_entry.pack(side="left")

        ctk.CTkButton(
            out_frame, text="Обзор", width=60, command=self._browse_output
        ).pack(side="left", padx=5)

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

        # Кнопка сохранения
        ctk.CTkButton(
            form,
            text="Сохранить проект",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save,
        ).pack(anchor="w", pady=20)

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

        self.ext_input.delete(0, "end")

    def _remove_ext(self, ext):
        if ext in self._extensions:
            self._extensions.remove(ext)
            self._refresh_chips()

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

    def _add_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.project.sources.append(
                {"type": "file", "path": path, "recursive": False, "exclude": []}
            )
            self._refresh_sources()

    def _remove_source(self, src):
        self.project.sources = [s for s in self.project.sources if s != src]
        self._refresh_sources()

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, path)

    def _save(self):
        self.project.name = self.name_entry.get()
        self.project.description = self.desc_entry.get("1.0", "end-1c")
        self.project.extensions = self._extensions
        self.project.output_path = self.out_entry.get()

        self.pm.save(self.project)
        if self.on_save:
            self.on_save(self.project)

    def _aggregate(self):
        from core.aggregator import Aggregator

        self._save()

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
        import os
        from pathlib import Path

        if self.project.sources:
            first = self.project.sources[0]
            path = Path(first["path"])
            if path.is_file():
                path = path.parent
            if path.exists():
                os.startfile(str(path))

    def _open_output(self):
        import os
        from pathlib import Path

        path = Path(self.project.output_path)
        if path.exists():
            if path.is_file():
                os.startfile(str(path.parent))
            else:
                os.startfile(str(path))
        else:
            self.status_label.configure(
                text="❌ Выходной файл ещё не создан", text_color="#c75450"
            )
