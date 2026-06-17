import customtkinter as ctk
from pathlib import Path
from PIL import Image
from core.project_manager import ProjectManager
from gui.components import ConfirmDialog


class ProjectCard(ctk.CTkFrame):
    def __init__(self, parent, project, on_click, on_delete, **kwargs):
        super().__init__(parent, fg_color="transparent", height=56, **kwargs)
        self.project = project
        self.on_click = on_click
        self.on_delete = on_delete
        self._icon_image = None  # ссылка на CTkImage

        # Иконка проекта
        if project.icon_path and Path(project.icon_path).exists():
            try:
                img = Image.open(project.icon_path)
                self._icon_image = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(40, 40)
                )
                self.icon = ctk.CTkLabel(
                    self,
                    image=self._icon_image,
                    text="",
                    width=44,
                    height=44,
                    fg_color="transparent",
                )
            except Exception:
                self.icon = ctk.CTkLabel(
                    self,
                    text="📁",
                    font=ctk.CTkFont(size=24),
                    width=44,
                    height=44,
                    fg_color="#2d2d30",
                    corner_radius=8,
                    anchor="center",
                )
        else:
            self.icon = ctk.CTkLabel(
                self,
                text="📁",
                font=ctk.CTkFont(size=24),
                width=44,
                height=44,
                fg_color="#2d2d30",
                corner_radius=8,
                anchor="center",
            )
        self.icon.pack(side="left", padx=(12, 10), pady=6)

        # Текст
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.text_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.name_label = ctk.CTkLabel(
            self.text_frame,
            text=project.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.name_label.pack(fill="x", pady=(2, 0))

        stack = project.stack_detected or "Unknown"
        self.stack_label = ctk.CTkLabel(
            self.text_frame,
            text=stack,
            font=ctk.CTkFont(size=11),
            text_color="#858585",
            anchor="w",
        )
        self.stack_label.pack(fill="x")

        # Кнопка удаления
        self.delete_btn = ctk.CTkButton(
            self,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            text_color="#858585",
            hover_color="#c75450",
            font=ctk.CTkFont(size=12),
            command=self._on_delete,
        )
        self.delete_btn.pack(side="right", padx=12)

        # Клик по карточке
        for widget in [
            self,
            self.icon,
            self.text_frame,
            self.name_label,
            self.stack_label,
        ]:
            widget.bind("<Button-1>", lambda e: on_click(project))
            widget.bind("<Enter>", self._on_hover)
            widget.bind("<Leave>", self._on_leave)

    def _on_hover(self, event):
        self.configure(fg_color="#2a2d2e")

    def _on_leave(self, event):
        self.configure(fg_color="transparent")

    def _on_delete(self):
        self.on_delete(self.project)


class Sidebar(ctk.CTkFrame):
    def __init__(
        self, parent, on_project_select, on_project_create, on_project_delete, **kwargs
    ):
        super().__init__(parent, width=260, fg_color="#252526", **kwargs)
        self.pack_propagate(False)

        self.pm = ProjectManager()
        self.on_project_select = on_project_select
        self.on_project_create = on_project_create
        self.on_project_delete = on_project_delete

        self.header = ctk.CTkLabel(
            self,
            text="ПРОЕКТЫ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#858585",
            anchor="w",
        )
        self.header.pack(fill="x", padx=15, pady=(15, 5))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.add_btn = ctk.CTkButton(
            self,
            text="+ Новый проект",
            fg_color="#007acc",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=12),
            command=self._on_create,
        )
        self.add_btn.pack(fill="x", padx=15, pady=15)

        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        projects = self.pm.list_all()
        for project in projects:
            card = ProjectCard(
                self.scroll,
                project,
                on_click=self.on_project_select,
                on_delete=self.on_project_delete,
            )
            card.pack(fill="x", pady=1)

    def _on_create(self):
        self.on_project_create()
