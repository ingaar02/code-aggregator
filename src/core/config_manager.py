import json
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.config_dir / "settings.json"
        self.projects_dir = self.config_dir / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        
        self._settings = self._load()
    
    def _load(self) -> dict:
        if self.settings_file.exists():
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_project_id": None,
            "theme": "dark",
            "default_extensions": [".js", ".jsx", ".ts", ".tsx", ".py", ".kt", ".xml", ".css", ".html", ".json"]
        }
    
    def save(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default=None):
        return self._settings.get(key, default)
    
    def set(self, key: str, value):
        self._settings[key] = value
        self.save()