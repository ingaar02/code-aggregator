import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional
from .config_manager import ConfigManager
from .stack_detector import StackDetector

@dataclass
class Source:
    type: str  # "directory" or "file"
    path: str
    recursive: bool = True
    exclude: List[str] = field(default_factory=list)

@dataclass
class Project:
    id: str
    name: str
    description: str = ""
    icon_path: str = ""
    stack_detected: str = "Unknown"
    sources: List[dict] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    exclude_extensions: List[str] = field(default_factory=list)
    output_path: str = ""
    backup_dir: str = ""
    auto_backup_interval: int = 300
    max_auto_backups: int = 10
    last_output_hash: str = ""
    last_backup_time: float = 0.0

class ProjectManager:
    def __init__(self):
        self.config = ConfigManager()
        self.projects_dir = self.config.projects_dir
    
    def _project_path(self, project_id: str) -> Path:
        return self.projects_dir / f"{project_id}.json"
    
    def create(self, name: str, description: str = "", sources: List[Source] = None,
               extensions: List[str] = None, output_path: str = "", backup_dir: str = "") -> Project:
        project_id = str(uuid.uuid4())[:8]
        
        # Auto-detect stack from first directory source
        stack = "Unknown"
        if sources:
            for s in sources:
                if s.type == "directory":
                    stack = StackDetector.detect(Path(s.path))
                    break
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            stack_detected=stack,
            sources=[asdict(s) for s in (sources or [])],
            extensions=extensions or [],
            output_path=output_path,
            backup_dir=backup_dir
        )
        
        self.save(project)
        self.config.set("last_project_id", project_id)
        return project
    
    def save(self, project: Project):
        path = self._project_path(project.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(project), f, indent=2, ensure_ascii=False)
    
    def load(self, project_id: str) -> Optional[Project]:
        path = self._project_path(project_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Project(**data)
    
    def delete(self, project_id: str) -> bool:
        path = self._project_path(project_id)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_all(self) -> List[Project]:
        projects = []
        for file in sorted(self.projects_dir.glob("*.json")):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            projects.append(Project(**data))
        return projects