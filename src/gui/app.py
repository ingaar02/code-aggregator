import customtkinter as ctk
from gui.sidebar import Sidebar
from gui.project_editor import ProjectEditor
from gui.components import Toast, ConfirmDialog
from core.project_manager import ProjectManager, Source

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Code Aggregator")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        self.update_idletasks()
        w, h = 1200, 800
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.pm = ProjectManager()
        self.current_project = None
        
        self.sidebar = Sidebar(
            self,
            on_project_select=self._on_select,
            on_project_create=self._on_create,
            on_project_delete=self._on_delete
        )
        self.sidebar.pack(side="left", fill="y")
        
        self.separator = ctk.CTkFrame(self, width=1, fg_color="#3e3e42")
        self.separator.pack(side="left", fill="y")
        
        self.editor = ProjectEditor(self)
        self.editor.pack(side="left", fill="both", expand=True)
        
        last_id = self.pm.config.get("last_project_id")
        if last_id:
            project = self.pm.load(last_id)
            if project:
                self._on_select(project)
    
    def _on_select(self, project):
        self.current_project = project
        self.editor.destroy()
        self.editor = ProjectEditor(self, project=project, on_save=self._on_save)
        self.editor.pack(side="left", fill="both", expand=True)
    
    def _on_create(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Новый проект")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        from gui.utils import setup_clipboard
        
        ctk.CTkLabel(dialog, text="Название проекта", font=ctk.CTkFont(size=12)).pack(pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(pady=5)
        setup_clipboard(name_entry)
        
        ctk.CTkLabel(dialog, text="Папка с исходниками", font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
        dir_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        dir_frame.pack(pady=5)
        
        dir_entry = ctk.CTkEntry(dir_frame, width=240)
        dir_entry.pack(side="left")
        setup_clipboard(dir_entry)
        
        def browse():
            path = ctk.filedialog.askdirectory()
            if path:
                dir_entry.delete(0, "end")
                dir_entry.insert(0, path)
        
        ctk.CTkButton(dir_frame, text="Обзор", width=50, command=browse).pack(side="left", padx=5)
        
        def create():
            name = name_entry.get().strip()
            path = dir_entry.get().strip()
            if not name:
                return
            
            sources = []
            if path:
                sources.append(Source(type="directory", path=path, recursive=True, exclude=["node_modules", ".git", "__pycache__"]))
            
            project = self.pm.create(
                name=name,
                sources=sources,
                extensions=[".js", ".jsx", ".ts", ".tsx", ".py", ".kt", ".xml"],
                output_path=f"output/{name}_aggregated.txt",
                backup_dir=f"output/{name}_backups"
            )
            
            dialog.destroy()
            self.sidebar.refresh()
            self._on_select(project)
            self._show_toast(f"Проект «{name}» создан")
        
        ctk.CTkButton(
            dialog, text="Создать", fg_color="#007acc", hover_color="#005a9e",
            command=create
        ).pack(pady=20)
        
        dialog.update_idletasks()
        dx = self.winfo_x() + (self.winfo_width() - 400) // 2
        dy = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{dx}+{dy}")
    
    def _on_delete(self, project):
        dialog = ConfirmDialog(self, message=f"Удалить проект «{project.name}»?")
        self.wait_window(dialog)
        
        if dialog.result:
            self.pm.delete(project.id)
            self.sidebar.refresh()
            if self.current_project and self.current_project.id == project.id:
                self.editor.destroy()
                self.editor = ProjectEditor(self)
                self.editor.pack(side="left", fill="both", expand=True)
            self._show_toast(f"Проект «{project.name}» удалён")
    
    def _on_save(self, project):
        self.sidebar.refresh()
        self._show_toast(f"Проект «{project.name}» сохранён")
    
    def _show_toast(self, message):
        Toast(self, message)