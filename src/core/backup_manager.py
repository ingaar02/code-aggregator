import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class BackupManager:
    def __init__(
        self,
        backup_dir: str,
        project_name: str,
        max_auto: int = 10,
        aliases: List[str] = None,
    ):
        self.backup_dir = Path(backup_dir)
        self.project_name = project_name
        self.max_auto = max_auto
        self.aliases = aliases or []
        self.all_names = [project_name] + self.aliases

        self.auto_dir = self.backup_dir / "auto"
        self.manual_dir = self.backup_dir / "manual"
        self.auto_dir.mkdir(parents=True, exist_ok=True)
        self.manual_dir.mkdir(parents=True, exist_ok=True)

    def _generate_name(self, suffix: str = "auto") -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{self.project_name}_{timestamp}_{suffix}.txt"

    def create_auto(
        self, source_path: str, current_hash: str, last_hash: str
    ) -> Optional[Dict]:
        if current_hash == last_hash:
            return None

        source = Path(source_path)
        if not source.exists():
            return None

        self._rotate_auto()

        dest = self.auto_dir / self._generate_name("auto")
        shutil.copy2(source, dest)

        return {
            "type": "auto",
            "path": str(dest),
            "name": dest.name,
            "time": datetime.now().isoformat(),
        }

    def create_manual(self, source_path: str) -> Optional[Dict]:
        source = Path(source_path)
        if not source.exists():
            return None

        dest = self.manual_dir / self._generate_name("manual")
        shutil.copy2(source, dest)

        return {
            "type": "manual",
            "path": str(dest),
            "name": dest.name,
            "time": datetime.now().isoformat(),
        }

    def _rotate_auto(self):
        # Ищем только по текущему имени для ротации
        backups = sorted(self.auto_dir.glob(f"{self.project_name}_*_auto.txt"))
        while len(backups) >= self.max_auto:
            backups[0].unlink()
            backups.pop(0)

    def list_backups(self) -> Dict[str, List[Dict]]:
        result = {"auto": [], "manual": []}
        seen = set()

        for backup_type, directory in [
            ("auto", self.auto_dir),
            ("manual", self.manual_dir),
        ]:
            for name in self.all_names:
                for f in directory.glob(f"{name}_*.txt"):
                    path_str = str(f)
                    if path_str in seen:
                        continue
                    seen.add(path_str)

                    result[backup_type].append(
                        {
                            "name": f.name,
                            "path": path_str,
                            "size": f.stat().st_size,
                            "time": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )

            # Сортируем по времени, новые сверху
            result[backup_type].sort(key=lambda x: x["time"], reverse=True)

        return result

    def delete_backup(self, path: str) -> bool:
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False
