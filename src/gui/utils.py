import customtkinter as ctk

# Иконка + цвет фона для расширений
FILE_ICONS = {
    ".py": ("🐍", "#3776ab"),
    ".js": ("📜", "#f7df1e"),
    ".jsx": ("⚛️", "#61dafb"),
    ".ts": ("📘", "#3178c6"),
    ".tsx": ("⚛️", "#61dafb"),
    ".kt": ("📱", "#7f52ff"),
    ".xml": ("🌐", "#e44d26"),
    ".css": ("🎨", "#264de4"),
    ".html": ("🌐", "#e44d26"),
    ".json": ("🗄️", "#5391fe"),
    ".txt": ("📄", "#858585"),
    ".md": ("📝", "#083fa1"),
    ".java": ("☕", "#b07219"),
    ".go": ("🐹", "#00add8"),
    ".rs": ("🦀", "#dea584"),
    ".cpp": ("⚙️", "#f34b7d"),
    ".c": ("⚙️", "#555555"),
    ".h": ("⚙️", "#a8b9cc"),
    ".vue": ("🟢", "#41b883"),
    ".dart": ("🎯", "#00b4ab"),
    ".swift": ("🦉", "#ffac45"),
    ".php": ("🐘", "#4f5d95"),
    ".rb": ("💎", "#701516"),
    ".sql": ("🗃️", "#e38c00"),
    ".sh": ("🐚", "#89e051"),
    ".yml": ("⚙️", "#cb171e"),
    ".yaml": ("⚙️", "#cb171e"),
    ".dockerfile": ("🐳", "#2496ed"),
    ".gitignore": ("🚫", "#000000"),
    ".env": ("🔐", "#ecd53f"),
    ".lock": ("🔒", "#5391fe"),
    ".ini": ("⚙️", "#d1d5db"),
    ".toml": ("⚙️", "#9c4221"),
    ".gradle": ("🐘", "#02303a"),
    ".cs": ("🟣", "#178600"),
    ".ps1": ("🪟", "#012456"),
    ".bat": ("🪟", "#012456"),
    ".cmd": ("🪟", "#012456"),
}

def get_file_icon(path: str):
    ext = path[path.rfind("."):].lower() if "." in path else ""
    return FILE_ICONS.get(ext, ("📄", "#858585"))

def setup_clipboard(widget):
    """Ctrl+A/C/V/X для CTkEntry и CTkTextbox"""
    if isinstance(widget, ctk.CTkEntry):
        widget.bind("<Control-a>", lambda e: widget.select_range(0, "end") or "break")
        widget.bind("<Control-A>", lambda e: widget.select_range(0, "end") or "break")
        widget.bind("<Control-c>", lambda e: _copy_entry(widget) or "break")
        widget.bind("<Control-C>", lambda e: _copy_entry(widget) or "break")
        widget.bind("<Control-v>", lambda e: _paste_entry(widget) or "break")
        widget.bind("<Control-V>", lambda e: _paste_entry(widget) or "break")
        widget.bind("<Control-x>", lambda e: _cut_entry(widget) or "break")
        widget.bind("<Control-X>", lambda e: _cut_entry(widget) or "break")
    elif isinstance(widget, ctk.CTkTextbox):
        widget.bind("<Control-a>", lambda e: widget.tag_add("sel", "1.0", "end") or "break")
        widget.bind("<Control-A>", lambda e: widget.tag_add("sel", "1.0", "end") or "break")
        widget.bind("<Control-c>", lambda e: _copy_textbox(widget) or "break")
        widget.bind("<Control-C>", lambda e: _copy_textbox(widget) or "break")
        widget.bind("<Control-v>", lambda e: _paste_textbox(widget) or "break")
        widget.bind("<Control-V>", lambda e: _paste_textbox(widget) or "break")
        widget.bind("<Control-x>", lambda e: _cut_textbox(widget) or "break")
        widget.bind("<Control-X>", lambda e: _cut_textbox(widget) or "break")

def _copy_entry(entry):
    try:
        entry.clipboard_clear()
        entry.clipboard_append(entry.get())
    except Exception:
        pass

def _paste_entry(entry):
    try:
        entry.insert("insert", entry.clipboard_get())
    except Exception:
        pass

def _cut_entry(entry):
    try:
        entry.clipboard_clear()
        entry.clipboard_append(entry.get())
        entry.delete(0, "end")
    except Exception:
        pass

def _copy_textbox(textbox):
    try:
        if textbox.tag_ranges("sel"):
            textbox.clipboard_clear()
            textbox.clipboard_append(textbox.get("sel.first", "sel.last"))
    except Exception:
        pass

def _paste_textbox(textbox):
    try:
        textbox.insert("insert", textbox.clipboard_get())
    except Exception:
        pass

def _cut_textbox(textbox):
    try:
        if textbox.tag_ranges("sel"):
            textbox.clipboard_clear()
            textbox.clipboard_append(textbox.get("sel.first", "sel.last"))
            textbox.delete("sel.first", "sel.last")
    except Exception:
        pass